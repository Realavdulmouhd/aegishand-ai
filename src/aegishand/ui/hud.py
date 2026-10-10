from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

from aegishand.vision.hand_tracker import HandTrackingResult
from aegishand.vision.landmark_utils import (
    HAND_CONNECTIONS,
    calculate_bounds,
    get_landmark,
    landmark_to_pixel,
)


@dataclass(frozen=True)
class HUDStatus:
    active_mode: str
    active_profile: str
    tracking_status: str
    gesture_label: str
    gesture_confidence: float
    action_name: str
    fps: float
    hand_count: int
    handedness: str
    desktop_control_enabled: bool
    safe_mode: bool
    cursor_position: tuple[int, int] | None
    warning: str
    diagnostics_enabled: bool


class ProfessionalHUD:
    def draw(
        self,
        frame: Any,
        result: HandTrackingResult,
        status: HUDStatus,
    ) -> Any:
        if cv2 is None:
            return frame

        self._draw_detected_hands(frame=frame, result=result)
        self._draw_cursor_target(frame=frame, status=status)
        self._draw_status_panel(frame=frame, status=status)
        self._draw_mode_hint(frame=frame, status=status)
        self._draw_footer(frame=frame)

        return frame

    def _draw_detected_hands(
        self,
        frame: Any,
        result: HandTrackingResult,
    ) -> None:
        for hand in result.hands:
            bounds = calculate_bounds(
                landmarks=hand.landmarks,
                frame_width=result.frame_width,
                frame_height=result.frame_height,
                padding=14,
            )

            if bounds:
                cv2.rectangle(
                    frame,
                    (bounds.left, bounds.top),
                    (bounds.right, bounds.bottom),
                    (80, 180, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    f"{hand.handedness} | {hand.confidence:.2f}",
                    (bounds.left, max(24, bounds.top - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.58,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

            for first_index, second_index in HAND_CONNECTIONS:
                first = get_landmark(hand.landmarks, first_index)
                second = get_landmark(hand.landmarks, second_index)

                first_point = landmark_to_pixel(
                    first,
                    result.frame_width,
                    result.frame_height,
                )

                second_point = landmark_to_pixel(
                    second,
                    result.frame_width,
                    result.frame_height,
                )

                cv2.line(
                    frame,
                    (first_point.x, first_point.y),
                    (second_point.x, second_point.y),
                    (70, 210, 140),
                    2,
                    cv2.LINE_AA,
                )

            for landmark in hand.landmarks:
                point = landmark_to_pixel(
                    landmark,
                    result.frame_width,
                    result.frame_height,
                )

                radius = 5 if landmark.index in (4, 8, 12, 16, 20) else 3

                cv2.circle(
                    frame,
                    (point.x, point.y),
                    radius,
                    (40, 220, 120),
                    -1,
                    cv2.LINE_AA,
                )

    def _draw_cursor_target(
        self,
        frame: Any,
        status: HUDStatus,
    ) -> None:
        if status.cursor_position is None:
            return

        x, y = status.cursor_position

        frame_height, frame_width = frame.shape[:2]

        preview_x = max(0, min(frame_width - 1, int(x)))
        preview_y = max(0, min(frame_height - 1, int(y)))

        cv2.circle(
            frame,
            (preview_x, preview_y),
            12,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        cv2.circle(
            frame,
            (preview_x, preview_y),
            4,
            (80, 220, 255),
            -1,
            cv2.LINE_AA,
        )

    def _draw_status_panel(
        self,
        frame: Any,
        status: HUDStatus,
    ) -> None:
        panel_left = 16
        panel_top = 16
        panel_right = 760
        panel_bottom = 320

        cv2.rectangle(
            frame,
            (panel_left, panel_top),
            (panel_right, panel_bottom),
            (20, 20, 20),
            -1,
        )

        cv2.rectangle(
            frame,
            (panel_left, panel_top),
            (panel_right, panel_bottom),
            (80, 180, 255),
            1,
        )

        self._put_text(
            frame,
            "AegisHand AI | Professional Control HUD",
            30,
            48,
            0.72,
            (255, 255, 255),
            2,
        )

        control_status = "ON" if status.desktop_control_enabled else "OFF"
        safe_mode = "ON" if status.safe_mode else "OFF"
        diagnostics = "ON" if status.diagnostics_enabled else "OFF"

        lines = [
            f"Profile: {status.active_profile} | Mode: {status.active_mode}",
            f"Tracking: {status.tracking_status} | Hands: {status.hand_count} | FPS: {status.fps:.1f}",
            f"Gesture: {status.gesture_label} | Confidence: {status.gesture_confidence:.2f}",
            f"Action: {status.action_name}",
            f"Handedness: {status.handedness}",
            f"Desktop control: {control_status} | Safe mode: {safe_mode} | Diagnostics: {diagnostics}",
        ]

        if status.cursor_position:
            x, y = status.cursor_position
            lines.append(f"Cursor target: x={x}, y={y}")
        else:
            lines.append("Cursor target: none")

        y = 82

        for line in lines:
            self._put_text(
                frame,
                line,
                30,
                y,
                0.54,
                (220, 220, 220),
                1,
            )
            y += 25

        warning_color = (
            (90, 220, 255)
            if status.desktop_control_enabled
            else (180, 180, 180)
        )

        self._put_text(
            frame,
            status.warning[:95],
            30,
            292,
            0.52,
            warning_color,
            1,
        )

    def _draw_mode_hint(
        self,
        frame: Any,
        status: HUDStatus,
    ) -> None:
        height, width = frame.shape[:2]

        mode = status.active_mode.strip().lower()

        hints = {
            "mouse": "Mouse mode: index move | peace click | three fingers right click | pinch drag | palm scroll",
            "scroll": "Scroll mode: open palm scroll | fist pause | two-hand lock emergency pause",
            "media": "Media mode: palm play/pause | peace next | three fingers previous | pinch mute",
            "volume": "Volume mode: index volume up | peace volume down | three fingers brightness up | palm brightness down",
            "presentation": "Presentation mode: index next | peace previous | palm start | three fingers blank | pinch unblank | two hands zoom",
            "drawing": "Drawing mode: index finger draws | open palm clears canvas | C clears canvas | fist pauses",
            "developer_demo": "Developer demo: safe mixed mode for showing architecture without aggressive control",
        }

        hint = hints.get(mode, "Mode hint unavailable.")

        box_left = 16
        box_right = width - 16
        box_top = height - 92
        box_bottom = height - 54

        cv2.rectangle(
            frame,
            (box_left, box_top),
            (box_right, box_bottom),
            (20, 20, 20),
            -1,
        )

        cv2.rectangle(
            frame,
            (box_left, box_top),
            (box_right, box_bottom),
            (80, 180, 255),
            1,
        )

        self._put_text(
            frame,
            hint[:140],
            30,
            height - 67,
            0.50,
            (220, 220, 220),
            1,
        )

    def _draw_footer(
        self,
        frame: Any,
    ) -> None:
        height, width = frame.shape[:2]

        footer = (
            "Q/ESC close | E emergency | P pause/resume | M cycle | "
            "1 mouse | 2 scroll | 3 media | 4 volume | 5 presentation | 6 drawing | 7 demo | C clear canvas"
        )

        cv2.rectangle(
            frame,
            (16, height - 46),
            (width - 16, height - 14),
            (20, 20, 20),
            -1,
        )

        self._put_text(
            frame,
            footer[:160],
            30,
            height - 24,
            0.46,
            (210, 210, 210),
            1,
        )

    @staticmethod
    def _put_text(
        frame: Any,
        text: str,
        x: int,
        y: int,
        scale: float,
        color: tuple[int, int, int],
        thickness: int,
    ) -> None:
        cv2.putText(
            frame,
            text,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness,
            cv2.LINE_AA,
        )