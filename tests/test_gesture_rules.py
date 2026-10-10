from __future__ import annotations

from dataclasses import dataclass

from aegishand.gestures.gesture_types import GestureType
from aegishand.gestures.rule_based_recognizer import RuleBasedGestureRecognizer
from aegishand.vision.landmark_utils import NormalizedLandmark


@dataclass(frozen=True)
class FakeHand:
    handedness: str
    confidence: float
    landmarks: tuple[NormalizedLandmark, ...]


def make_hand(
    *,
    thumb: bool,
    index: bool,
    middle: bool,
    ring: bool,
    pinky: bool,
    pinch: bool = False,
) -> FakeHand:
    landmarks = [
        NormalizedLandmark(index=i, x=0.5, y=0.6, z=0.0)
        for i in range(21)
    ]

    def set_finger(tip: int, pip: int, extended: bool) -> None:
        landmarks[pip] = NormalizedLandmark(index=pip, x=0.5, y=0.50, z=0.0)
        landmarks[tip] = NormalizedLandmark(
            index=tip,
            x=0.5,
            y=0.30 if extended else 0.62,
            z=0.0,
        )

    landmarks[3] = NormalizedLandmark(index=3, x=0.45, y=0.55, z=0.0)
    landmarks[4] = NormalizedLandmark(
        index=4,
        x=0.35 if thumb else 0.48,
        y=0.55,
        z=0.0,
    )

    set_finger(8, 6, index)
    set_finger(12, 10, middle)
    set_finger(16, 14, ring)
    set_finger(20, 18, pinky)

    if pinch:
        landmarks[4] = NormalizedLandmark(index=4, x=0.42, y=0.42, z=0.0)
        landmarks[8] = NormalizedLandmark(index=8, x=0.44, y=0.44, z=0.0)

    return FakeHand(
        handedness="Right",
        confidence=0.95,
        landmarks=tuple(landmarks),
    )


def test_recognizes_open_palm() -> None:
    hand = make_hand(
        thumb=True,
        index=True,
        middle=True,
        ring=True,
        pinky=True,
    )

    gesture = RuleBasedGestureRecognizer().recognize(hand)

    assert gesture.gesture == GestureType.OPEN_PALM


def test_recognizes_fist() -> None:
    hand = make_hand(
        thumb=False,
        index=False,
        middle=False,
        ring=False,
        pinky=False,
    )

    gesture = RuleBasedGestureRecognizer().recognize(hand)

    assert gesture.gesture == GestureType.FIST


def test_recognizes_index_point() -> None:
    hand = make_hand(
        thumb=False,
        index=True,
        middle=False,
        ring=False,
        pinky=False,
    )

    gesture = RuleBasedGestureRecognizer().recognize(hand)

    assert gesture.gesture == GestureType.INDEX_POINT


def test_recognizes_peace() -> None:
    hand = make_hand(
        thumb=False,
        index=True,
        middle=True,
        ring=False,
        pinky=False,
    )

    gesture = RuleBasedGestureRecognizer().recognize(hand)

    assert gesture.gesture == GestureType.PEACE


def test_recognizes_three_fingers() -> None:
    hand = make_hand(
        thumb=False,
        index=True,
        middle=True,
        ring=True,
        pinky=False,
    )

    gesture = RuleBasedGestureRecognizer().recognize(hand)

    assert gesture.gesture == GestureType.THREE_FINGERS


def test_recognizes_pinch() -> None:
    hand = make_hand(
        thumb=True,
        index=True,
        middle=False,
        ring=False,
        pinky=False,
        pinch=True,
    )

    gesture = RuleBasedGestureRecognizer().recognize(hand)

    assert gesture.gesture == GestureType.PINCH