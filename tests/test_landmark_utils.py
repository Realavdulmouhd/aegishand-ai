from dataclasses import dataclass

import pytest

from aegishand.vision.landmark_utils import (
    build_normalized_landmarks,
    calculate_bounds,
    landmark_to_pixel,
    normalized_to_pixel,
)


@dataclass(frozen=True)
class FakeRawLandmark:
    x: float
    y: float
    z: float


def test_normalized_to_pixel_converts_coordinates() -> None:
    point = normalized_to_pixel(
        x=0.50,
        y=0.25,
        frame_width=1280,
        frame_height=720,
    )

    assert point.x == 640
    assert point.y == 180


def test_normalized_to_pixel_clamps_out_of_range_values() -> None:
    point = normalized_to_pixel(
        x=1.50,
        y=-0.20,
        frame_width=1280,
        frame_height=720,
    )

    assert point.x == 1279
    assert point.y == 0


def test_normalized_to_pixel_rejects_invalid_frame_size() -> None:
    with pytest.raises(ValueError):
        normalized_to_pixel(
            x=0.50,
            y=0.50,
            frame_width=0,
            frame_height=720,
        )


def test_build_normalized_landmarks_keeps_indexes() -> None:
    raw_landmarks = [
        FakeRawLandmark(x=0.1, y=0.2, z=0.0),
        FakeRawLandmark(x=0.3, y=0.4, z=-0.1),
    ]

    landmarks = build_normalized_landmarks(raw_landmarks)

    assert len(landmarks) == 2
    assert landmarks[0].index == 0
    assert landmarks[1].index == 1


def test_landmark_to_pixel_uses_frame_size() -> None:
    raw_landmarks = [FakeRawLandmark(x=0.25, y=0.50, z=0.0)]
    landmark = build_normalized_landmarks(raw_landmarks)[0]

    point = landmark_to_pixel(
        landmark=landmark,
        frame_width=800,
        frame_height=600,
    )

    assert point.x == 200
    assert point.y == 300


def test_calculate_bounds_returns_box_with_padding() -> None:
    raw_landmarks = [
        FakeRawLandmark(x=0.25, y=0.25, z=0.0),
        FakeRawLandmark(x=0.75, y=0.75, z=0.0),
    ]

    landmarks = build_normalized_landmarks(raw_landmarks)

    bounds = calculate_bounds(
        landmarks=landmarks,
        frame_width=800,
        frame_height=600,
        padding=10,
    )

    assert bounds is not None
    assert bounds.left == 190
    assert bounds.top == 140
    assert bounds.right == 610
    assert bounds.bottom == 460