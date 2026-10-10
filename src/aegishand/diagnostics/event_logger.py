from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DiagnosticEvent:
    event_type: str
    message: str
    data: dict[str, Any]
    timestamp: float


class DiagnosticEventLogger:
    def __init__(self, enabled: bool, log_path: str) -> None:
        self.enabled = enabled
        self.log_path = Path(log_path)

        if self.enabled:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event_type: str, message: str, **data: Any) -> None:
        if not self.enabled:
            return

        event = DiagnosticEvent(
            event_type=event_type,
            message=message,
            data=_clean_data(data),
            timestamp=time.time(),
        )

        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")


def _clean_data(data: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}

    blocked_keys = {
        "frame",
        "image",
        "raw_image",
        "camera_frame",
        "password",
        "token",
        "secret",
        "credential",
    }

    for key, value in data.items():
        normalized_key = key.lower()

        if normalized_key in blocked_keys:
            safe[key] = "[removed]"
            continue

        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        else:
            safe[key] = str(value)

    return safe