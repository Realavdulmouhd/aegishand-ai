from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

from aegishand.vision.landmark_utils import NormalizedLandmark, landmark_to_pixel


@dataclass(frozen=True)
class AirCanvasConfig:
    brush_radius: int = 6
    min_draw_distance: int = 8
    overlay_opacity: float = 0.85

    def validate(self) -> None:
        if self.brush_radius < 1 or self.brush_radius > 40:
            raise ValueError("Brush radius must be between 1 and 40.")

        if self.min_draw_distance < 0:
            raise ValueError("Minimum draw distance cannot be negative.")

        if not 0.0 <= self.overlay_opacity <= 1.0:
            raise ValueError("Overlay opacity must be between 0.0 and 1.0.")


@dataclass(frozen=True)
class DrawingStatus:
    active: bool
    point_count: int
    message: str


class AirCanvas:
    def __init__(self, config: AirCanvasConfig | None = None) -> None:
        self.config = config or AirCanvasConfig()
        self.config.validate()

        self._canvas: Any | None = None
        self._last_point: tuple[int, int] | None = None
        self._point_count = 0

    def ensure_size(self, frame_width: int, frame_height: int) -> None:
        if self._canvas is not None:
            height, width = self._canvas.shape[:2]
            if width == frame_width and height == frame_height:
                return

        self._canvas = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)
        self._last_point = None
        self._point_count = 0

    def draw_point(
        self,
        landmark: NormalizedLandmark,
        frame_width: int,
        frame_height: int,
    ) -> DrawingStatus:
        if cv2 is None:
            return DrawingStatus(False, self._point_count, "OpenCV is not available.")

        self.ensure_size(frame_width=frame_width, frame_height=frame_height)

        point = landmark_to_pixel(
            landmark=landmark,
            frame_width=frame_width,
            frame_height=frame_height,
        )

        current = (point.x, point.y)

        if self._last_point is None:
            self._last_point = current
            self._point_count += 1
            cv2.circle(self._canvas, current, self.config.brush_radius, (80, 220, 255), -1)
            return DrawingStatus(True, self._point_count, "Drawing started.")

        if _distance(current, self._last_point) < self.config.min_draw_distance:
            return DrawingStatus(True, self._point_count, "Drawing point held.")

        cv2.line(
            self._canvas,
            self._last_point,
            current,
            (80, 220, 255),
            self.config.brush_radius,
            cv2.LINE_AA,
        )

        self._last_point = current
        self._point_count += 1

        return DrawingStatus(True, self._point_count, "Drawing.")

    def lift_pen(self) -> None:
        self._last_point = None

    def clear(self) -> DrawingStatus:
        if self._canvas is not None:
            self._canvas[:] = 0

        self._last_point = None
        self._point_count = 0

        return DrawingStatus(False, self._point_count, "Canvas cleared.")

    def overlay(self, frame: Any) -> Any:
        if cv2 is None or self._canvas is None:
            return frame

        return cv2.addWeighted(
            frame,
            1.0,
            self._canvas,
            self.config.overlay_opacity,
            0,
        )


def _distance(first: tuple[int, int], second: tuple[int, int]) -> float:
    return sqrt(((first[0] - second[0]) ** 2) + ((first[1] - second[1]) ** 2))