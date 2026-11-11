"""Specification tests for scripts/security_scan.py (secret scanner for history, tree and bundle).

The 'secrets' below are fake strings built at runtime so this file itself never matches.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security_scan import (
    SERVER_ONLY_NAMES,
    Finding,
    apply_allowlist,
    load_allowlist,
    scan_bundle,
    scan_git_history,
    scan_text,
)

FAKE_GH = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
FAKE_AWS = "AKIA" + "ABCDEFGHIJKLMNOP"
FAKE_KEY_LINE = "FRED_API_KEY" + "=" + "0123456789abcdef0123456789abcdef"
PRIVATE = "-----BEGIN " + "RSA PRIVATE KEY-----"


def test_detects_known_token_formats_and_assignments() -> None:
    text = "\n".join([f"token: {FAKE_GH}", f"aws = '{FAKE_AWS}'", FAKE_KEY_LINE, PRIVATE])
    found = scan_text(text, source="example.env")
    kinds = {f.kind for f in found}
    assert {"github-token", "aws-access-key", "secret-assignment", "private-key"} <= kinds
    assert all(isinstance(f, Finding) and f.source == "example.env" for f in found)
    assert {f.line for f in found} == {1, 2, 3, 4}


def test_findings_never_print_the_secret() -> None:
    (finding,) = [f for f in scan_text(FAKE_KEY_LINE, source="x") if f.kind == "secret-assignment"]
    assert "0123456789abcdef0123456789abcdef" not in finding.preview
    assert finding.preview == "FRED_API_KEY=012…"  # first 16 characters, as specified
    assert "…" in finding.preview


@pytest.mark.parametrize(
    "line",
    [
        "FRED_API_KEY=",
        "FRED_API_KEY=your-key-here",
        "api_key: ${FRED_API_KEY}",
        'password = "change-me-local-only"',
        "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change-me-local-only}",
        "token = <your token>",
        "api_key=REDACTED",
        "secret_key = os.environ['SECRET_KEY']",
        "postgresql+psycopg://macropulse:macropulse@localhost:5432/macropulse",
        "postgresql+psycopg://${POSTGRES_USER:-mp}:${POSTGRES_PASSWORD:-change-me}@db:5432/mp",
    ],
)
def test_placeholders_and_dev_defaults_are_not_findings(line: str) -> None:
    assert scan_text(line, source="x") == []


def test_database_url_with_a_real_password_is_flagged() -> None:
    url = "postgresql://admin:" + "S3cr3tPassw0rd" + "@db.example.com/prod"
    assert [f.kind for f in scan_text(url, source="x")] == ["database-password"]


def test_bundle_must_not_contain_server_only_names(tmp_path: Path) -> None:
    static = tmp_path / "static" / "chunks"
    static.mkdir(parents=True)
    (static / "a.js").write_text('const x = "hello";', encoding="utf-8")
    assert scan_bundle(tmp_path / "static") == []
    (static / "b.js").write_text("fetch(process.env.DATABASE_URL)", encoding="utf-8")
    found = scan_bundle(tmp_path / "static")
    assert [f.kind for f in found] == ["server-only-name"]
    assert "DATABASE_URL" in SERVER_ONLY_NAMES
    assert "FRED_API_KEY" in SERVER_ONLY_NAMES


def test_git_history_scan_reports_commit_and_file(tmp_path: Path) -> None:
    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)  # noqa: S603, S607

    git("init", "-q")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Test")
    (tmp_path / "clean.txt").write_text("nothing here\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-q", "-m", "clean")
    assert scan_git_history(tmp_path) == []
    (tmp_path / "leak.env").write_text(FAKE_KEY_LINE + "\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-q", "-m", "leak")
    (tmp_path / "leak.env").write_text("FRED_API_KEY=\n", encoding="utf-8")
    git("commit", "-qam", "remove")
    found = scan_git_history(tmp_path)
    assert len(found) == 1  # removed later, still in history
    assert found[0].kind == "secret-assignment"
    assert found[0].source.endswith("leak.env")
    assert len(found[0].commit or "") == 40


def test_allowlist_needs_a_reason_and_skips_only_listed_findings(tmp_path: Path) -> None:
    found = scan_text(FAKE_KEY_LINE + "\n" + f"token: {FAKE_GH}", source="t.py")
    allow = tmp_path / ".security-scan-allow"
    allow.write_text(
        "# reviewed\nsecret-assignment\tt.py\tFRED_API_KEY=012…\tfake value in a test\n",
        encoding="utf-8",
    )
    kept, skipped = apply_allowlist(found, load_allowlist(allow))
    assert skipped == 1
    assert "FRED_API_KEY=012…" not in {f.preview for f in kept}
    assert {f.line for f in kept} == {2}  # the token line is still reported
    allow.write_text("secret-assignment\tt.py\tFRED_API_KEY=012…\t\n", encoding="utf-8")
    with pytest.raises(ValueError, match="reason"):
        load_allowlist(allow)
