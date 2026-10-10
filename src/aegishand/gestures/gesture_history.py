from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from time import time


@dataclass(frozen=True)
class GestureHistoryEntry:
    name: str
    confidence: float
    timestamp: float


class GestureHistory:
    def __init__(self, max_size: int = 30) -> None:
        self._history: deque[GestureHistoryEntry] = deque(maxlen=max_size)

    def add(
        self,
        name: str,
        confidence: float,
    ) -> None:
        self._history.append(
            GestureHistoryEntry(
                name=name,
                confidence=confidence,
                timestamp=time(),
            )
        )

    def entries(self) -> list[GestureHistoryEntry]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()

    def latest(self) -> GestureHistoryEntry | None:
        if not self._history:
            return None

        return self._history[-1]

    def count_matching(
        self,
        gesture_name: str,
    ) -> int:
        return sum(
            1
            for entry in self._history
            if entry.name == gesture_name
        )