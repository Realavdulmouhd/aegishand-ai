from __future__ import annotations

from logging import Logger

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

from aegishand.camera.camera_stream import CameraStream, CameraStreamConfig
from aegishand.control.action_dispatcher import ActionDispatcher, ActionDispatchResult
from aegishand.control.mouse_controller import MouseController
from aegishand.control.system_controller import SystemController
from aegishand.diagnostics.event_logger import DiagnosticEventLogger
from aegishand.drawing.air_canvas import AirCanvas
from aegishand.gestures.gesture_types import RecognizedGesture
from aegishand.gestures.rule_based_recognizer import RuleBasedGestureRecognizer
from aegishand.gestures.two_hand_recognizer import TwoHandGestureRecognizer
from aegishand.modes.mode_manager import ModeManager
from aegishand.profiles.profile_manager import ProfileManager
from aegishand.safety.cooldown import CooldownManager
from aegishand.safety.safety_manager import SafetyManager
from aegishand.ui.hud import HUDStatus, ProfessionalHUD
from aegishand.vision.hand_tracker import HandTrackerConfig, HandTrackerError, MediaPipeHandTracker
from aegishand.vision.landmark_utils import get_landmark


def run_gesture_runtime(
    camera_config: CameraStreamConfig,
    tracker_config: HandTrackerConfig,
    mode_manager: ModeManager,
    profile_manager: ProfileManager,
    safety_manager: SafetyManager,
    cooldown_manager: CooldownManager,
    recognizer: RuleBasedGestureRecognizer,
    two_hand_recognizer: TwoHandGestureRecognizer,
    hud: ProfessionalHUD,
    mouse_controller: MouseController | None = None,
    system_controller: SystemController | None = None,
    air_canvas: AirCanvas | None = None,
    event_logger: DiagnosticEventLogger | None = None,
    logger: Logger | None = None,
) -> None:
    if cv2 is None:
        raise HandTrackerError("OpenCV is not installed. Run: pip install -r requirements.txt")

    window_title = "AegisHand AI Gesture Runtime"

    dispatcher = ActionDispatcher(
        mode_manager=mode_manager,
        profile_manager=profile_manager,
        safety_manager=safety_manager,
        cooldown_manager=cooldown_manager,
        mouse_controller=mouse_controller,
        system_controller=system_controller,
    )

    if event_logger:
        event_logger.log(
            "runtime_started",
            "Gesture runtime started.",
            profile=profile_manager.active_profile_name,
            mode=mode_manager.get_mode().value,
        )

    with CameraStream(config=camera_config, logger=logger) as camera:
        with MediaPipeHandTracker(config=tracker_config, logger=logger) as tracker:
            while True:
                camera_frame = camera.read()

                if camera_frame is None:
                    if logger:
                        logger.warning("Camera returned an empty frame")
                    continue

                result = tracker.process_frame(camera_frame.image)
                primary_hand = result.hands[0] if result.has_hands else None

                gesture = _recognize_best_gesture(
                    hands=result.hands,
                    primary_hand=primary_hand,
                    recognizer=recognizer,
                    two_hand_recognizer=two_hand_recognizer,
                )

                dispatch_result = dispatcher.dispatch(
                    gesture=gesture,
                    hand=primary_hand,
                )

                if event_logger and dispatch_result.action_name != "none":
                    event_logger.log(
                        "action_dispatch",
                        dispatch_result.message,
                        gesture=gesture.label,
                        action=dispatch_result.action_name,
                        executed=dispatch_result.executed,
                        mode=mode_manager.get_mode().value,
                        profile=profile_manager.active_profile_name,
                    )

                preview_frame = camera_frame.image

                if air_canvas is not None:
                    drawing_message = _handle_air_drawing(
                        air_canvas=air_canvas,
                        dispatch_result=dispatch_result,
                        primary_hand=primary_hand,
                        frame_width=result.frame_width,
                        frame_height=result.frame_height,
                    )

                    if drawing_message and event_logger:
                        event_logger.log(
                            "drawing",
                            drawing_message,
                            mode=mode_manager.get_mode().value,
                        )

                    preview_frame = air_canvas.overlay(preview_frame)

                status = _build_hud_status(
                    gesture_label=gesture.label,
                    gesture_confidence=gesture.confidence,
                    result_hand_count=result.hand_count,
                    primary_handedness=primary_hand.handedness if primary_hand else "none",
                    fps=camera_frame.fps,
                    mode_manager=mode_manager,
                    profile_manager=profile_manager,
                    safety_manager=safety_manager,
                    dispatch_result=dispatch_result,
                    mouse_controller=mouse_controller,
                    system_controller=system_controller,
                    event_logger=event_logger,
                )

                preview = hud.draw(
                    frame=preview_frame,
                    result=result,
                    status=status,
                )

                cv2.imshow(window_title, preview)

                key = cv2.waitKey(1) & 0xFF

                should_close = _handle_keyboard_control(
                    key=key,
                    mode_manager=mode_manager,
                    safety_manager=safety_manager,
                    mouse_controller=mouse_controller,
                    air_canvas=air_canvas,
                    event_logger=event_logger,
                    logger=logger,
                )

                if should_close:
                    break

    if mouse_controller is not None and mouse_controller.drag_active:
        mouse_controller.end_drag()

    if event_logger:
        event_logger.log("runtime_closed", "Gesture runtime closed.")


