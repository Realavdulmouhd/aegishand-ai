from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from aegishand.gestures.finger_state import FingerStateDetector
from aegishand.gestures.gesture_types import GestureType, RecognizedGesture
from aegishand.vision.landmark_utils import (
    NormalizedLandmark,
    distance_between_indexes,
)


class HandLike(Protocol):
    handedness: str
    confidence: float
    landmarks: tuple[NormalizedLandmark, ...]


@dataclass(frozen=True)
class GestureRecognizerConfig:
    pinch_distance_threshold: float = 0.055
    min_hand_confidence: float = 0.55


class RuleBasedGestureRecognizer:
    def __init__(
        self,
        config: GestureRecognizerConfig | None = None,
        finger_detector: FingerStateDetector | None = None,
    ) -> None:
        self.config = config or GestureRecognizerConfig()
        self.finger_detector = finger_detector or FingerStateDetector()

    def recognize(self, hand: HandLike | None) -> RecognizedGesture:
        if hand is None:
            return RecognizedGesture.no_hand()

        if hand.confidence < self.config.min_hand_confidence:
            return RecognizedGesture.unknown()

        finger_state = self.finger_detector.detect(hand)

        if self._is_pinch(hand):
            return RecognizedGesture(
                gesture=GestureType.PINCH,
                confidence=0.91,
                finger_state=finger_state,
            )

        if finger_state.all_extended:
            return RecognizedGesture(
                gesture=GestureType.OPEN_PALM,
                confidence=0.90,
                finger_state=finger_state,
            )

        if finger_state.none_extended:
            return RecognizedGesture(
                gesture=GestureType.FIST,
                confidence=0.88,
                finger_state=finger_state,
            )

        if finger_state.is_only("index"):
            return RecognizedGesture(
                gesture=GestureType.INDEX_POINT,
                confidence=0.87,
                finger_state=finger_state,
            )

        if finger_state.is_only("index", "middle"):
            return RecognizedGesture(
                gesture=GestureType.PEACE,
                confidence=0.88,
                finger_state=finger_state,
            )

        if finger_state.is_only("index", "middle", "ring"):
            return RecognizedGesture(
                gesture=GestureType.THREE_FINGERS,
                confidence=0.86,
                finger_state=finger_state,
            )

        return RecognizedGesture.unknown(finger_state=finger_state)

    def _is_pinch(self, hand: HandLike) -> bool:
        distance = distance_between_indexes(
            landmarks=hand.landmarks,
            first_index=4,
            second_index=8,
        )

        return distance <= self.config.pinch_distance_threshold