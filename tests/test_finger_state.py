from __future__ import annotations

from dataclasses import dataclass

from aegishand.gestures.finger_state import FingerStateDetector
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
    handedness: str = "Right",
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

    return FakeHand(
        handedness=handedness,
        confidence=0.95,
        landmarks=tuple(landmarks),
    )


def test_detects_open_palm() -> None:
    hand = make_hand(
        thumb=True,
        index=True,
        middle=True,
        ring=True,
        pinky=True,
    )

    state = FingerStateDetector().detect(hand)

    assert state.all_extended is True
    assert state.extended_count == 5


def test_detects_fist() -> None:
    hand = make_hand(
        thumb=False,
        index=False,
        middle=False,
        ring=False,
        pinky=False,
    )

    state = FingerStateDetector().detect(hand)

    assert state.none_extended is True


def test_detects_index_only() -> None:
    hand = make_hand(
        thumb=False,
        index=True,
        middle=False,
        ring=False,
        pinky=False,
    )

    state = FingerStateDetector().detect(hand)

    assert state.is_only("index") is True