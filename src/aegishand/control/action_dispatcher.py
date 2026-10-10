from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from aegishand.control.mouse_controller import CursorPosition
from aegishand.control.system_controller import SystemActionResult
from aegishand.gestures.gesture_types import GestureType, RecognizedGesture
from aegishand.modes.mode_manager import ModeManager
from aegishand.profiles.profile_manager import ProfileManager
from aegishand.safety.cooldown import CooldownManager
from aegishand.safety.safety_manager import SafetyManager
from aegishand.vision.landmark_utils import NormalizedLandmark, get_landmark


class HandLike(Protocol):
    handedness: str
    confidence: float
    landmarks: tuple[NormalizedLandmark, ...]


class MouseControlPort(Protocol):
    desktop_control_enabled: bool
    drag_active: bool

    def preview_target(self, normalized_x: float, normalized_y: float) -> CursorPosition:
        ...

    def move_to(self, normalized_x: float, normalized_y: float) -> CursorPosition:
        ...

    def left_click(self) -> bool:
        ...

    def right_click(self) -> bool:
        ...

    def start_drag(self) -> bool:
        ...

    def update_drag(self, normalized_x: float, normalized_y: float) -> CursorPosition:
        ...

    def end_drag(self) -> bool:
        ...

    def scroll(self, amount: int) -> bool:
        ...

    def reset_smoothing(self) -> None:
        ...


class SystemControlPort(Protocol):
    desktop_control_enabled: bool

    def play_pause(self) -> SystemActionResult:
        ...

    def next_track(self) -> SystemActionResult:
        ...

    def previous_track(self) -> SystemActionResult:
        ...

    def mute(self) -> SystemActionResult:
        ...

    def volume_up(self) -> SystemActionResult:
        ...

    def volume_down(self) -> SystemActionResult:
        ...

    def brightness_up(self) -> SystemActionResult:
        ...

    def brightness_down(self) -> SystemActionResult:
        ...

    def presentation_start(self) -> SystemActionResult:
        ...

    def presentation_next(self) -> SystemActionResult:
        ...

    def presentation_previous(self) -> SystemActionResult:
        ...

    def presentation_blank(self) -> SystemActionResult:
        ...

    def presentation_unblank(self) -> SystemActionResult:
        ...

    def presentation_zoom_in(self) -> SystemActionResult:
        ...

    def presentation_zoom_out(self) -> SystemActionResult:
        ...

    def security_pause(self) -> SystemActionResult:
        ...

    def security_resume(self) -> SystemActionResult:
        ...

    def security_lock(self) -> SystemActionResult:
        ...


@dataclass(frozen=True)
class ActionDispatcherConfig:
    min_action_confidence: float = 0.70

    # Backward-compatible name used by older tests/code.
    confidence_threshold: float = 0.70

    click_cooldown_seconds: float = 0.55
    right_click_cooldown_seconds: float = 0.70
    drag_cooldown_seconds: float = 0.20
    scroll_cooldown_seconds: float = 0.08

    system_action_cooldown_seconds: float = 0.55
    brightness_cooldown_seconds: float = 0.85
    presentation_cooldown_seconds: float = 0.65
    two_hand_cooldown_seconds: float = 0.85
    security_action_cooldown_seconds: float = 0.90
    local_action_cooldown_seconds: float = 0.10

    scroll_deadzone: float = 0.025

    # Backward-compatible name used by older tests/code.
    scroll_dead_zone: float = 0.035

    scroll_sensitivity: int = 900

    # Backward-compatible simple scroll amount.
    scroll_amount: int = 4


@dataclass(frozen=True, init=False)
class ActionDispatchResult:
    action_name: str
    executed: bool
    message: str
    cursor_position: CursorPosition | None
    preview_only: bool

    def __init__(
        self,
        action_name: str,
        executed: bool,
        message: str | None = None,
        cursor_position: CursorPosition | None = None,
        preview_only: bool = False,
        reason: str | None = None,
    ) -> None:
        object.__setattr__(self, "action_name", action_name)
        object.__setattr__(self, "executed", executed)
        object.__setattr__(
            self,
            "message",
            message if message is not None else reason or "",
        )
        object.__setattr__(self, "cursor_position", cursor_position)
        object.__setattr__(self, "preview_only", preview_only)

    @property
    def success(self) -> bool:
        return self.executed

    @property
    def reason(self) -> str:
        return self.message


