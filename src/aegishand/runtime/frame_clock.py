from __future__ import annotations

import time

from aegishand.core.types import FrameTiming


class FrameClock:
    def __init__(self) -> None:
        self._last_frame_time = time.perf_counter()
        self._frame_id = 0

    def tick(self) -> FrameTiming:
        current_time = time.perf_counter()

        delta_time = current_time - self._last_frame_time
        self._last_frame_time = current_time

        fps = 1.0 / delta_time if delta_time > 0 else 0.0

        self._frame_id += 1

        return FrameTiming(
            frame_id=self._frame_id,
            delta_time=delta_time,
            fps=fps,
        )