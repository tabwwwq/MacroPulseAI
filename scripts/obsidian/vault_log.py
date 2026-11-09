"""Write MacroPulse activity into the Obsidian vault (stdlib only, never raises).

Subcommands
-----------
hook       Read a Claude Code hook payload (JSON on stdin) and append a line to the daily activity
           log `vault/80 Logs/YYYY-MM-DD.md`. On SessionStart it also prints a short context note
           (project status from the vault) that Claude Code adds to the new session.
codex-run  Record a delegated Codex run as a note in `vault/60 Agents/Codex runs/` and log it.

Logs are machine-written and local (git-ignored); curated notes live in the other vault folders.
Secrets are redacted before anything is written. Any failure is swallowed so a logging problem
can never block the agent.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
VAULT = Path(os.environ.get("MACROPULSE_VAULT", REPO_ROOT / "vault"))
LOGS_DIR = "80 Logs"
CODEX_DIR = "60 Agents/Codex runs"
STATUS_NOTE = "10 Project/Status.md"

MAX_PROMPT = 400
MAX_REPLY = 400
MAX_COMMAND = 160
MAX_EMBED = 6000

_SECRET_PATTERNS = [
    # key=value / key: value for secret-looking names
    re.compile(
        r"(?i)\b([A-Z0-9_]*(?:api[_-]?key|token|secret|passw(?:or)?d|pwd)[A-Z0-9_]*)\s*([=:])\s*(\"[^\"]*\"|'[^']*'|\S+)"
    ),
    re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}\b"),  # provider-style keys
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),  # GitHub tokens
    re.compile(r"\b[A-Fa-f0-9]{32,}\b"),  # long hex (API keys, hashes of secrets)
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{16,}=*"),
]


def redact(text: str) -> str:
    out = _SECRET_PATTERNS[0].sub(lambda m: f"{m.group(1)}{m.group(2)}***", text)
    for pattern in _SECRET_PATTERNS[1:]:
        out = pattern.sub("***", out)
    return out


def one_line(text: str, limit: int) -> str:
    flat = " ".join(str(text).split())
    flat = redact(flat).replace("|", "\\|")
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"


def now() -> datetime:
    return datetime.now().astimezone()


# ------------------------------------------------------------------ file helpers


@contextlib.contextmanager
def _lock(target: Path, timeout: float = 3.0) -> Any:
    """Tiny cross-platform lock so concurrent async hooks don't interleave writes."""
    lock = target.with_suffix(target.suffix + ".lock")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    deadline = time.monotonic() + timeout
    fd: int | None = None
    while True:
        try:
            fd = os.open(lock, flags)
            break
        except OSError:
            if time.monotonic() > deadline:
                # Stale lock from a crashed writer: take it over once, else write unlocked.
                with contextlib.suppress(OSError):
                    lock.unlink()
                try:
                    fd = os.open(lock, flags)
                except OSError:
                    fd = None
                break
            time.sleep(0.02)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
            with contextlib.suppress(OSError):
                lock.unlink()


def _daily_log(day: datetime) -> Path:
    return VAULT / LOGS_DIR / f"{day:%Y-%m-%d}.md"


def _log_header(day: datetime) -> str:
    return (
        "---\n"
        "type: activity-log\n"
        f"date: {day:%Y-%m-%d}\n"
        "tags:\n  - log/auto\n"
        "---\n\n"
        f"# Activity log · {day:%Y-%m-%d}\n\n"
        "> [!info] Auto-generated\n"
        "> Written by Claude Code hooks and the Codex runner via `scripts/obsidian/vault_log.py`.\n"
        f"> Curated summary of the day: [[70 Sessions/{day:%Y-%m-%d}]] · Back to [[Home]]\n"
    )


