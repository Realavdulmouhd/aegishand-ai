from __future__ import annotations

import time
from dataclasses import dataclass
from logging import Logger
from typing import Any

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

try:
    import mediapipe as mp
except ImportError:  # pragma: no cover
    mp = None

from aegishand.camera.camera_stream import CameraStream, CameraStreamConfig
from aegishand.vision.landmark_utils import (
    NormalizedLandmark,
    build_normalized_landmarks,
    calculate_bounds,
)


class HandTrackerError(RuntimeError):
    """Raised when MediaPipe hand tracking cannot run safely."""


@dataclass(frozen=True)
class HandTrackerConfig:
    max_hands: int
    min_detection_confidence: float
    min_tracking_confidence: float
    model_complexity: int = 1

    def validate(self) -> None:
        if self.max_hands < 1 or self.max_hands > 2:
            raise HandTrackerError("AegisHand AI currently supports one or two hands.")

        if not 0.0 <= self.min_detection_confidence <= 1.0:
            raise HandTrackerError("Detection confidence must be between 0.0 and 1.0.")

        if not 0.0 <= self.min_tracking_confidence <= 1.0:
            raise HandTrackerError("Tracking confidence must be between 0.0 and 1.0.")

        if self.model_complexity not in (0, 1):
            raise HandTrackerError("Model complexity must be 0 or 1.")


@dataclass(frozen=True)
class DetectedHand:
    handedness: str
    confidence: float
    landmarks: tuple[NormalizedLandmark, ...]

    @property
    def landmark_count(self) -> int:
        return len(self.landmarks)


@dataclass(frozen=True)
class HandTrackingResult:
    hands: tuple[DetectedHand, ...]
    frame_width: int
    frame_height: int
    timestamp: float

    @property
    def has_hands(self) -> bool:
        return len(self.hands) > 0

    @property
    def hand_count(self) -> int:
        return len(self.hands)


class MediaPipeHandTracker:
    def __init__(self, config: HandTrackerConfig, logger: Logger | None = None) -> None:
        self.config = config
        self.logger = logger
        self._hands: Any | None = None
        self._mp_hands: Any | None = None
        self._drawing_utils: Any | None = None
        self._drawing_styles: Any | None = None

    def open(self) -> None:
        self.config.validate()

        if cv2 is None:
            raise HandTrackerError("OpenCV is not installed. Run: pip install -r requirements.txt")

        if mp is None:
            raise HandTrackerError("MediaPipe is not installed. Run: pip install -r requirements.txt")

        self._mp_hands = mp.solutions.hands
        self._drawing_utils = mp.solutions.drawing_utils
        self._drawing_styles = mp.solutions.drawing_styles

        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.config.max_hands,
            model_complexity=self.config.model_complexity,
            min_detection_confidence=self.config.min_detection_confidence,
            min_tracking_confidence=self.config.min_tracking_confidence,
        )

        if self.logger:
            self.logger.info("MediaPipe hand tracker opened")

    def process_frame(self, frame_bgr: Any) -> HandTrackingResult:
        if self._hands is None:
            raise HandTrackerError("Hand tracker is not open. Call open() before processing frames.")

        frame_height, frame_width = frame_bgr.shape[:2]

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False

        raw_result = self._hands.process(frame_rgb)

        hands = self._extract_hands(raw_result)

        return HandTrackingResult(
            hands=hands,
            frame_width=frame_width,
            frame_height=frame_height,
            timestamp=time.perf_counter(),
        )

    def draw_landmarks(self, frame_bgr: Any, result: HandTrackingResult) -> Any:
        if self._mp_hands is None or self._drawing_utils is None:
            return frame_bgr

        if not result.has_hands:
            return frame_bgr

        for hand in result.hands:
            bounds = calculate_bounds(
                landmarks=hand.landmarks,
                frame_width=result.frame_width,
                frame_height=result.frame_height,
            )

            if bounds:
                cv2.rectangle(
                    frame_bgr,
                    (bounds.left, bounds.top),
                    (bounds.right, bounds.bottom),
                    (80, 180, 255),
                    2,
                )

            for landmark in hand.landmarks:
                pixel_x = int(landmark.x * result.frame_width)
                pixel_y = int(landmark.y * result.frame_height)
                cv2.circle(frame_bgr, (pixel_x, pixel_y), 3, (40, 220, 120), -1)

            label = f"{hand.handedness} | {hand.confidence:.2f} | {hand.landmark_count} points"

            if bounds:
                cv2.putText(
                    frame_bgr,
                    label,
                    (bounds.left, max(24, bounds.top - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

        return frame_bgr

    def close(self) -> None:
        if self._hands is not None:
            self._hands.close()
            self._hands = None

        if self.logger:
            self.logger.info("MediaPipe hand tracker closed")

    def _extract_hands(self, raw_result: Any) -> tuple[DetectedHand, ...]:
        if not raw_result.multi_hand_landmarks:
            return tuple()

        detected_hands: list[DetectedHand] = []

        for index, hand_landmarks in enumerate(raw_result.multi_hand_landmarks):
            handedness = "Unknown"
            confidence = 0.0

            if raw_result.multi_handedness and index < len(raw_result.multi_handedness):
                classification = raw_result.multi_handedness[index].classification[0]
                handedness = classification.label
                confidence = float(classification.score)

            detected_hands.append(
                DetectedHand(
                    handedness=handedness,
                    confidence=confidence,
                    landmarks=build_normalized_landmarks(hand_landmarks.landmark),
                )
            )

        return tuple(detected_hands)

    def __enter__(self) -> MediaPipeHandTracker:
        self.open()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()


def draw_tracking_status(frame: Any, result: HandTrackingResult, fps: float) -> Any:
    if cv2 is None:
        return frame

    cv2.rectangle(frame, (16, 16), (500, 138), (25, 25, 25), -1)

    cv2.putText(
        frame,
        "AegisHand AI | MediaPipe Hand Tracking",
        (30, 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.67,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    tracking_status = "Tracking" if result.has_hands else "No hand detected"

    cv2.putText(
        frame,
        f"Status: {tracking_status} | Hands: {result.hand_count} | FPS: {fps:.1f}",
        (30, 82),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (220, 220, 220),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        "Desktop control: OFF | Press Q or ESC to close",
        (30, 116),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (180, 180, 180),
        1,
        cv2.LINE_AA,
    )

    return frame


def run_hand_tracking_preview(
    camera_config: CameraStreamConfig,
    tracker_config: HandTrackerConfig,
    logger: Logger | None = None,
) -> None:
    if cv2 is None:
        raise HandTrackerError("OpenCV is not installed. Run: pip install -r requirements.txt")

    window_title = "AegisHand AI Hand Tracking"

    with CameraStream(config=camera_config, logger=logger) as camera:
        with MediaPipeHandTracker(config=tracker_config, logger=logger) as tracker:
            while True:
                camera_frame = camera.read()

                if camera_frame is None:
                    if logger:
                        logger.warning("Camera returned an empty frame")
                    continue

                result = tracker.process_frame(camera_frame.image)
                preview = tracker.draw_landmarks(camera_frame.image, result)
                preview = draw_tracking_status(preview, result, camera_frame.fps)

                cv2.imshow(window_title, preview)

                key = cv2.waitKey(1) & 0xFF

                if key in (27, ord("q")):
                    break