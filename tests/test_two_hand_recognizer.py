from __future__ import annotations

from dataclasses import dataclass

from aegishand.gestures.gesture_types import GestureType
from aegishand.gestures.two_hand_recognizer import TwoHandGestureRecognizer
from aegishand.vision.landmark_utils import NormalizedLandmark


@dataclass
class FakeHand:
    handedness: str
    confidence: float
    landmarks: tuple[NormalizedLandmark, ...]


def make_hand(wrist_x: float, *, fist: bool = False) -> FakeHand:
    landmarks = [
        NormalizedLandmark(index=i, x=wrist_x, y=0.5, z=0.0)
        for i in range(21)
    ]

    landmarks[0] = NormalizedLandmark(index=0, x=wrist_x, y=0.5, z=0.0)

    if fist:
        finger_tip_y = 0.62
    else:
        finger_tip_y = 0.30

    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        landmarks[pip] = NormalizedLandmark(index=pip, x=wrist_x, y=0.50, z=0.0)
        landmarks[tip] = NormalizedLandmark(index=tip, x=wrist_x, y=finger_tip_y, z=0.0)

    landmarks[3] = NormalizedLandmark(index=3, x=wrist_x + 0.03, y=0.5, z=0.0)
    landmarks[4] = NormalizedLandmark(
        index=4,
        x=wrist_x + 0.08 if not fist else wrist_x + 0.01,
        y=0.5,
        z=0.0,
    )

    return FakeHand(
        handedness="Left",
        confidence=0.95,
        landmarks=tuple(landmarks),
    )


def test_two_fists_create_lock_gesture() -> None:
    recognizer = TwoHandGestureRecognizer()

    gesture = recognizer.recognize(
        (
            make_hand(0.30, fist=True),
            make_hand(0.70, fist=True),
        )
    )

    assert gesture is not None
    assert gesture.gesture == GestureType.TWO_HAND_LOCK


def test_hands_moving_apart_create_zoom_in() -> None:
    recognizer = TwoHandGestureRecognizer()

    recognizer.recognize(
        (
            make_hand(0.42),
            make_hand(0.58),
        )
    )

    gesture = recognizer.recognize(
        (
            make_hand(0.25),
            make_hand(0.75),
        )
    )

    assert gesture is not None
    assert gesture.gesture == GestureType.TWO_HAND_ZOOM_IN


def test_hands_moving_closer_create_zoom_out() -> None:
    recognizer = TwoHandGestureRecognizer()

    recognizer.recognize(
        (
            make_hand(0.20),
            make_hand(0.80),
        )
    )

    gesture = recognizer.recognize(
        (
            make_hand(0.42),
            make_hand(0.58),
        )
    )

    assert gesture is not None
    assert gesture.gesture == GestureType.TWO_HAND_ZOOM_OUT