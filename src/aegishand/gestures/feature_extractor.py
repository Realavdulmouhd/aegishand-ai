from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Iterable, Protocol

import numpy as np

from aegishand.vision.landmark_utils import NormalizedLandmark


class FeatureExtractionError(RuntimeError):
    """Raised when hand landmark features cannot be extracted safely."""


class HandLike(Protocol):
    handedness: str
    confidence: float
    landmarks: tuple[NormalizedLandmark, ...]


@dataclass(frozen=True)
class HandFeatureVector:
    values: tuple[float, ...]
    names: tuple[str, ...]

    @property
    def size(self) -> int:
        return len(self.values)

    def as_tuple(self) -> tuple[float, ...]:
        return self.values

    def as_list(self) -> list[float]:
        return list(self.values)

    def as_numpy(self) -> np.ndarray:
        return np.array(self.values, dtype=float)

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self):
        return iter(self.values)


class HandFeatureExtractor:
    """
    Converts 21 hand landmarks into a compact 68-value feature vector.

    Feature layout:
    - 63 normalized landmark values
      21 landmarks × x, y, z
    - 4 fingertip distance values
      thumb-to-index, thumb-to-middle, thumb-to-ring, thumb-to-pinky
    - 1 handedness value
      right = 1.0, left = -1.0, unknown = 0.0

    This stores no raw camera frame and no biometric image.
    """

    def __init__(self) -> None:
        self._feature_names = self._build_feature_names()

    @property
    def feature_names(self) -> tuple[str, ...]:
        return self._feature_names

    def extract(
        self,
        hand_or_landmarks: HandLike | Iterable[NormalizedLandmark],
    ) -> HandFeatureVector:
        landmarks = self._extract_landmarks(hand_or_landmarks)
        handedness = self._extract_handedness(hand_or_landmarks)

        wrist = landmarks[0]
        middle_mcp = landmarks[9]

        scale = _distance(wrist, middle_mcp)

        if scale <= 0:
            scale = self._fallback_scale(landmarks)

        if scale <= 0:
            raise FeatureExtractionError(
                "Cannot normalize landmarks because hand scale is zero."
            )

        values: list[float] = []

        for landmark in landmarks:
            values.append((landmark.x - wrist.x) / scale)
            values.append((landmark.y - wrist.y) / scale)
            values.append((landmark.z - wrist.z) / scale)

        distance_pairs = (
            (4, 8),
            (4, 12),
            (4, 16),
            (4, 20),
        )

        for first, second in distance_pairs:
            values.append(_distance(landmarks[first], landmarks[second]) / scale)

        values.append(self._handedness_value(handedness))

        if len(values) != 68:
            raise FeatureExtractionError(
                f"Feature extractor produced {len(values)} values instead of 68."
            )

        return HandFeatureVector(
            values=tuple(values),
            names=self.feature_names,
        )

    def extract_many(
        self,
        hands: Iterable[HandLike | Iterable[NormalizedLandmark]],
    ) -> list[HandFeatureVector]:
        return [self.extract(hand) for hand in hands]

    def feature_count(self) -> int:
        return len(self.feature_names)

    def _extract_landmarks(
        self,
        hand_or_landmarks: HandLike | Iterable[NormalizedLandmark],
    ) -> tuple[NormalizedLandmark, ...]:
        if hasattr(hand_or_landmarks, "landmarks"):
            raw_landmarks = getattr(hand_or_landmarks, "landmarks")
        else:
            raw_landmarks = hand_or_landmarks

        try:
            landmarks = tuple(raw_landmarks)
        except TypeError as exc:
            raise FeatureExtractionError(
                "Expected a hand object or an iterable of landmarks."
            ) from exc

        if len(landmarks) != 21:
            raise FeatureExtractionError(
                f"Expected 21 hand landmarks, received {len(landmarks)}."
            )

        for index, landmark in enumerate(landmarks):
            if not all(hasattr(landmark, attribute) for attribute in ("x", "y", "z")):
                raise FeatureExtractionError(
                    f"Landmark at index {index} is missing x, y, or z."
                )

        return landmarks

    def _extract_handedness(self, hand_or_landmarks: Any) -> str:
        return str(getattr(hand_or_landmarks, "handedness", "unknown"))

    def _fallback_scale(
        self,
        landmarks: tuple[NormalizedLandmark, ...],
    ) -> float:
        wrist = landmarks[0]
        candidates = (5, 9, 13, 17, 8, 12, 16, 20)

        return max(
            _distance(wrist, landmarks[index])
            for index in candidates
        )

    def _handedness_value(self, handedness: str) -> float:
        normalized = handedness.strip().lower()

        if normalized == "right":
            return 1.0

        if normalized == "left":
            return -1.0

        return 0.0

    def _build_feature_names(self) -> tuple[str, ...]:
        names: list[str] = []

        for index in range(21):
            names.append(f"landmark_{index}_relative_x")
            names.append(f"landmark_{index}_relative_y")
            names.append(f"landmark_{index}_relative_z")

        names.extend(
            [
                "distance_thumb_index",
                "distance_thumb_middle",
                "distance_thumb_ring",
                "distance_thumb_pinky",
                "handedness",
            ]
        )

        return tuple(names)


def _distance(first: NormalizedLandmark, second: NormalizedLandmark) -> float:
    return sqrt(
        ((first.x - second.x) ** 2)
        + ((first.y - second.y) ** 2)
        + ((first.z - second.z) ** 2)
    )