from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from logging import Logger
from typing import Any

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None


class CameraStreamError(RuntimeError):
    """Raised when the webcam cannot be opened or read safely."""


@dataclass(frozen=True)
class CameraStreamConfig:
    index: int
    width: int
    height: int
    fps_limit: int

    def validate(self) -> None:
        if self.index < 0:
            raise CameraStreamError("Camera index cannot be negative.")

        if self.width < 320 or self.height < 240:
            raise CameraStreamError("Camera resolution is too small for reliable tracking.")

        if self.fps_limit < 1:
            raise CameraStreamError("FPS limit must be at least 1.")


@dataclass(frozen=True)
class CameraFrame:
    image: Any
    timestamp: float
    fps: float
    width: int
    height: int


class CameraStream:
    def __init__(self, config: CameraStreamConfig, logger: Logger | None = None) -> None:
        self.config = config
        self.logger = logger
        self._capture: Any | None = None
        self._last_frame_time: float | None = None
        self._smoothed_fps = 0.0

    def open(self) -> None:
        self.config.validate()

        if cv2 is None:
            raise CameraStreamError(
                "OpenCV is not installed. Run: pip install -r requirements.txt"
            )

        backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
        self._capture = cv2.VideoCapture(self.config.index, backend)

        if not self._capture.isOpened():
            self._capture.release()
            self._capture = None
            raise CameraStreamError(
                f"Could not open camera index {self.config.index}. "
                "Check camera permission or try another camera index."
            )

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self._capture.set(cv2.CAP_PROP_FPS, self.config.fps_limit)

        if self.logger:
            self.logger.info("Camera opened at index %s", self.config.index)

    def read(self) -> CameraFrame | None:
        if self._capture is None or not self._capture.isOpened():
            raise CameraStreamError("Camera is not open. Call open() before read().")

        success, image = self._capture.read()

        if not success or image is None:
            return None

        timestamp = time.perf_counter()
        fps = self._calculate_fps(timestamp)
        height, width = image.shape[:2]

        return CameraFrame(
            image=image,
            timestamp=timestamp,
            fps=fps,
            width=width,
            height=height,
        )

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

        if cv2 is not None:
            cv2.destroyAllWindows()

        if self.logger:
            self.logger.info("Camera released")

    def is_open(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def _calculate_fps(self, current_time: float) -> float:
        if self._last_frame_time is None:
            self._last_frame_time = current_time
            return 0.0

        elapsed = current_time - self._last_frame_time
        self._last_frame_time = current_time

        if elapsed <= 0:
            return self._smoothed_fps

        instant_fps = 1.0 / elapsed

        if self._smoothed_fps == 0.0:
            self._smoothed_fps = instant_fps
        else:
            self._smoothed_fps = (self._smoothed_fps * 0.90) + (instant_fps * 0.10)

        return self._smoothed_fps

    def __enter__(self) -> CameraStream:
        self.open()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.release()


def draw_camera_status(frame: Any, camera_index: int, fps: float) -> Any:
    if cv2 is None:
        return frame

    cv2.rectangle(frame, (16, 16), (430, 124), (25, 25, 25), -1)
    cv2.putText(
        frame,
        "AegisHand AI | Camera Preview",
        (30, 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"Camera: {camera_index} | FPS: {fps:.1f}",
        (30, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (220, 220, 220),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "Press Q or ESC to close",
        (30, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (180, 180, 180),
        1,
        cv2.LINE_AA,
    )

    return frame


def run_camera_preview(config: CameraStreamConfig, logger: Logger | None = None) -> None:
    if cv2 is None:
        raise CameraStreamError("OpenCV is not installed. Run: pip install -r requirements.txt")

    window_title = "AegisHand AI Camera Preview"

    with CameraStream(config=config, logger=logger) as camera:
        while True:
            camera_frame = camera.read()

            if camera_frame is None:
                if logger:
                    logger.warning("Camera returned an empty frame")
                continue

            preview = draw_camera_status(
                frame=camera_frame.image,
                camera_index=config.index,
                fps=camera_frame.fps,
            )

            cv2.imshow(window_title, preview)

            key = cv2.waitKey(1) & 0xFF

            if key in (27, ord("q")):
                break