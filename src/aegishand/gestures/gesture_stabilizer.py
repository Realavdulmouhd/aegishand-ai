from __future__ import annotations

from aegishand.core.events import (
    GestureCandidate,
    StableGesture,
)
from aegishand.gestures.dwell_detector import DwellDetector
from aegishand.gestures.gesture_history import GestureHistory


class GestureStabilizer:
    """
    Converts noisy frame-level gesture candidates
    into stable interaction-ready gestures.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.80,
        required_consistent_frames: int = 5,
        required_hold_ms: int = 220,
        history_size: int = 30,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.required_consistent_frames = (
            required_consistent_frames
        )

        self.history = GestureHistory(
            max_size=history_size
        )

        self.dwell_detector = DwellDetector(
            required_hold_ms=required_hold_ms
        )

        self._last_stable_gesture: str | None = None

    def update(
        self,
        candidate: GestureCandidate,
    ) -> StableGesture | None:
        if candidate.confidence < self.confidence_threshold:
            return None

        self.history.add(
            name=candidate.name,
            confidence=candidate.confidence,
        )

        matching_frames = self.history.count_matching(
            candidate.name
        )

        if (
            matching_frames
            < self.required_consistent_frames
        ):
            return None

        dwell_confirmed = self.dwell_detector.update(
            candidate.name
        )

        if not dwell_confirmed:
            return None

        if candidate.name == self._last_stable_gesture:
            return None

        self._last_stable_gesture = candidate.name

        return StableGesture(
            name=candidate.name,
            confidence=candidate.confidence,
            hold_time_ms=candidate.duration_ms,
            handedness=candidate.handedness,
        )

    def reset(self) -> None:
        self.history.clear()
        self.dwell_detector.reset()
        self._last_stable_gesture = None