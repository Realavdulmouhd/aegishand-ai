import json
from pathlib import Path

from aegishand.diagnostics.event_logger import DiagnosticEventLogger


def test_event_logger_writes_jsonl(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    logger = DiagnosticEventLogger(enabled=True, log_path=str(log_path))

    logger.log(
        "test_event",
        "A safe event was logged.",
        gesture="open_palm",
        frame="should_not_be_saved",
    )

    lines = log_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 1

    event = json.loads(lines[0])

    assert event["event_type"] == "test_event"
    assert event["data"]["gesture"] == "open_palm"
    assert event["data"]["frame"] == "[removed]"


def test_event_logger_respects_disabled_state(tmp_path: Path) -> None:
    log_path = tmp_path / "events.jsonl"
    logger = DiagnosticEventLogger(enabled=False, log_path=str(log_path))

    logger.log("test_event", "This should not be written.")

    assert not log_path.exists()