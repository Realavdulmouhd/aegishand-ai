from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from aegishand.gestures.finger_state import FingerState


class GestureType(str, Enum):
    NO_HAND = "no_hand"
    UNKNOWN = "unknown"

    OPEN_PALM = "open_palm"
    FIST = "fist"
    INDEX_POINT = "index_point"
    PEACE = "peace"
    THREE_FINGERS = "three_fingers"
    PINCH = "pinch"

    TWO_HAND_ZOOM_IN = "two_hand_zoom_in"
    TWO_HAND_ZOOM_OUT = "two_hand_zoom_out"
    TWO_HAND_LOCK = "two_hand_lock"


@dataclass(frozen=True)
class RecognizedGesture:
    gesture: GestureType
    confidence: float
    finger_state: FingerState | None = None

    @property
    def label(self) -> str:
        return self.gesture.value

    @classmethod
    def no_hand(cls) -> RecognizedGesture:
        return cls(gesture=GestureType.NO_HAND, confidence=0.0)

    @classmethod
    def unknown(cls, finger_state: FingerState | None = None) -> RecognizedGesture:
        return cls(
            gesture=GestureType.UNKNOWN,
            confidence=0.20,
            finger_state=finger_state,
        )