@dataclass(frozen=True)
class ActionCatalog:
    mouse_actions: frozenset[str]
    system_actions: frozenset[str]
    safety_actions: frozenset[str]
    local_actions: frozenset[str]
    two_hand_actions: frozenset[str]

    @classmethod
    def build_default(cls) -> ActionCatalog:
        return cls(
            mouse_actions=frozenset(
                {
                    "move_cursor",
                    "left_click",
                    "right_click",
                    "drag",
                    "start_drag",
                    "update_drag",
                    "end_drag",
                    "scroll",
                    "scroll_up",
                    "scroll_down",
                }
            ),
            system_actions=frozenset(
                {
                    "play_pause",
                    "next_track",
                    "previous_track",
                    "mute",
                    "volume_up",
                    "volume_down",
                    "brightness_up",
                    "brightness_down",
                    "presentation_start",
                    "presentation_next",
                    "presentation_previous",
                    "presentation_blank",
                    "presentation_unblank",
                    "presentation_zoom_in",
                    "presentation_zoom_out",
                    "security_lock",
                }
            ),
            safety_actions=frozenset(
                {
                    "pause_control",
                    "emergency_pause",
                    "security_pause",
                    "security_resume",
                }
            ),
            local_actions=frozenset(
                {
                    "draw_air",
                    "clear_canvas",
                }
            ),
            two_hand_actions=frozenset(
                {
                    "two_hand_lock",
                    "two_hand_zoom_in",
                    "two_hand_zoom_out",
                }
            ),
        )

    def contains(self, action_name: str) -> bool:
        return (
            action_name in self.mouse_actions
            or action_name in self.system_actions
            or action_name in self.safety_actions
            or action_name in self.local_actions
        )