def append_log(lines: list[str], session_id: str | None = None, session_label: str = "") -> Path:
    stamp = now()
    path = _daily_log(stamp)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock(path):
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        chunks: list[str] = []
        if not existing:
            chunks.append(_log_header(stamp))
        if session_id:
            marker = f"session `{session_id[:8]}`"
            if marker not in existing:
                label = f" ({session_label})" if session_label else ""
                chunks.append(f"\n## {stamp:%H:%M} · {marker}{label}\n")
        chunks.extend(f"{line}\n" for line in lines)
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write("".join(chunks))
    return path


# ------------------------------------------------------------------ Claude Code hooks

_EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
_SHELL_TOOLS = {"Bash", "PowerShell"}


def _rel(path_str: str) -> str:
    try:
        return Path(path_str).resolve().relative_to(REPO_ROOT).as_posix()
    except (ValueError, OSError):
        return Path(path_str).name


def last_assistant_text(transcript_path: str | None) -> str | None:
    """Final assistant text block from a Claude Code JSONL transcript, if readable."""
    if not transcript_path:
        return None
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for raw in reversed(lines[-400:]):
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        message = entry.get("message") if isinstance(entry, dict) else None
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            texts = [
                c.get("text", "")
                for c in content
                if isinstance(c, dict) and c.get("type") == "text"
            ]
            text = "\n".join(t for t in texts if t.strip())
            if text.strip():
                return text
    return None


def _describe_tool(t: str, tool: str, tool_input: dict[str, Any]) -> str | None:
    if tool in _EDIT_TOOLS:
        target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        verb = "Created" if tool == "Write" else "Edited"
        return f"- {t} ✏️ {verb} `{_rel(target)}`"
    if tool in _SHELL_TOOLS:
        desc = one_line(tool_input.get("description", ""), 120)
        cmd = one_line(tool_input.get("command", ""), MAX_COMMAND)
        label = f"{desc} — " if desc else ""
        return f"- {t} ⚙️ {label}`{cmd}`"
    if tool in {"Agent", "Task"}:
        return f"- {t} 🧩 Subagent — {one_line(tool_input.get('description', ''), 120)}"
    if tool == "Skill":
        return f"- {t} 🎯 Skill `{one_line(tool_input.get('skill', ''), 60)}`"
    return None  # read-only and browser tools are not logged


def describe_event(payload: dict[str, Any]) -> list[str]:
    event = payload.get("hook_event_name", "")
    t = f"{now():%H:%M}"
    line: str | None = None
    if event == "SessionStart":
        line = f"- {t} 🟢 Session started · source: {payload.get('source', 'unknown')}"
    elif event == "UserPromptSubmit":
        line = f"- {t} 💬 **Prompt** — {one_line(payload.get('prompt', ''), MAX_PROMPT)}"
    elif event == "PostToolUse":
        line = _describe_tool(t, payload.get("tool_name", ""), payload.get("tool_input") or {})
    elif event == "Stop":
        reply = last_assistant_text(payload.get("transcript_path"))
        line = f"- {t} 🏁 " + (f"**Reply** — {one_line(reply, MAX_REPLY)}" if reply else "Done")
    elif event == "SessionEnd":
        line = f"- {t} 🔴 Session ended · reason: {payload.get('reason', 'unknown')}"
    return [line] if line else []


def session_context() -> str:
    """Short project context printed on SessionStart (added to Claude's context)."""
    status = VAULT / STATUS_NOTE
    lines = [
        "MacroPulse Obsidian vault: `vault/` (open it in Obsidian). Keep curated notes current "
        "per CLAUDE.md §13: Status, phase note, decisions, findings and today's session journal.",
    ]
    if status.exists():
        text = status.read_text(encoding="utf-8")
        match = re.search(r"^## Now\s*\n(.*?)(?=^## |\Z)", text, flags=re.S | re.M)
        if match:
            lines.append("Current status (vault/10 Project/Status.md):")
            lines.append(match.group(1).strip()[:900])
    return "\n".join(lines)


