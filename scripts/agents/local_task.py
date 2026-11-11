"""Delegate a single-file task to the local open-weight model (llama.cpp `llama-server`).

The lead (Claude) writes a brief, picks the context files and the ONE output file. The model gets
everything in one request and must answer with the complete file in a single fenced code block;
this script writes only that file, so the model cannot touch anything else. For a revision, pass
`--feedback` (test failures, review notes): the current file and the feedback are sent back.

    uv run --no-project python scripts/agents/local_task.py --name report-charts \
        --brief .agents/briefs/report-charts.md \
        --context apps/api/src/macropulse_api/reports/content.py \
        --output apps/api/src/macropulse_api/reports/charts.py

Every run is stored under .agents/local-runs/<stamp>-<name>.{prompt.md,response.md,meta.json} and
recorded in the Obsidian vault like a Codex run. Standard library only.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / ".agents" / "local-runs"
FENCE = re.compile(r"```[a-zA-Z0-9_+-]*\n(.*?)```", re.DOTALL)
SYSTEM = (
    "You are a careful senior engineer on the MacroPulse AI repository (FastAPI + Next.js). "
    "Follow the brief exactly; it is the specification. Never invent data, APIs or modules that "
    "are not in the provided context or the standard library / listed dependencies. "
    "Answer with the COMPLETE content of the requested file in exactly one fenced code block, "
    "followed by at most five short bullet points on decisions or doubts. No other code blocks."
)


def _rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _safe_output(raw: str) -> Path:
    path = (ROOT / raw).resolve()
    if ROOT not in path.parents:
        raise SystemExit(f"output must be inside the repository: {raw}")
    if any(part in {".git", ".venv", "node_modules"} for part in path.parts):
        raise SystemExit(f"refusing to write into {raw}")
    return path


def build_messages(
    brief: str, context: list[Path], output: Path, feedback: str | None
) -> list[dict]:
    parts = [
        f"# Brief\n\n{brief.strip()}\n",
        f"# Output file\n\n`{_rel(output)}`\n",
        "# Context files\n",
    ]
    for path in context:
        lang = path.suffix.lstrip(".") or "text"
        parts.append(f"## `{_rel(path)}`\n\n```{lang}\n{path.read_text(encoding='utf-8')}\n```\n")
    if feedback is not None:
        current = (
            output.read_text(encoding="utf-8") if output.exists() else "(file does not exist yet)"
        )
        parts.append(f"# Your previous version of `{_rel(output)}`\n\n```\n{current}\n```\n")
        parts.append(
            "# Review feedback (fix every point; keep what already works)\n\n" + feedback.strip()
        )
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "\n".join(parts)}]


def call(url: str, messages: list[dict[str, str]], max_tokens: int, think: bool) -> dict:
    body = {
        "model": "local",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "chat_template_kwargs": {"enable_thinking": think},
    }
    req = urllib.request.Request(  # noqa: S310 - URL checked to be local below
        f"{url}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    if not url.startswith(("http://127.0.0.1", "http://localhost")):
        raise SystemExit("--url must point at a local server")
    with urllib.request.urlopen(req, timeout=3600) as r:  # noqa: S310 - checked local URL
        return json.load(r)


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0915 - linear CLI flow
    if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to a legacy code page
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", required=True)
    ap.add_argument("--brief", required=True, type=Path)
    ap.add_argument("--context", nargs="*", default=[], type=Path)
    ap.add_argument("--output", required=True)
    ap.add_argument("--feedback", type=Path, help="review notes / test output for a revision")
    ap.add_argument("--url", default="http://127.0.0.1:8080/v1")
    ap.add_argument("--max-tokens", type=int, default=12000)
    ap.add_argument("--think", action="store_true", help="let the model reason before answering")
    args = ap.parse_args(argv)

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,40}", args.name):
        raise SystemExit("--name must be a short slug")
    output = _safe_output(args.output)
    brief = (ROOT / args.brief).read_text(encoding="utf-8")
    context = [(ROOT / p).resolve() for p in args.context]
    feedback = (ROOT / args.feedback).read_text(encoding="utf-8") if args.feedback else None
    messages = build_messages(brief, context, output, feedback)

    RUNS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    base = RUNS / f"{stamp}-{args.name}"
    prompt_file = base.with_suffix(".prompt.md")
    prompt_file.write_text(messages[1]["content"], encoding="utf-8")

    t0 = time.perf_counter()
    try:
        reply = call(args.url, messages, args.max_tokens, args.think)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"[local-task] server not reachable or timed out: {exc}", file=sys.stderr)
        return 2
    seconds = time.perf_counter() - t0
    message = reply["choices"][0]["message"]
    text = message.get("content") or ""
    result_file = base.with_suffix(".response.md")
    result_file.write_text(text, encoding="utf-8")
    timings = reply.get("timings", {})
    meta = {
        "name": args.name,
        "output": _rel(output),
        "revision": feedback is not None,
        "seconds": round(seconds, 1),
        "prompt_tokens": timings.get("prompt_n"),
        "completion_tokens": timings.get("predicted_n"),
        "tokens_per_second": round(timings.get("predicted_per_second", 0), 1),
        "finish_reason": reply["choices"][0].get("finish_reason"),
    }
    base.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    blocks = FENCE.findall(text)
    code = 1
    if len(blocks) != 1:
        print(f"[local-task] expected exactly one code block, got {len(blocks)}; nothing written.")
    elif meta["finish_reason"] == "length":
        print("[local-task] answer was cut off (max tokens); nothing written.")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(blocks[0], encoding="utf-8", newline="\n")
        print(f"[local-task] wrote {_rel(output)} ({len(blocks[0].splitlines())} lines)")
        code = 0
    print(f"[local-task] {json.dumps(meta)}")
    notes = FENCE.sub("", text).strip()
    if notes:
        print("[local-task] model notes:\n" + notes[:1500])
    with contextlib.suppress(OSError, subprocess.SubprocessError):
        subprocess.run(  # noqa: S603 - fixed argv, local script
            [
                sys.executable,
                str(ROOT / "scripts" / "obsidian" / "vault_log.py"),
                "codex-run",
                "--name",
                f"local-{args.name}",
                "--stamp",
                stamp,
                "--exit-code",
                str(code),
                "--sandbox",
                "local-single-file",
                "--prompt-file",
                str(prompt_file),
                "--result-file",
                str(result_file),
            ],
            check=False,
            capture_output=True,
            timeout=60,
        )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