class ActionDispatcher:
    def __init__(
        self,
        mode_manager: ModeManager,
        profile_manager: ProfileManager | None = None,
        safety_manager: SafetyManager | None = None,
        cooldown_manager: CooldownManager | None = None,
        mouse_controller: MouseControlPort | None = None,
        system_controller: SystemControlPort | None = None,
        config: ActionDispatcherConfig | None = None,
        desktop_control_enabled: bool | None = None,
        logger: Any | None = None,
        **_: Any,
    ) -> None:
        if safety_manager is None:
            raise TypeError("ActionDispatcher requires safety_manager.")

        if cooldown_manager is None:
            raise TypeError("ActionDispatcher requires cooldown_manager.")

        self.mode_manager = mode_manager
        self.profile_manager = profile_manager
        self.safety_manager = safety_manager
        self.cooldown_manager = cooldown_manager
        self.mouse = mouse_controller
        self.mouse_controller = mouse_controller
        self.system = system_controller
        self.system_controller = system_controller
        self.config = config or ActionDispatcherConfig()
        self.catalog = ActionCatalog.build_default()
        self.logger = logger

        self.desktop_control_enabled = (
            desktop_control_enabled
            if desktop_control_enabled is not None
            else self._detect_desktop_control_enabled()
        )

        self._last_scroll_y: float | None = None
        self._dragging = False

    def dispatch(
        self,
        gesture: RecognizedGesture | None = None,
        hand: HandLike | None = None,
        action_name: str | None = None,
        gesture_or_action: RecognizedGesture | str | None = None,
        payload: dict[str, Any] | None = None,
        confidence: float | None = None,
        is_dangerous: bool = False,
        **kwargs: Any,
    ) -> ActionDispatchResult:
        payload = payload or {}

        if hand is None:
            hand = kwargs.get("hand")

        if gesture is None and isinstance(gesture_or_action, RecognizedGesture):
            gesture = gesture_or_action

        if gesture is None and gesture_or_action is not None:
            if self._looks_like_gesture(gesture_or_action):
                gesture = gesture_or_action  # type: ignore[assignment]

        if action_name is None and isinstance(gesture_or_action, str):
            action_name = gesture_or_action

        if action_name is None:
            action_name = payload.get("action_name") or kwargs.get("action")

        if action_name is not None:
            return self.dispatch_action(
                action_name=action_name,
                hand=hand,
                confidence=confidence if confidence is not None else 1.0,
                is_dangerous=is_dangerous,
            )

        if gesture is None:
            self._stop_continuous_actions()
            self._last_scroll_y = None

            return self._result(
                action_name="none",
                executed=False,
                message="No gesture or action was provided.",
                preview_only=True,
            )

        return self.dispatch_gesture(
            gesture=gesture,
            hand=hand,
        )

    def dispatch_gesture(
        self,
        gesture: RecognizedGesture,
        hand: HandLike | None,
    ) -> ActionDispatchResult:
        gesture_label = self._gesture_label(gesture)

        if hand is None and gesture_label not in {
            "two_hand_lock",
            "two_hand_zoom_in",
            "two_hand_zoom_out",
        }:
            self._stop_continuous_actions()
            self._last_scroll_y = None

            return self._result(
                action_name="none",
                executed=False,
                message="No hand detected.",
                preview_only=True,
            )

        active_mode = self._active_mode()
        action_name = self._resolve_action(
            active_mode=active_mode,
            gesture_label=gesture_label,
        )

        if action_name in {"none", "no_action", ""}:
            self._stop_continuous_actions()

            return self._result(
                action_name="none",
                executed=False,
                message=(
                    f"No profile mapping for gesture '{gesture_label}' "
                    f"in mode '{active_mode}'."
                ),
                preview_only=True,
            )

        if action_name in {"pause_control", "emergency_pause"}:
            self._stop_continuous_actions()
            self._pause_control()

            return self._result(
                action_name=action_name,
                executed=True,
                message=(
                    "Two-hand lock detected. Control paused safely."
                    if action_name == "emergency_pause"
                    else "Control paused by gesture."
                ),
            )

        gesture_confidence = self._gesture_confidence(gesture, hand)

        if gesture_confidence < self._confidence_threshold():
            self._stop_continuous_actions()

            return self._result(
                action_name=action_name,
                executed=False,
                message="Gesture confidence is too low for action.",
                preview_only=True,
            )

        return self._execute_action(
            action_name=action_name,
            hand=hand,
        )

    def dispatch_action(
        self,
        action_name: str,
        hand: HandLike | None = None,
        confidence: float = 1.0,
        is_dangerous: bool = False,
    ) -> ActionDispatchResult:
        normalized_action = self._normalize_action(action_name)

        if confidence < self._confidence_threshold():
            self._stop_continuous_actions()

            return self._result(
                action_name=normalized_action,
                executed=False,
                message="Action confidence is too low.",
                preview_only=True,
            )

        if normalized_action in {"pause_control", "emergency_pause"}:
            self._stop_continuous_actions()
            self._pause_control()

            return self._result(
                action_name=normalized_action,
                executed=True,
                message="Control paused safely.",
            )

        if normalized_action in {"none", "no_action", ""}:
            self._stop_continuous_actions()

            return self._result(
                action_name="none",
                executed=False,
                message="No action is mapped.",
                preview_only=True,
            )

        if not self._can_execute(normalized_action, is_dangerous=is_dangerous):
            return self._result(
                action_name=normalized_action,
                executed=False,
                message=self._safety_reason(),
                preview_only=True,
            )

        return self._execute_action(
            action_name=normalized_action,
            hand=hand,
        )

    def _execute_action(
        self,
        action_name: str,
        hand: HandLike | None,
    ) -> ActionDispatchResult:
        mouse_actions = {
            "move_cursor",
            "left_click",
            "right_click",
            "drag",
            "start_drag",
            "update_drag",
            "end_drag",
            "scroll",
            "scroll_up",
            "scroll_down",
        }

        system_actions = {
            "play_pause",
            "next_track",
            "previous_track",
            "mute",
            "volume_up",
            "volume_down",
            "brightness_up",
            "brightness_down",
            "presentation_start",
            "presentation_next",
            "presentation_previous",
            "presentation_blank",
            "presentation_unblank",
            "presentation_zoom_in",
            "presentation_zoom_out",
            "security_lock",
        }

        safety_actions = {
            "security_pause",
            "security_resume",
        }

        local_actions = {
            "draw_air",
            "clear_canvas",
        }

        if action_name in mouse_actions:
            if hand is None:
                return self._result(
                    action_name=action_name,
                    executed=False,
                    message="Mouse action needs a primary hand.",
                    preview_only=True,
                )

            return self._execute_mouse_action(
                action_name=action_name,
                hand=hand,
            )

        if action_name in system_actions:
            return self._execute_system_action(action_name=action_name)

        if action_name in safety_actions:
            return self._execute_safety_action(action_name=action_name)

        if action_name in local_actions:
            self._stop_continuous_actions()

            return self._result(
                action_name=action_name,
                executed=True,
                message=f"Local action '{action_name}' ready.",
                preview_only=True,
            )

        self._stop_continuous_actions()

        return self._result(
            action_name=action_name,
            executed=False,
            message=f"Action '{action_name}' is configured but not implemented yet.",
            preview_only=True,
        )

    def _execute_mouse_action(
        self,
        action_name: str,
        hand: HandLike,
    ) -> ActionDispatchResult:
        if self.mouse is None:
            return self._result(
                action_name=action_name,
                executed=False,
                message=f"{action_name} previewed only. Mouse controller is not connected.",
                preview_only=True,
            )

        if action_name == "move_cursor":
            return self._move_cursor(hand)

        if action_name == "left_click":
            return self._click(hand, action_name="left_click")

        if action_name == "right_click":
            return self._click(hand, action_name="right_click")

        if action_name in {"drag", "start_drag"}:
            return self._drag(hand)

        if action_name == "update_drag":
            return self._update_drag(hand)

        if action_name == "end_drag":
            return self._end_drag()

        if action_name in {"scroll", "scroll_up", "scroll_down"}:
            return self._scroll(hand, forced_action=action_name)

        return self._result(
            action_name=action_name,
            executed=False,
            message=f"Mouse action '{action_name}' is not handled.",
            preview_only=True,
        )

    def _execute_safety_action(self, action_name: str) -> ActionDispatchResult:
        self._stop_continuous_actions()

        cooldown = self.config.security_action_cooldown_seconds

        if not self._consume_cooldown(action_name, cooldown):
            remaining = self._remaining_cooldown(action_name, cooldown)

            return self._result(
                action_name=action_name,
                executed=False,
                message=f"{action_name} is cooling down for {remaining:.2f}s.",
                preview_only=True,
            )

        if action_name == "security_pause":
            self._pause_control()

            return self._result(
                action_name=action_name,
                executed=True,
                message="Security pause executed. Control is paused safely.",
            )

        if action_name == "security_resume":
            resumed = self._resume_control()

            return self._result(
                action_name=action_name,
                executed=resumed,
                message=(
                    "Security resume executed. Control is enabled again."
                    if resumed
                    else "Security resume was blocked by emergency stop or missing permission."
                ),
                preview_only=not resumed,
            )

        return self._result(
            action_name=action_name,
            executed=False,
            message=f"Safety action '{action_name}' is not implemented.",
            preview_only=True,
        )

    def _execute_system_action(self, action_name: str) -> ActionDispatchResult:
        self._stop_continuous_actions()

        if self.system is None:
            return self._result(
                action_name=action_name,
                executed=False,
                message=f"{action_name} previewed only. System controller is not connected.",
                preview_only=True,
            )

        cooldown = self._cooldown_for_action(action_name)

        if not self._consume_cooldown(action_name, cooldown):
            remaining = self._remaining_cooldown(action_name, cooldown)

            return self._result(
                action_name=action_name,
                executed=False,
                message=f"{action_name} is cooling down for {remaining:.2f}s.",
                preview_only=True,
            )

        if not self._can_execute(action_name):
            return self._result(
                action_name=action_name,
                executed=False,
                message=self._safety_reason(),
                preview_only=True,
            )

        system_action = getattr(self.system, action_name, None)

        if not callable(system_action):
            return self._result(
                action_name=action_name,
                executed=False,
                message=f"System controller does not support '{action_name}'.",
                preview_only=True,
            )

        result = system_action()

        return self._result(
            action_name=action_name,
            executed=bool(result.executed),
            message=str(result.message),
            preview_only=not bool(result.executed),
        )

    def _move_cursor(self, hand: HandLike) -> ActionDispatchResult:
        self._end_drag_if_needed()

        index_tip = self._get_landmark(hand, 8, "index_tip")

        if index_tip is None:
            return self._result(
                action_name="move_cursor",
                executed=False,
                message="Index fingertip landmark was not found.",
                preview_only=True,
            )

        if self._can_execute("move_cursor"):
            cursor_position = self.mouse.move_to(index_tip.x, index_tip.y)

            executed = bool(getattr(self.mouse, "desktop_control_enabled", False))

            return self._result(
                action_name="move_cursor",
                executed=executed,
                message="Cursor moved." if executed else "Cursor target previewed.",
                cursor_position=cursor_position,
                preview_only=not executed,
            )

        cursor_position = self.mouse.preview_target(index_tip.x, index_tip.y)

        return self._result(
            action_name="move_cursor_preview",
            executed=False,
            message=self._safety_reason(),
            cursor_position=cursor_position,
            preview_only=True,
        )

    def _click(self, hand: HandLike, action_name: str) -> ActionDispatchResult:
        self._end_drag_if_needed()

        index_tip = self._get_landmark(hand, 8, "index_tip")

        if index_tip is None:
            return self._result(
                action_name=action_name,
                executed=False,
                message="Index fingertip landmark was not found.",
                preview_only=True,
            )

        cursor_position = self.mouse.preview_target(index_tip.x, index_tip.y)

        cooldown = (
            self.config.click_cooldown_seconds
            if action_name == "left_click"
            else self.config.right_click_cooldown_seconds
        )

        if not self._consume_cooldown(action_name, cooldown):
            remaining = self._remaining_cooldown(action_name, cooldown)

            return self._result(
                action_name=action_name,
                executed=False,
                message=f"{action_name} is cooling down for {remaining:.2f}s.",
                cursor_position=cursor_position,
                preview_only=True,
            )

        if not self._can_execute(action_name):
            return self._result(
                action_name=action_name,
                executed=False,
                message=self._safety_reason(),
                cursor_position=cursor_position,
                preview_only=True,
            )

        executed = (
            self.mouse.left_click()
            if action_name == "left_click"
            else self.mouse.right_click()
        )

        return self._result(
            action_name=action_name,
            executed=executed,
            message=(
                f"{action_name} executed."
                if executed
                else f"{action_name} previewed only."
            ),
            cursor_position=cursor_position,
            preview_only=not executed,
        )

    def _drag(self, hand: HandLike) -> ActionDispatchResult:
        index_tip = self._get_landmark(hand, 8, "index_tip")

        if index_tip is None:
            return self._result(
                action_name="drag",
                executed=False,
                message="Index fingertip landmark was not found.",
                preview_only=True,
            )

        if not self._can_execute("drag"):
            cursor_position = self.mouse.preview_target(index_tip.x, index_tip.y)

            return self._result(
                action_name="drag_preview",
                executed=False,
                message=self._safety_reason(),
                cursor_position=cursor_position,
                preview_only=True,
            )

        started = self.mouse.start_drag()
        cursor_position = self.mouse.update_drag(index_tip.x, index_tip.y)

        executed = bool(getattr(self.mouse, "desktop_control_enabled", False))
        self._dragging = bool(getattr(self.mouse, "drag_active", False))

        return self._result(
            action_name="drag",
            executed=executed,
            message="Drag started." if started else "Dragging.",
            cursor_position=cursor_position,
            preview_only=not executed,
        )

    def _update_drag(self, hand: HandLike) -> ActionDispatchResult:
        index_tip = self._get_landmark(hand, 8, "index_tip")

        if index_tip is None:
            return self._result(
                action_name="update_drag",
                executed=False,
                message="Index fingertip landmark was not found.",
                preview_only=True,
            )

        if not self._can_execute("drag"):
            cursor_position = self.mouse.preview_target(index_tip.x, index_tip.y)

            return self._result(
                action_name="drag_preview",
                executed=False,
                message=self._safety_reason(),
                cursor_position=cursor_position,
                preview_only=True,
            )

        cursor_position = self.mouse.update_drag(index_tip.x, index_tip.y)

        executed = bool(getattr(self.mouse, "desktop_control_enabled", False))

        return self._result(
            action_name="update_drag",
            executed=executed,
            message="Drag updated.",
            cursor_position=cursor_position,
            preview_only=not executed,
        )

    def _end_drag(self) -> ActionDispatchResult:
        if self.mouse is None:
            return self._result(
                action_name="end_drag",
                executed=False,
                message="Mouse controller is not connected.",
                preview_only=True,
            )

        was_active = bool(getattr(self.mouse, "drag_active", False))
        executed = self.mouse.end_drag()
        self._dragging = False

        return self._result(
            action_name="end_drag",
            executed=executed,
            message="Drag ended." if was_active else "Drag was not active.",
            preview_only=not executed,
        )

    def _scroll(
        self,
        hand: HandLike,
        forced_action: str = "scroll",
    ) -> ActionDispatchResult:
        self._end_drag_if_needed()

        wrist = self._get_landmark(hand, 0, "wrist")

        if wrist is None:
            return self._result(
                action_name="scroll",
                executed=False,
                message="Wrist landmark was not found.",
                preview_only=True,
            )

        if self._last_scroll_y is None:
            self._last_scroll_y = wrist.y

            return self._result(
                action_name="scroll_ready",
                executed=False,
                message="Scroll reference locked. Move palm up or down.",
                preview_only=True,
            )

        if forced_action == "scroll_up":
            scroll_amount = abs(self.config.scroll_sensitivity // 25)
        elif forced_action == "scroll_down":
            scroll_amount = -abs(self.config.scroll_sensitivity // 25)
        else:
            delta_y = wrist.y - self._last_scroll_y
            self._last_scroll_y = wrist.y

            if abs(delta_y) < self._scroll_deadzone():
                return self._result(
                    action_name="scroll",
                    executed=False,
                    message="Palm movement is inside scroll dead zone.",
                    preview_only=True,
                )

            scroll_amount = int(-delta_y * self.config.scroll_sensitivity)

            if scroll_amount == 0:
                scroll_amount = (
                    -self.config.scroll_amount
                    if delta_y > 0
                    else self.config.scroll_amount
                )

        if scroll_amount == 0:
            return self._result(
                action_name="scroll",
                executed=False,
                message="Scroll amount is too small.",
                preview_only=True,
            )

        if not self._consume_cooldown("scroll", self.config.scroll_cooldown_seconds):
            return self._result(
                action_name="scroll",
                executed=False,
                message="Scroll cooldown active.",
                preview_only=True,
            )

        if not self._can_execute("scroll"):
            return self._result(
                action_name="scroll",
                executed=False,
                message=self._safety_reason(),
                preview_only=True,
            )

        executed = self.mouse.scroll(scroll_amount)

        return self._result(
            action_name="scroll",
            executed=executed,
            message=(
                f"Scrolled {scroll_amount}."
                if executed
                else f"Scroll preview: {scroll_amount}."
            ),
            preview_only=not executed,
        )

    def _resolve_action(self, active_mode: str, gesture_label: str) -> str:
        if self.profile_manager is not None:
            action = self.profile_manager.resolve_action(
                mode=active_mode,
                gesture=gesture_label,
            )

            if action not in {None, "", "no_action"}:
                return self._normalize_action(action)

        fallback_maps = {
            "mouse": {
                "index_point": "move_cursor",
                "peace": "left_click",
                "three_fingers": "right_click",
                "pinch": "drag",
                "open_palm": "scroll",
                "fist": "pause_control",
                "two_hand_lock": "emergency_pause",
            },
            "scroll": {
                "open_palm": "scroll",
                "fist": "pause_control",
                "two_hand_lock": "emergency_pause",
            },
            "media": {
                "open_palm": "play_pause",
                "peace": "next_track",
                "three_fingers": "previous_track",
                "pinch": "mute",
                "fist": "pause_control",
                "two_hand_lock": "emergency_pause",
            },
            "volume": {
                "index_point": "volume_up",
                "peace": "volume_down",
                "pinch": "mute",
                "three_fingers": "brightness_up",
                "open_palm": "brightness_down",
                "fist": "pause_control",
                "two_hand_lock": "emergency_pause",
            },
            "presentation": {
                "open_palm": "presentation_start",
                "index_point": "presentation_next",
                "peace": "presentation_previous",
                "three_fingers": "presentation_blank",
                "pinch": "presentation_unblank",
                "fist": "pause_control",
                "two_hand_zoom_in": "presentation_zoom_in",
                "two_hand_zoom_out": "presentation_zoom_out",
                "two_hand_lock": "emergency_pause",
            },
            "security": {
                "open_palm": "security_resume",
                "index_point": "security_pause",
                "peace": "security_lock",
                "three_fingers": "security_lock",
                "pinch": "security_pause",
                "fist": "security_pause",
                "two_hand_lock": "security_pause",
            },
            "drawing": {
                "index_point": "draw_air",
                "open_palm": "clear_canvas",
                "fist": "pause_control",
                "two_hand_lock": "clear_canvas",
            },
            "developer_demo": {
                "open_palm": "play_pause",
                "index_point": "move_cursor",
                "peace": "left_click",
                "fist": "pause_control",
                "two_hand_lock": "emergency_pause",
            },
        }

        return self._normalize_action(
            fallback_maps.get(active_mode, {}).get(gesture_label, "no_action")
        )

    def _active_mode(self) -> str:
        mode = self.mode_manager.get_mode()

        if hasattr(mode, "value"):
            return str(mode.value).strip().lower()

        return str(mode).strip().lower()

    def _gesture_label(self, gesture: RecognizedGesture) -> str:
        raw = getattr(gesture, "gesture", None)

        if raw is None:
            raw = getattr(gesture, "gesture_type", None)

        if raw is None:
            raw = getattr(gesture, "type", None)

        if raw is None:
            raw = getattr(gesture, "label", None)

        if raw is None:
            raw = getattr(gesture, "name", "unknown")

        if isinstance(raw, GestureType):
            return raw.value

        if hasattr(raw, "value"):
            return str(raw.value).strip().lower()

        return str(raw).strip().lower()

    def _gesture_confidence(
        self,
        gesture: RecognizedGesture,
        hand: HandLike | None,
    ) -> float:
        gesture_confidence = getattr(gesture, "confidence", None)

        if gesture_confidence is not None:
            return float(gesture_confidence)

        if hand is not None:
            return float(getattr(hand, "confidence", 1.0))

        return 1.0

    def _normalize_action(self, action_name: str | None) -> str:
        if action_name is None:
            return "no_action"

        aliases = {
            "click": "left_click",
            "primary_click": "left_click",
            "secondary_click": "right_click",
            "right_click": "right_click",
            "pinch": "drag",
            "drag_start": "drag",
            "pinch_start": "drag",
            "start_drag": "drag",
            "pinch_release": "end_drag",
            "release_drag": "end_drag",
            "release_pinch": "end_drag",
            "scroll": "scroll",
            "stop": "pause_control",
            "pause": "pause_control",
            "next_slide": "presentation_next",
            "previous_slide": "presentation_previous",
            "blank_screen": "presentation_blank",
            "start_presentation": "presentation_start",
            "lock": "security_lock",
            "lock_screen": "security_lock",
            "workstation_lock": "security_lock",
            "security_stop": "security_pause",
            "safe_pause": "security_pause",
            "safe_resume": "security_resume",
        }

        normalized = str(action_name).strip().lower()
        return aliases.get(normalized, normalized)

    def _get_landmark(
        self,
        hand: HandLike,
        index: int,
        name: str,
    ) -> NormalizedLandmark | None:
        try:
            return get_landmark(hand.landmarks, name)
        except Exception:
            pass

        try:
            return get_landmark(hand.landmarks, index)
        except Exception:
            pass

        try:
            return hand.landmarks[index]
        except Exception:
            return None

    def _cooldown_for_action(self, action_name: str) -> float:
        if action_name in {"brightness_up", "brightness_down"}:
            return self.config.brightness_cooldown_seconds

        if action_name in {"presentation_zoom_in", "presentation_zoom_out"}:
            return self.config.two_hand_cooldown_seconds

        if action_name.startswith("presentation_"):
            return self.config.presentation_cooldown_seconds

        if action_name.startswith("security_"):
            return self.config.security_action_cooldown_seconds

        if action_name in {
            "play_pause",
            "next_track",
            "previous_track",
            "mute",
            "volume_up",
            "volume_down",
        }:
            return self.config.system_action_cooldown_seconds

        return self.config.system_action_cooldown_seconds

    def _consume_cooldown(self, action_name: str, cooldown_seconds: float) -> bool:
        if cooldown_seconds <= 0:
            return True

        use_if_ready = getattr(self.cooldown_manager, "use_if_ready", None)

        if callable(use_if_ready):
            return bool(
                use_if_ready(
                    action_name,
                    cooldown_seconds=cooldown_seconds,
                )
            )

        is_ready = getattr(self.cooldown_manager, "is_ready", None)
        mark_used = getattr(self.cooldown_manager, "mark_used", None)

        if callable(is_ready):
            ready = bool(is_ready(action_name))

            if ready and callable(mark_used):
                mark_used(action_name)

            return ready

        return True

    def _remaining_cooldown(self, action_name: str, cooldown_seconds: float) -> float:
        remaining_seconds = getattr(self.cooldown_manager, "remaining_seconds", None)

        if callable(remaining_seconds):
            return float(
                remaining_seconds(
                    action_name,
                    cooldown_seconds=cooldown_seconds,
                )
            )

        return cooldown_seconds

    def _can_execute(self, action_name: str, is_dangerous: bool = False) -> bool:
        can_execute_action = getattr(self.safety_manager, "can_execute_action", None)

        if not callable(can_execute_action):
            return True

        try:
            return bool(
                can_execute_action(
                    action_name=action_name,
                    is_dangerous=is_dangerous,
                )
            )
        except TypeError:
            try:
                return bool(can_execute_action(action_name))
            except TypeError:
                return bool(can_execute_action(action_name, is_dangerous))

    def _safety_reason(self) -> str:
        return str(
            getattr(
                self.safety_manager,
                "last_block_reason",
                "Safety manager blocked this action.",
            )
        )

    def _pause_control(self) -> None:
        pause_control = getattr(self.safety_manager, "pause_control", None)

        if callable(pause_control):
            pause_control()

    def _resume_control(self) -> bool:
        if bool(getattr(self.safety_manager, "emergency_stopped", False)):
            return False

        resume_control = getattr(self.safety_manager, "resume_control", None)

        if callable(resume_control):
            resume_control()
            return bool(getattr(self.safety_manager, "control_enabled", True))

        request_control_permission = getattr(
            self.safety_manager,
            "request_control_permission",
            None,
        )

        if callable(request_control_permission):
            request_control_permission()
            return bool(getattr(self.safety_manager, "control_enabled", True))

        if hasattr(self.safety_manager, "control_enabled"):
            setattr(self.safety_manager, "control_enabled", True)
            return True

        return False

    def _stop_continuous_actions(self) -> None:
        self._end_drag_if_needed()

    def _end_drag_if_needed(self) -> None:
        if self.mouse is not None and bool(getattr(self.mouse, "drag_active", False)):
            self.mouse.end_drag()

        self._dragging = False

    def _detect_desktop_control_enabled(self) -> bool:
        mouse_enabled = bool(
            self.mouse is not None
            and getattr(self.mouse, "desktop_control_enabled", False)
        )

        system_enabled = bool(
            self.system is not None
            and getattr(self.system, "desktop_control_enabled", False)
        )

        return mouse_enabled or system_enabled

    def _confidence_threshold(self) -> float:
        return max(
            float(getattr(self.config, "min_action_confidence", 0.70)),
            float(getattr(self.config, "confidence_threshold", 0.70)),
        )

    def _scroll_deadzone(self) -> float:
        return min(
            float(getattr(self.config, "scroll_deadzone", 0.025)),
            float(getattr(self.config, "scroll_dead_zone", 0.035)),
        )

    def _looks_like_gesture(self, value: object) -> bool:
        return any(
            hasattr(value, attribute)
            for attribute in ("gesture", "gesture_type", "type", "label", "name")
        )

    def _result(
        self,
        action_name: str,
        executed: bool,
        message: str,
        cursor_position: CursorPosition | None = None,
        preview_only: bool = False,
    ) -> ActionDispatchResult:
        result = ActionDispatchResult(
            action_name=action_name,
            executed=executed,
            message=message,
            cursor_position=cursor_position,
            preview_only=preview_only,
        )

        self._log_result(result)
        return result

    def _log_result(self, result: ActionDispatchResult) -> None:
        if self.logger is None:
            return

        if result.executed:
            self.logger.info(
                "Action dispatched: %s | %s",
                result.action_name,
                result.message,
            )
            return

        self.logger.info(
            "Action blocked or previewed: %s | %s",
            result.action_name,
            result.message,
        )