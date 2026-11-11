Task: write a small secret scanner for the release audit.

## Files
- CREATE `scripts/security_scan.py` — the only file you write. Standard library only (Python 3.12).
- CONTEXT (provided below, do not change): `scripts/tests/test_security_scan.py` — the tests are the
  specification; read every assertion.

## API (module-level, importable)
```python
@dataclass(frozen=True)
class Finding:
    kind: str  # "github-token" | "aws-access-key" | "openai-key" | "anthropic-key" |
    # "google-api-key" | "slack-token" | "private-key" | "secret-assignment" |
    # "database-password" | "server-only-name"
    source: str  # file path (or "path" for history findings)
    line: int  # 1-based line number in the scanned text (0 when unknown)
    preview: str  # the matched text, truncated: first 16 characters of the match + "…"
    commit: str | None = None  # full 40-char commit hash for history findings


SERVER_ONLY_NAMES: tuple[str, ...] = (
    "FRED_API_KEY",
    "fred_api_key",
    "DATABASE_URL",
    "POSTGRES_PASSWORD",
)


def scan_text(text: str, *, source: str) -> list[Finding]: ...
def scan_bundle(static_dir: Path) -> list[Finding]: ...
def scan_git_history(repo: Path) -> list[Finding]: ...
def main(argv: list[str] | None = None) -> int: ...
```

## Rules
1. Token formats (anywhere in a line): `github-token` `gh[pousr]_[A-Za-z0-9]{36,}`; `aws-access-key`
   `AKIA[0-9A-Z]{16}`; `openai-key` `sk-(proj-)?[A-Za-z0-9]{20,}`; `anthropic-key` `sk-ant-[A-Za-z0-9_-]{20,}`
   (check before `openai-key`; report only one kind per match); `google-api-key` `AIza[0-9A-Za-z_-]{35}`;
   `slack-token` `xox[baprs]-[A-Za-z0-9-]{10,}`; `private-key` `-----BEGIN [A-Z ]*PRIVATE KEY-----`.
2. `secret-assignment`: a name containing (case-insensitive) `api_key`, `apikey`, `api-key`, `secret`,
   `token`, `password` or `passwd`, then optional quote, `:` or `=`, optional spaces and quote, then a
   value of at least 16 characters from `[A-Za-z0-9_\-/+]`. NOT a finding when the value is a
   placeholder: empty, starts with `$` or `<` or `${`, contains `your`, `change-me`, `example`,
   `REDACTED`, `xxx` (case-insensitive), or is code such as `os.environ[...]` / `os.getenv(...)`.
   (A value of fewer than 16 allowed characters is not a finding.)
3. `database-password`: `postgres(ql)?(\+\w+)?://USER:PASSWORD@` with a password that is not one of the
   local dev defaults `macropulse`, `postgres`, `change-me-local-only` and does not start with `$`.
4. `preview`: the first 16 characters of the matched text followed by "…" — never the whole secret.
5. `scan_bundle(static_dir)`: every `*.js`, `*.css`, `*.html`, `*.json`, `*.map` file below the
   directory (recursively): `scan_text` findings plus one `server-only-name` finding per line that
   contains any name from `SERVER_ONLY_NAMES` (preview = that name). `source` is the file path.
6. `scan_git_history(repo)`: run `git -C <repo> log -p --all --no-color --format=commit:%H` with
   `subprocess.run([...], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)`;
   track the current commit (lines `commit:<hash>`) and file (`+++ b/<path>`); scan only added lines
   (starting with `+` but not `+++`), passing the line without its `+`. Report each distinct
   (kind, file, preview) once, with the first commit that added it (git log lists newest first, so
   keep the LAST occurrence seen). `line` is 0 for history findings.
7. `main`: argparse with `--history` (scan the git history of the current directory's repo),
   `--bundle PATH` (scan a built static directory) and `--tree PATH...` (scan files); print one line
   per finding `KIND  SOURCE[:LINE]  [COMMIT[:12]]  PREVIEW`, then a summary line; exit code 1 when
   anything was found, 0 otherwise. Reconfigure stdout to UTF-8 (Windows consoles).
8. Full type hints, module docstring, ruff-clean (line length 100; S603/S607 are acceptable for the
   fixed git call — add `# noqa: S603, S607` on that line).

## Out of scope
Do not edit the tests or any other file. The lead runs the tests and sends you any failures.