def run_hook(stdin_text: str) -> None:
    payload = json.loads(stdin_text) if stdin_text.strip() else {}
    if not isinstance(payload, dict):
        return
    lines = describe_event(payload)
    if lines:
        is_start = payload.get("hook_event_name") == "SessionStart"
        source = payload.get("source", "") if is_start else ""
        append_log(lines, session_id=payload.get("session_id"), session_label=source)
    if payload.get("hook_event_name") == "SessionStart":
        print(session_context())


# ------------------------------------------------------------------ Codex runs


def _quote_block(text: str, limit: int) -> str:
    body = redact(text.strip())
    if len(body) > limit:
        body = body[:limit].rstrip() + "\n…(truncated)"
    return "\n".join(f"> {line}" if line else ">" for line in body.splitlines())


def record_codex_run(
    *,
    name: str,
    stamp: str,
    exit_code: int,
    sandbox: str,
    network: bool,
    prompt_file: Path | None,
    result_file: Path | None,
) -> Path:
    started = datetime.strptime(stamp, "%Y%m%d-%H%M%S").astimezone()
    prompt = prompt_file.read_text(encoding="utf-8") if prompt_file and prompt_file.exists() else ""
    result = result_file.read_text(encoding="utf-8") if result_file and result_file.exists() else ""
    status = "success" if exit_code == 0 and result.strip() else "failed"
    title = f"{started:%Y-%m-%d %H%M} {name}"
    note = VAULT / CODEX_DIR / f"{title}.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    icon = "✅" if status == "success" else "❌"
    content = (
        "---\n"
        "type: codex-run\n"
        f"name: {name}\n"
        f"date: {started:%Y-%m-%d}\n"
        f'time: "{started:%H:%M}"\n'
        f"status: {status}\n"
        f"exit_code: {exit_code}\n"
        f"sandbox: {sandbox}\n"
        f"network: {str(network).lower()}\n"
        "tags:\n  - agent/codex\n"
        "---\n\n"
        f"# {icon} Codex · {name}\n\n"
        "Delegated by Claude Code via `scripts/agents/codex-task.ps1` on "
        f"{started:%Y-%m-%d %H:%M}. "
        f"Sandbox `{sandbox}`, network {'on' if network else 'off'}, exit code {exit_code}.\n"
        "See [[Agent workflow]] for how delegation and review work.\n\n"
        "> [!summary] Codex report\n"
        f"{_quote_block(result or '(no final report written)', MAX_EMBED)}\n\n"
        "> [!quote]- Brief sent to Codex\n"
        f"{_quote_block(prompt or '(prompt not recorded)', MAX_EMBED)}\n"
    )
    note.write_text(content, encoding="utf-8", newline="\n")
    link = f"[[{CODEX_DIR}/{title}|{name}]]"
    append_log([f"- {now():%H:%M} 🤖 Codex run {link} — {status}, exit {exit_code}"])
    return note


# ------------------------------------------------------------------ CLI


def main(argv: list[str] | None = None) -> int:
    # Hook payloads (e.g. Russian prompts) and our output are UTF-8; Windows defaults to cp1252.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("hook", help="consume a Claude Code hook payload from stdin")
    codex = sub.add_parser("codex-run", help="record a delegated Codex run")
    codex.add_argument("--name", required=True)
    codex.add_argument("--stamp", required=True, help="YYYYmmdd-HHMMSS")
    codex.add_argument("--exit-code", type=int, required=True)
    codex.add_argument("--sandbox", default="workspace-write")
    codex.add_argument("--network", action="store_true")
    codex.add_argument("--prompt-file", type=Path)
    codex.add_argument("--result-file", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "hook":
            run_hook(sys.stdin.read())
        else:
            note = record_codex_run(
                name=args.name,
                stamp=args.stamp,
                exit_code=args.exit_code,
                sandbox=args.sandbox,
                network=args.network,
                prompt_file=args.prompt_file,
                result_file=args.result_file,
            )
            print(f"vault note: {note.relative_to(VAULT).as_posix()}")
    except Exception as exc:  # logging must never break the caller
        print(f"vault_log: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
