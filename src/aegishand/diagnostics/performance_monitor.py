from __future__ import annotations

from collections import deque
from statistics import mean


class PerformanceMonitor:
    def __init__(
        self,
        history_size: int = 120,
    ) -> None:
        self.frame_times = deque(maxlen=history_size)

    def add_frame_time(
        self,
        frame_time_ms: float,
    ) -> None:
        self.frame_times.append(frame_time_ms)

    def average_frame_time(self) -> float:
        if not self.frame_times:
            return 0.0

        return mean(self.frame_times)

    def average_fps(self) -> float:
        avg_ms = self.average_frame_time()

        if avg_ms <= 0:
            return 0.0

        return 1000 / avg_ms