def _recognize_best_gesture(
    hands: tuple[object, ...],
    primary_hand: object | None,
    recognizer: RuleBasedGestureRecognizer,
    two_hand_recognizer: TwoHandGestureRecognizer,
) -> RecognizedGesture:
    two_hand_gesture = two_hand_recognizer.recognize(hands)

    if two_hand_gesture is not None:
        return two_hand_gesture

    return recognizer.recognize(primary_hand)


def _handle_air_drawing(
    air_canvas: AirCanvas,
    dispatch_result: ActionDispatchResult,
    primary_hand: object | None,
    frame_width: int,
    frame_height: int,
) -> str | None:
    if dispatch_result.action_name == "clear_canvas":
        return air_canvas.clear().message

    if dispatch_result.action_name != "draw_air":
        air_canvas.lift_pen()
        return None

    if primary_hand is None:
        air_canvas.lift_pen()
        return None

    index_tip = get_landmark(primary_hand.landmarks, 8)
    drawing_status = air_canvas.draw_point(
        landmark=index_tip,
        frame_width=frame_width,
        frame_height=frame_height,
    )

    return drawing_status.message


def _handle_keyboard_control(
    key: int,
    mode_manager: ModeManager,
    safety_manager: SafetyManager,
    mouse_controller: MouseController | None,
    air_canvas: AirCanvas | None,
    event_logger: DiagnosticEventLogger | None,
    logger: Logger | None,
) -> bool:
    if key in (27, ord("q")):
        return True

    if key == ord("e"):
        safety_manager.trigger_emergency_stop()

        if mouse_controller is not None and mouse_controller.drag_active:
            mouse_controller.end_drag()

        if event_logger:
            event_logger.log("emergency_stop", "Emergency stop triggered from keyboard.")

        if logger:
            logger.warning("Emergency stop triggered from keyboard")

        return False

    if key == ord("p"):
        if safety_manager.control_enabled:
            safety_manager.pause_control()

            if mouse_controller is not None and mouse_controller.drag_active:
                mouse_controller.end_drag()

            if event_logger:
                event_logger.log("control_paused", "Control paused from keyboard.")

            if logger:
                logger.info("Control paused from keyboard")
        else:
            if mouse_controller is not None and mouse_controller.desktop_control_enabled:
                safety_manager.resume_control()

                if event_logger:
                    event_logger.log("control_resumed", "Control resumed from keyboard.")

                if logger:
                    logger.info("Control resumed from keyboard")

        return False

    if key == ord("m"):
        new_mode = mode_manager.cycle_next()

        if air_canvas is not None and new_mode.value != "drawing":
            air_canvas.lift_pen()

        if event_logger:
            event_logger.log("mode_changed", "Mode changed from keyboard.", mode=new_mode.value)

        if logger:
            logger.info("Mode changed to %s", new_mode.value)

        return False

    if key in (ord("1"), ord("2"), ord("3"), ord("4"), ord("5"), ord("6"), ord("7")):
        selected_mode = mode_manager.set_from_shortcut(chr(key))

        if selected_mode and air_canvas is not None and selected_mode.value != "drawing":
            air_canvas.lift_pen()

        if selected_mode and event_logger:
            event_logger.log("mode_changed", "Mode changed by shortcut.", mode=selected_mode.value)

        if selected_mode and logger:
            logger.info("Mode changed to %s", selected_mode.value)

        return False

    if key == ord("c") and air_canvas is not None:
        air_canvas.clear()

        if event_logger:
            event_logger.log("drawing", "Canvas cleared from keyboard.")

        return False

    return False


def _build_hud_status(
    gesture_label: str,
    gesture_confidence: float,
    result_hand_count: int,
    primary_handedness: str,
    fps: float,
    mode_manager: ModeManager,
    profile_manager: ProfileManager,
    safety_manager: SafetyManager,
    dispatch_result: ActionDispatchResult,
    mouse_controller: MouseController | None,
    system_controller: SystemController | None,
    event_logger: DiagnosticEventLogger | None,
) -> HUDStatus:
    desktop_control_enabled = (
        (
            mouse_controller is not None
            and mouse_controller.desktop_control_enabled
        )
        or (
            system_controller is not None
            and system_controller.desktop_control_enabled
        )
    ) and safety_manager.control_enabled and not safety_manager.emergency_stopped

    cursor_tuple = None

    if dispatch_result.cursor_position is not None:
        cursor_tuple = (
            dispatch_result.cursor_position.x,
            dispatch_result.cursor_position.y,
        )

    warning = dispatch_result.message

    if safety_manager.emergency_stopped:
        warning = "EMERGENCY STOP ACTIVE. Restart runtime before controlling again."

    tracking_status = "Tracking" if result_hand_count > 0 else "No hand detected"

    return HUDStatus(
        active_mode=mode_manager.get_mode().value,
        active_profile=profile_manager.active_profile_name,
        tracking_status=tracking_status,
        gesture_label=gesture_label,
        gesture_confidence=gesture_confidence,
        action_name=dispatch_result.action_name,
        fps=fps,
        hand_count=result_hand_count,
        handedness=primary_handedness,
        desktop_control_enabled=desktop_control_enabled,
        safe_mode=safety_manager.safe_mode,
        cursor_position=cursor_tuple,
        warning=warning,
        diagnostics_enabled=event_logger is not None and event_logger.enabled,
    )