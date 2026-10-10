from time import sleep

from aegishand.core.events import GestureCandidate
from aegishand.core.types import Handedness
from aegishand.gestures.gesture_stabilizer import (
    GestureStabilizer,
)


def test_stable_gesture_detection() -> None:
    stabilizer = GestureStabilizer(
        confidence_threshold=0.75,
        required_consistent_frames=3,
        required_hold_ms=100,
    )

    result = None

    for _ in range(3):
        candidate = GestureCandidate(
            name="pinch",
            confidence=0.90,
            handedness=Handedness.RIGHT,
            duration_ms=150,
        )

        sleep(0.05)

        result = stabilizer.update(candidate)

    sleep(0.12)

    result = stabilizer.update(candidate)

    assert result is not None
    assert result.name == "pinch"