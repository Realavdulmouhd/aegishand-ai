from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Protocol


class RawLandmark(Protocol):
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class NormalizedLandmark:
    index: int
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class PixelPoint:
    x: int
    y: int


@dataclass(frozen=True)
class LandmarkBounds:
    left: int
    top: int
    right: int
    bottom: int


HAND_CONNECTIONS: tuple[tuple[int, int], ...] = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
)


def build_normalized_landmarks(raw_landmarks: Iterable[RawLandmark]) -> tuple[NormalizedLandmark, ...]:
    return tuple(
        NormalizedLandmark(
            index=index,
            x=float(landmark.x),
            y=float(landmark.y),
            z=float(landmark.z),
        )
        for index, landmark in enumerate(raw_landmarks)
    )


def get_landmark(landmarks: tuple[NormalizedLandmark, ...], index: int) -> NormalizedLandmark:
    if index < 0 or index >= len(landmarks):
        raise IndexError(f"Landmark index {index} is outside the available landmark range.")

    return landmarks[index]


def normalized_to_pixel(x: float, y: float, frame_width: int, frame_height: int) -> PixelPoint:
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("Frame width and height must be positive.")

    pixel_x = int(x * frame_width)
    pixel_y = int(y * frame_height)

    return PixelPoint(
        x=_clamp(pixel_x, 0, frame_width - 1),
        y=_clamp(pixel_y, 0, frame_height - 1),
    )


def landmark_to_pixel(
    landmark: NormalizedLandmark,
    frame_width: int,
    frame_height: int,
) -> PixelPoint:
    return normalized_to_pixel(
        x=landmark.x,
        y=landmark.y,
        frame_width=frame_width,
        frame_height=frame_height,
    )


def landmarks_to_pixels(
    landmarks: Iterable[NormalizedLandmark],
    frame_width: int,
    frame_height: int,
) -> tuple[PixelPoint, ...]:
    return tuple(
        landmark_to_pixel(
            landmark=landmark,
            frame_width=frame_width,
            frame_height=frame_height,
        )
        for landmark in landmarks
    )


def landmark_distance(first: NormalizedLandmark, second: NormalizedLandmark) -> float:
    return math.sqrt(
        ((first.x - second.x) ** 2)
        + ((first.y - second.y) ** 2)
        + ((first.z - second.z) ** 2)
    )


def distance_between_indexes(
    landmarks: tuple[NormalizedLandmark, ...],
    first_index: int,
    second_index: int,
) -> float:
    first = get_landmark(landmarks, first_index)
    second = get_landmark(landmarks, second_index)

    return landmark_distance(first, second)


def calculate_bounds(
    landmarks: Iterable[NormalizedLandmark],
    frame_width: int,
    frame_height: int,
    padding: int = 12,
) -> LandmarkBounds | None:
    points = landmarks_to_pixels(
        landmarks=landmarks,
        frame_width=frame_width,
        frame_height=frame_height,
    )

    if not points:
        return None

    left = min(point.x for point in points) - padding
    top = min(point.y for point in points) - padding
    right = max(point.x for point in points) + padding
    bottom = max(point.y for point in points) + padding

    return LandmarkBounds(
        left=_clamp(left, 0, frame_width - 1),
        top=_clamp(top, 0, frame_height - 1),
        right=_clamp(right, 0, frame_width - 1),
        bottom=_clamp(bottom, 0, frame_height - 1),
    )


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))