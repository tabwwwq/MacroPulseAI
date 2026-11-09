"""Tests for the Obsidian vault logger (loaded from its script path)."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "vault_log.py"


@pytest.fixture
def vl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    spec = importlib.util.spec_from_file_location("vault_log_under_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "VAULT", tmp_path / "vault")
    return module


def _assistant(content: list[dict[str, str]]) -> dict[str, object]:
    return {"message": {"role": "assistant", "content": content}}


def _today_log(vl: ModuleType) -> str:
    return vl._daily_log(vl.now()).read_text(encoding="utf-8")


def test_redacts_secret_shaped_values(vl: ModuleType) -> None:
    text = (
        "set FRED_API_KEY=abcdef0123456789abcdef0123456789 and token: s3cr3t-value "
        "sk-live_ABCDEFGHIJKLMNOPQRST ghp_abcdefghijklmnopqrstuvwxyz123"
    )
    out = vl.redact(text)
    assert "abcdef0123456789" not in out
    assert "s3cr3t-value" not in out
    assert "sk-live" not in out
    assert "ghp_" not in out
    assert "FRED_API_KEY=***" in out


def test_prompt_and_tool_events_append_to_daily_log_with_session_header(vl: ModuleType) -> None:
    vl.run_hook(
        json.dumps(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "abcdef1234",
                "prompt": "Build   the\nPhase 2 UI",
            }
        )
    )
    vl.run_hook(
        json.dumps(
            {
                "hook_event_name": "PostToolUse",
                "session_id": "abcdef1234",
                "tool_name": "PowerShell",
                "tool_input": {"command": "pnpm test", "description": "Run tests"},
            }
        )
    )
    vl.run_hook(
        json.dumps(
            {
                "hook_event_name": "PostToolUse",
                "session_id": "abcdef1234",
                "tool_name": "Read",
                "tool_input": {"file_path": "x"},
            }
        )
    )
    log = _today_log(vl)
    assert log.startswith("---\ntype: activity-log")
    assert log.count("session `abcdef12`") == 1  # header written once per session per day
    assert "💬 **Prompt** — Build the Phase 2 UI" in log
    assert "⚙️ Run tests — `pnpm test`" in log
    assert "Read" not in log.split("## ")[-1]  # read-only tools are not logged


def test_stop_logs_the_final_assistant_reply(vl: ModuleType, tmp_path: Path) -> None:
    transcript = tmp_path / "t.jsonl"
    transcript.write_text(
        "\n".join(
            [
                json.dumps({"message": {"role": "user", "content": "hi"}}),
                json.dumps(_assistant([{"type": "text", "text": "Done: all tests pass."}])),
                json.dumps(_assistant([{"type": "tool_use", "name": "x"}])),
            ]
        ),
        encoding="utf-8",
    )
    vl.run_hook(
        json.dumps(
            {
                "hook_event_name": "Stop",
                "session_id": "s1234567",
                "transcript_path": str(transcript),
            }
        )
    )
    assert "🏁 **Reply** — Done: all tests pass." in _today_log(vl)


def test_session_start_prints_status_context(
    vl: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    status = vl.VAULT / "10 Project" / "Status.md"
    status.parent.mkdir(parents=True)
    status.write_text(
        "# Status\n\n## Now\nPhase 2 in progress.\n\n## Next\nPhase 3\n", encoding="utf-8"
    )
    vl.run_hook(
        json.dumps(
            {"hook_event_name": "SessionStart", "session_id": "s7654321", "source": "startup"}
        )
    )
    out = capsys.readouterr().out
    assert "Phase 2 in progress." in out
    assert "Phase 3" not in out
    assert "🟢 Session started" in _today_log(vl)


def test_codex_run_creates_note_and_log_entry(vl: ModuleType, tmp_path: Path) -> None:
    prompt = tmp_path / "p.md"
    result = tmp_path / "r.md"
    prompt.write_text("Do the thing. key=abcdef0123456789abcdef0123456789", encoding="utf-8")
    result.write_text("1. Summary: done", encoding="utf-8")
    note = vl.record_codex_run(
        name="probe",
        stamp="20261108-230755",
        exit_code=0,
        sandbox="workspace-write",
        network=True,
        prompt_file=prompt,
        result_file=result,
    )
    body = note.read_text(encoding="utf-8")
    assert note.name == "2026-11-08 2307 probe.md"
    assert "status: success" in body
    assert "> 1. Summary: done" in body
    assert "abcdef0123456789" not in body
    assert "[[60 Agents/Codex runs/2026-11-08 2307 probe|probe]]" in _today_log(vl)


def test_bad_input_never_raises(vl: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("{not json"))
    assert vl.main(["hook"]) == 0
