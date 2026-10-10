from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class CooldownManager:
    default_seconds: float
    _last_action_times: dict[str, float] = field(default_factory=dict)

    def is_ready(self, action_name: str, cooldown_seconds: float | None = None) -> bool:
        now = time.monotonic()
        last_time = self._last_action_times.get(action_name)

        if last_time is None:
            return True

        required_delay = self.default_seconds if cooldown_seconds is None else cooldown_seconds
        return now - last_time >= required_delay

    def mark_used(self, action_name: str) -> None:
        self._last_action_times[action_name] = time.monotonic()

    def use_if_ready(self, action_name: str, cooldown_seconds: float | None = None) -> bool:
        if not self.is_ready(action_name, cooldown_seconds=cooldown_seconds):
            return False

        self.mark_used(action_name)
        return True

    def remaining_seconds(self, action_name: str, cooldown_seconds: float | None = None) -> float:
        last_time = self._last_action_times.get(action_name)

        if last_time is None:
            return 0.0

        required_delay = self.default_seconds if cooldown_seconds is None else cooldown_seconds
        elapsed = time.monotonic() - last_time

        return max(0.0, required_delay - elapsed)

    def reset(self, action_name: str | None = None) -> None:
        if action_name is None:
            self._last_action_times.clear()
            return

        self._last_action_times.pop(action_name, None)