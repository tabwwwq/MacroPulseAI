"""Secret scanner for the MacroPulse release audit.

Scans source text, built static bundles and git history for leaked secrets.
Standard library only (Python 3.12).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SERVER_ONLY_NAMES: tuple[str, ...] = (
    "FRED_API_KEY",
    "fred_api_key",
    "DATABASE_URL",
    "POSTGRES_PASSWORD",
)

_BUNDLE_SUFFIXES = {".js", ".css", ".html", ".json", ".map"}

_TOKEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai-key", re.compile(r"sk-(proj-)?[A-Za-z0-9]{20,}")),
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("google-api-key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("slack-token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

_SECRET_NAME_RE = re.compile(
    r"(?i)\b([A-Za-z0-9_.-]*(?:api_key|apikey|api-key|secret|token|password|passwd)[A-Za-z0-9_.-]*)"
    r"\s*['\"]?\s*[:=]\s*['\"]?\s*"
    r"([A-Za-z0-9_\-/+]*)",
)

_DB_URL_RE = re.compile(
    r"postgres(ql)?(\+\w+)?://([^:/@]+):([^@]+)@",
    re.IGNORECASE,
)

_DEV_PASSWORDS = {"macropulse", "postgres", "change-me-local-only"}

_PLACEHOLDER_MARKERS = ("your", "change-me", "example", "redacted", "xxx")


@dataclass(frozen=True)
class Finding:
    kind: str
    source: str
    line: int
    preview: str
    commit: str | None = None


def _preview(matched: str) -> str:
    return matched[:16] + "…"


def _is_placeholder(value: str) -> bool:
    if not value:
        return True
    if value.startswith("$") or value.startswith("<"):
        return True
    low = value.lower()
    return any(marker in low for marker in _PLACEHOLDER_MARKERS)


def _scan_secret_assignments(line: str, source: str, line_no: int) -> list[Finding]:
    findings: list[Finding] = []
    for m in _SECRET_NAME_RE.finditer(line):
        value = m.group(2)
        if len(value) < 16:
            continue
        if _is_placeholder(value):
            continue
        matched = line[m.start() : m.end()]
        findings.append(
            Finding(
                kind="secret-assignment",
                source=source,
                line=line_no,
                preview=_preview(matched),
            )
        )
    return findings


def _scan_database_passwords(line: str, source: str, line_no: int) -> list[Finding]:
    findings: list[Finding] = []
    for m in _DB_URL_RE.finditer(line):
        password = m.group(4)
        if password in _DEV_PASSWORDS:
            continue
        if "$" in password:  # shell / compose interpolation such as ${POSTGRES_PASSWORD:-...}
            continue
        findings.append(
            Finding(
                kind="database-password",
                source=source,
                line=line_no,
                preview=_preview(m.group(0)),
            )
        )
    return findings


def scan_text(text: str, *, source: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.split("\n")
    for line_no, line in enumerate(lines, start=1):
        for kind, pattern in _TOKEN_PATTERNS:
            for m in pattern.finditer(line):
                findings.append(
                    Finding(
                        kind=kind,
                        source=source,
                        line=line_no,
                        preview=_preview(m.group(0)),
                    )
                )
        findings.extend(_scan_secret_assignments(line, source, line_no))
        findings.extend(_scan_database_passwords(line, source, line_no))
    return findings


def scan_bundle(static_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(static_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in _BUNDLE_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        findings.extend(scan_text(text, source=path.as_posix()))
        for line_no, line in enumerate(text.split("\n"), start=1):
            for name in SERVER_ONLY_NAMES:
                if name in line:
                    findings.append(
                        Finding(
                            kind="server-only-name",
                            source=path.as_posix(),
                            line=line_no,
                            preview=name,
                        )
                    )
    return findings


def scan_git_history(repo: Path) -> list[Finding]:
    result = subprocess.run(  # noqa: S603
        ["git", "-C", str(repo), "log", "-p", "--all", "--no-color", "--format=commit:%H"],  # noqa: S607
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    output = result.stdout
    # Map (kind, file, preview) -> Finding with the LAST commit seen (oldest commit).
    seen: dict[tuple[str, str, str], Finding] = {}
    current_commit: str | None = None
    current_file: str | None = None
    for raw_line in output.split("\n"):
        if raw_line.startswith("commit:"):
            current_commit = raw_line[len("commit:") :].strip()
            current_file = None
            continue
        if raw_line.startswith("+++ b/"):
            current_file = raw_line[len("+++ b/") :]
            continue
        if raw_line.startswith("diff --git"):
            current_file = None
            continue
        if current_commit is None or current_file is None:
            continue
        if not raw_line.startswith("+") or raw_line.startswith("+++"):
            continue
        added_line = raw_line[1:]
        for finding in scan_text(added_line, source=current_file):
            key = (finding.kind, finding.source, finding.preview)
            seen[key] = Finding(
                kind=finding.kind,
                source=finding.source,
                line=0,
                preview=finding.preview,
                commit=current_commit,
            )
    return list(seen.values())


def load_allowlist(path: Path) -> set[tuple[str, str, str]]:
    """Reviewed false positives: lines `kind<TAB>source<TAB>preview<TAB>reason` ('#' comments)."""
    allowed: set[tuple[str, str, str]] = set()
    if not path.exists():
        return allowed
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) < 4 or not parts[3].strip():
            raise ValueError(
                f"{path}: every entry needs kind, source, preview and a reason: {raw!r}"
            )
        allowed.add((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return allowed


def apply_allowlist(
    findings: list[Finding], allowed: set[tuple[str, str, str]]
) -> tuple[list[Finding], int]:
    kept = [f for f in findings if (f.kind, f.source, f.preview) not in allowed]
    return kept, len(findings) - len(kept)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Secret scanner for release audit.")
    parser.add_argument("--history", action="store_true", help="Scan git history of current repo.")
    parser.add_argument("--bundle", type=Path, help="Scan a built static directory.")
    parser.add_argument("--tree", nargs="+", type=Path, help="Scan specific files.")
    parser.add_argument(
        "--allow",
        type=Path,
        default=Path(".security-scan-allow"),
        help="Reviewed false positives (default: .security-scan-allow).",
    )
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    if args.history:
        findings.extend(scan_git_history(Path.cwd()))
    if args.bundle is not None:
        findings.extend(scan_bundle(args.bundle))
    if args.tree:
        for path in args.tree:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            findings.extend(scan_text(text, source=path.as_posix()))

    findings, allowed = apply_allowlist(findings, load_allowlist(args.allow))
    for f in findings:
        location = f"{f.source}:{f.line}" if f.line else f.source
        commit_part = f" {f.commit[:12]}" if f.commit else ""
        print(f"{f.kind}  {location}{commit_part}  {f.preview}")

    print(f"Summary: {len(findings)} finding(s), {allowed} reviewed false positive(s) skipped")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
