from __future__ import annotations

from time import time


class DwellDetector:
    """
    Confirms that a gesture remains stable
    for a minimum duration before activation.
    """

    def __init__(
        self,
        required_hold_ms: int = 220,
    ) -> None:
        self.required_hold_ms = required_hold_ms

        self._active_gesture: str | None = None
        self._gesture_start_time: float | None = None

    def update(
        self,
        gesture_name: str,
    ) -> bool:
        current_time = time()

        if gesture_name != self._active_gesture:
            self._active_gesture = gesture_name
            self._gesture_start_time = current_time
            return False

        if self._gesture_start_time is None:
            return False

        held_duration_ms = (
            current_time - self._gesture_start_time
        ) * 1000

        return held_duration_ms >= self.required_hold_ms

    def reset(self) -> None:
        self._active_gesture = None
        self._gesture_start_time = None