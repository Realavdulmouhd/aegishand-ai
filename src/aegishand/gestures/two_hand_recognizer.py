from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from aegishand.gestures.finger_state import FingerStateDetector
from aegishand.gestures.gesture_types import GestureType, RecognizedGesture
from aegishand.vision.landmark_utils import NormalizedLandmark, landmark_distance


class HandLike(Protocol):
    handedness: str
    confidence: float
    landmarks: tuple[NormalizedLandmark, ...]


@dataclass(frozen=True)
class TwoHandGestureConfig:
    min_hand_confidence: float = 0.60
    zoom_delta_threshold: float = 0.045


class TwoHandGestureRecognizer:
    def __init__(
        self,
        config: TwoHandGestureConfig | None = None,
        finger_detector: FingerStateDetector | None = None,
    ) -> None:
        self.config = config or TwoHandGestureConfig()
        self.finger_detector = finger_detector or FingerStateDetector()
        self._previous_hand_distance: float | None = None

    def recognize(self, hands: tuple[HandLike, ...]) -> RecognizedGesture | None:
        if len(hands) < 2:
            self._previous_hand_distance = None
            return None

        first, second = hands[0], hands[1]

        if (
            first.confidence < self.config.min_hand_confidence
            or second.confidence < self.config.min_hand_confidence
        ):
            return RecognizedGesture.unknown()

        first_state = self.finger_detector.detect(first)
        second_state = self.finger_detector.detect(second)

        if first_state.none_extended and second_state.none_extended:
            self._previous_hand_distance = None
            return RecognizedGesture(
                gesture=GestureType.TWO_HAND_LOCK,
                confidence=0.94,
            )

        if not (first_state.all_extended and second_state.all_extended):
            self._previous_hand_distance = None
            return None

        current_distance = landmark_distance(
            first.landmarks[0],
            second.landmarks[0],
        )

        if self._previous_hand_distance is None:
            self._previous_hand_distance = current_distance
            return None

        delta = current_distance - self._previous_hand_distance
        self._previous_hand_distance = current_distance

        if abs(delta) < self.config.zoom_delta_threshold:
            return None

        if delta > 0:
            return RecognizedGesture(
                gesture=GestureType.TWO_HAND_ZOOM_IN,
                confidence=0.82,
            )

        return RecognizedGesture(
            gesture=GestureType.TWO_HAND_ZOOM_OUT,
            confidence=0.82,
        )