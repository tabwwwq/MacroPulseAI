---
type: codex-run
name: local-security-scan
date: 2026-11-11
time: "11:59"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-security-scan

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-11 11:59. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```python
> """Secret scanner for the MacroPulse release audit.
>
> Scans source text, built static bundles and git history for leaked secrets.
> Standard library only (Python 3.12).
> """
>
> from __future__ import annotations
>
> import argparse
> import re
> import subprocess
> import sys
> from dataclasses import dataclass
> from pathlib import Path
>
> SERVER_ONLY_NAMES: tuple[str, ...] = (
>     "FRED_API_KEY",
>     "fred_api_key",
>     "DATABASE_URL",
>     "POSTGRES_PASSWORD",
> )
>
> _BUNDLE_SUFFIXES = {".js", ".css", ".html", ".json", ".map"}
>
> _TOKEN_PATTERNS:*** re.Pattern[str]]] = [
>     ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
>     ("openai-key", re.compile(r"sk-(proj-)?[A-Za-z0-9]{20,}")),
>     ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
>     ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
>     ("google-api-key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
>     ("slack-token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
>     ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
> ]
>
> _SECRET_NAME_RE=***
>     r"(?i)\b([A-Za-z0-9_.-]*(?:api_key|apikey|api-key|secret|token|password|passwd)[A-Za-z0-9_.-]*)"
>     r"\s*['\"]?\s*[:=]\s*['\"]?\s*"
>     r"([A-Za-z0-9_\-/+]*)",
> )
>
> _DB_URL_RE = re.compile(
>     r"postgres(ql)?(\+\w+)?://([^:/@]+):([^@]+)@",
>     re.IGNORECASE,
> )
>
> _DEV_PASSWORDS=*** "postgres", "change-me-local-only"}
>
> _PLACEHOLDER_MARKERS = ("your", "change-me", "example", "redacted", "xxx")
>
>
> @dataclass(frozen=True)
> class Finding:
>     kind: str
>     source: str
>     line: int
>     preview: str
>     commit: str | None = None
>
>
> def _preview(matched: str) -> str:
>     return matched[:16] + "…"
>
>
> def _is_placeholder(value: str) -> bool:
>     if not value:
>         return True
>     if value.startswith("$") or value.startswith("<"):
>         return True
>     low = value.lower()
>     for marker in _PLACEHOLDER_MARKERS:
>         if marker in low:
>             return True
>     return False
>
>
> def _scan_secret_assignments(line: str, source: str, line_no: int) -> list[Finding]:
>     findings: list[Finding] = []
>     for m in _SECRET_NAME_RE.finditer(line):
>         name = m.group(1)
>         value = m.group(2)
>         if len(value) < 16:
>             continue
>         if _is_placeholder(value):
>             continue
>         matched = line[m.start() : m.end()]
>         findings.append(
>             Finding(
>                 kind="secret-assignment",
>                 source=source,
>                 line=line_no,
>                 preview=_preview(matched),
>             )
>         )
>     return findings
>
>
> def _scan_database_passwords(line: str, source: str, line_no: int) -> list[Finding]:
>     findings: list[Finding] = []
>     for m in _DB_URL_RE.finditer(line):
>         password=***
>         if password in _DEV_PASSWORDS:***
>         if password.startswith("$"):
>             continue
>         findings.append(
>             Finding(
>                 kind="database-password",
>                 source=source,
>                 line=line_no,
>                 preview=_preview(m.group(0)),
>             )
>         )
>     return findings
>
>
> def scan_text(text: str, *, source: str) -> list[Finding]:
>     findings: list[Finding] = []
>     lines = text.split("\n")
>     for line_no, line in enumerate(lines, start=1):
>         for kind, pattern in _TOKEN_PATTERNS:*** m in pattern.finditer(line):
>                 findings.append(
>                     Finding(
>                         kind=kind,
>                         source=source,
>                         line=line_no,
>                         preview=_preview(m.group(0)),
>                     )
>                 )
>         findings.extend(_scan_secret_assignments(line, source, line_no))
>         findings.extend(_scan_database_passwords(line, source, line_no))
>     return findings
>
>
> def scan_bundle(static_dir: Path) -> list[Finding]:
>     findings: list[Finding] = []
>     for path in sorted(static_dir.rglob("*")):
>         if not path.is_file():
>             continue
>         if path.suffix not in _BUNDLE_SUFFIXES:
>             continue
>         try:
>             text = path.read_text(encoding="utf-8", errors="replace")
>         except OSError:
>             continue
>         findings.extend(scan_text(text, source=str(path)))
>         for line_no, line in enumerate(text.split("\n"), start=1):
>             for name in SERVER_ONLY_NAMES:
>                 if name in line:
>                     findings.append(
>                         Finding(
>                             kind="server-only-name",
>                             source=str(path),
>                             line=line_no,
>                             preview=name,
>                         )
>                     )
>     return findings
>
>
> def scan_git_history(repo: Path) -> list[Finding]:
>     result = subprocess.run(  # noqa: S603, S607
>         ["git", "-C", str(repo), "log", "-p", "--all", "--no-color", "--format=commit:%H"],
>         capture_output=True,
>         text=True,
>         encoding="utf-8",
>         errors="replace",
>         check=True,
>     )
>     output = result.stdout
>     # Map (kind, file, preview) -> Finding with the LAST commit seen (oldest commit).
>     seen: dict[tuple[str, str, str], Finding] = {}
>     current_commit: str | None = None
>     current_file: str | None = None
>     for raw_line in output.split("\n"):
>         if raw_line.startswith("commit:"):
>             current_commit = raw_line[len("commit:") :].strip()
>             current_file = None
>             continue
>         if raw_line.startswith("+++ b/"):
>             current_file = raw_line[len("+++ b/") :]
>             continue
>         if raw_line.startswith("diff --git"):
>             current_file = None
>             continue
>         if current_commit is None or current_file is None:
>             continue
>         if not raw_line.startswith("+") or raw_line.startswith("+++"):
>             continue
>         added_line = raw_line[1:]
>         for finding in scan_text(added_line, source=current_file):
>             key = (finding.kind, finding.source, finding.preview)
>             seen[key] = Finding(
>                 kin
> …(truncated)

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write a small secret scanner for the release audit.
>
> ## Files
> - CREATE `scripts/security_scan.py` — the only file you write. Standard library only (Python 3.12).
> - CONTEXT (provided below, do not change): `scripts/tests/test_security_scan.py` — the tests are the
>   specification; read every assertion.
>
> ## API (module-level, importable)
> ```python
> @dataclass(frozen=True)
> class Finding:
>     kind: str            # "github-token" | "aws-access-key" | "openai-key" | "anthropic-key" |
>                          # "google-api-key" | "slack-token" | "private-key" | "secret-assignment" |
>                          # "database-password" | "server-only-name"
>     source: str          # file path (or "path" for history findings)
>     line: int            # 1-based line number in the scanned text (0 when unknown)
>     preview: str         # the matched text, truncated: first 16 characters of the match + "…"
>     commit: str | None = None   # full 40-char commit hash for history findings
>
> SERVER_ONLY_NAMES: tuple[str, ...] = ("FRED_API_KEY", "fred_api_key", "DATABASE_URL", "POSTGRES_PASSWORD")
>
> def scan_text(text: str, *, source: str) -> list[Finding]: ...
> def scan_bundle(static_dir: Path) -> list[Finding]: ...
> def scan_git_history(repo: Path) -> list[Finding]: ...
> def main(argv: list[str] | None = None) -> int: ...
> ```
>
> ## Rules
> 1. Token formats (anywhere in a line): `github-token` `gh[pousr]_[A-Za-z0-9]{36,}`; `aws-access-key`
>    `AKIA[0-9A-Z]{16}`; `openai-key` `sk-(proj-)?[A-Za-z0-9]{20,}`; `anthropic-key` `sk-ant-[A-Za-z0-9_-]{20,}`
>    (check before `openai-key`; report only one kind per match); `google-api-key` `AIza[0-9A-Za-z_-]{35}`;
>    `slack-token` `xox[baprs]-[A-Za-z0-9-]{10,}`; `private-key` `-----BEGIN [A-Z ]*PRIVATE KEY-----`.
> 2. `secret-assignment`: a name containing (case-insensitive) `api_key`, `apikey`, `api-key`, `secret`,
>    `token`, `password` or `passwd`, then optional quote, `:` or `=`, optional spaces and quote, then a
>    value of at least 16 characters from `[A-Za-z0-9_\-/+]`. NOT a finding when the value is a
>    placeholder: empty, starts with `$` or `<` or `${`, contains `your`, `change-me`, `example`,
>    `REDACTED`, `xxx` (case-insensitive), or is code such as `os.environ[...]` / `os.getenv(...)`.
>    (A value of fewer than 16 allowed characters is not a finding.)
> 3. `database-password`: `postgres(ql)?(\+\w+)?://USER:PASSWORD@` with a password that is not one of the
>    local dev defaults `macropulse`, `postgres`, `change-me-local-only` and does not start with `$`.
> 4. `preview`: the first 16 characters of the matched text followed by "…" — never the whole secret.
> 5. `scan_bundle(static_dir)`: every `*.js`, `*.css`, `*.html`, `*.json`, `*.map` file below the
>    directory (recursively): `scan_text` findings plus one `server-only-name` finding per line that
>    contains any name from `SERVER_ONLY_NAMES` (preview = that name). `source` is the file path.
> 6. `scan_git_history(repo)`: run `git -C <repo> log -p --all --no-color --format=commit:%H` with
>    `subprocess.run([...], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)`;
>    track the current commit (lines `commit:<hash>`) and file (`+++ b/<path>`); scan only added lines
>    (starting with `+` but not `+++`), passing the line without its `+`. Report each distinct
>    (kind, file, preview) once, with the first commit that added it (git log lists newest first, so
>    keep the LAST occurrence seen). `line` is 0 for history findings.
> 7. `main`: argparse with `--history` (scan the git history of the current directory's repo),
>    `--bundle PATH` (scan a built static directory) and `--tree PATH...` (scan files); print one line
>    per finding `KIND  SOURCE[:LINE]  [COMMIT[:12]]  PREVIEW`, then a summary line; exit code 1 when
>    anything was found, 0 otherwise. Reconfigure stdout to UTF-8 (Windows consoles).
> 8. Full type hints, module docstring, ruff-clean (line length 100; S603/S607 are acceptable for the
>    fixed git call — add `# noqa: S603, S607` on that line).
>
> ## Out of scope
> Do not edit the tests or any other file. The lead runs the tests and sends you any failures.
>
> # Output file
>
> `scripts/security_scan.py`
>
> # Context files
>
> ## `scripts/tests/test_security_scan.py`
>
> ```py
> """Specification tests for scripts/security_scan.py (secret scanner for history, tree and bundle).
>
> The 'secrets' below are fake strings built at runtime so this file itself never matches.
> """
>
> from __future__ import annotations
>
> import subprocess
> import sys
> from pathlib import Path
>
> import pytest
>
> sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
>
> from security_scan import (  # noqa: E402
>     SERVER_ONLY_NAMES,
>     Finding,
>     scan_bundle,
>     scan_git_history,
>     scan_text,
> )
>
> FAKE_GH = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
> FAKE_AWS = "AKIA" + "ABCDEFGHIJKLMNOP"
> FAKE_KEY_LINE = "FRED_API_KEY" + "=" + "***"
> PRIVATE = "-----BEGIN " + "RSA PRIVATE KEY-----"
>
>
> def test_detects_known_token_formats_and_assignments() -> None:
>     text = "\n".join([f"token:*** f"aws = '{FAKE_AWS}'", FAKE_KEY_LINE, PRIVATE])
>     found = scan_text(text, source="example.env")
>     kinds = {f.kind for f in found}
>     assert {"github-token", "aws-access-key", "secret-assignment", "private-key"} <= kinds
>     assert all(isinstance(f, Finding) and f.source == "example.env" for f in found)
>     assert {f.line for f in found} == {1, 2, 3, 4}
>
>
> def test_findings_never_print_the_secret() -> None:
>     (finding,) = [f for f in scan_text(FAKE_KEY_LINE, source="x") if f.kind == "secret-assignment"]
>     assert "***" not in finding.preview
>     assert finding.preview.startswith("FRED_API_KEY=***
>     assert "…" in finding.preview
>
>
> @pytest.mark.parametrize(
>     "line",
>     [
>         "FRED_API_KEY=***FRED_API_KEY=***
>         "api_key:***
>         'password=***',
>         "POSTGRES_PASSWORD:***
>         "token=*** token>",
>         "api_key=***
>         "secret_key=***
>         "postgresql+psycopg://macropulse:macropulse@localhost:5432/macropulse",
>     ],
> )
> …(truncated)
