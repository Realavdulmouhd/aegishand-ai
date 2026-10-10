from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from aegishand.vision.landmark_utils import NormalizedLandmark, get_landmark


class HandLike(Protocol):
    handedness: str
    landmarks: tuple[NormalizedLandmark, ...]


@dataclass(frozen=True)
class FingerState:
    thumb: bool
    index: bool
    middle: bool
    ring: bool
    pinky: bool

    @property
    def extended_count(self) -> int:
        return sum((self.thumb, self.index, self.middle, self.ring, self.pinky))

    @property
    def all_extended(self) -> bool:
        return self.extended_count == 5

    @property
    def none_extended(self) -> bool:
        return self.extended_count == 0

    def is_only(self, *finger_names: str) -> bool:
        expected = set(finger_names)
        states = {
            "thumb": self.thumb,
            "index": self.index,
            "middle": self.middle,
            "ring": self.ring,
            "pinky": self.pinky,
        }

        return all(is_extended == (name in expected) for name, is_extended in states.items())


class FingerStateDetector:
    def __init__(self, vertical_margin: float = 0.025, thumb_margin: float = 0.030) -> None:
        self.vertical_margin = vertical_margin
        self.thumb_margin = thumb_margin

    def detect(self, hand: HandLike) -> FingerState:
        landmarks = hand.landmarks

        thumb = self._is_thumb_extended(hand)
        index = self._is_finger_extended(landmarks, tip_index=8, pip_index=6)
        middle = self._is_finger_extended(landmarks, tip_index=12, pip_index=10)
        ring = self._is_finger_extended(landmarks, tip_index=16, pip_index=14)
        pinky = self._is_finger_extended(landmarks, tip_index=20, pip_index=18)

        return FingerState(
            thumb=thumb,
            index=index,
            middle=middle,
            ring=ring,
            pinky=pinky,
        )

    def _is_finger_extended(
        self,
        landmarks: tuple[NormalizedLandmark, ...],
        tip_index: int,
        pip_index: int,
    ) -> bool:
        tip = get_landmark(landmarks, tip_index)
        pip = get_landmark(landmarks, pip_index)

        return tip.y < pip.y - self.vertical_margin

    def _is_thumb_extended(self, hand: HandLike) -> bool:
        thumb_tip = get_landmark(hand.landmarks, 4)
        thumb_ip = get_landmark(hand.landmarks, 3)

        handedness = hand.handedness.strip().lower()

        if handedness == "left":
            return thumb_tip.x > thumb_ip.x + self.thumb_margin

        return thumb_tip.x < thumb_ip.x - self.thumb_margin