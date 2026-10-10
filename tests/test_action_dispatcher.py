from __future__ import annotations

from dataclasses import dataclass

from aegishand.control.action_dispatcher import ActionDispatcher, ActionDispatcherConfig
from aegishand.control.mouse_controller import CursorPosition
from aegishand.control.system_controller import SystemActionResult
from aegishand.gestures.gesture_types import GestureType, RecognizedGesture
from aegishand.modes.mode_manager import ModeManager
from aegishand.profiles.profile_manager import ProfileManager
from aegishand.safety.cooldown import CooldownManager
from aegishand.safety.safety_manager import SafetyManager
from aegishand.vision.landmark_utils import NormalizedLandmark


@dataclass(frozen=True)
class FakeHand:
    handedness: str
    confidence: float
    landmarks: tuple[NormalizedLandmark, ...]


class FakeMouse:
    def __init__(self) -> None:
        self.desktop_control_enabled = True
        self.drag_active = False
        self.left_clicks = 0
        self.right_clicks = 0
        self.scroll_amounts: list[int] = []
        self.last_position: CursorPosition | None = None

    def preview_target(self, normalized_x: float, normalized_y: float) -> CursorPosition:
        self.last_position = CursorPosition(x=int(normalized_x * 1000), y=int(normalized_y * 1000))
        return self.last_position

    def move_to(self, normalized_x: float, normalized_y: float) -> CursorPosition:
        return self.preview_target(normalized_x, normalized_y)

    def left_click(self) -> bool:
        self.left_clicks += 1
        return True

    def right_click(self) -> bool:
        self.right_clicks += 1
        return True

    def start_drag(self) -> bool:
        if self.drag_active:
            return False
        self.drag_active = True
        return True

    def update_drag(self, normalized_x: float, normalized_y: float) -> CursorPosition:
        return self.preview_target(normalized_x, normalized_y)

    def end_drag(self) -> bool:
        if not self.drag_active:
            return False
        self.drag_active = False
        return True

    def scroll(self, amount: int) -> bool:
        self.scroll_amounts.append(amount)
        return True

    def reset_smoothing(self) -> None:
        self.last_position = None


class FakeSystem:
    def __init__(self) -> None:
        self.desktop_control_enabled = True
        self.calls: list[str] = []

    def play_pause(self) -> SystemActionResult:
        self.calls.append("play_pause")
        return SystemActionResult(True, "Play or pause executed.")

    def next_track(self) -> SystemActionResult:
        self.calls.append("next_track")
        return SystemActionResult(True, "Next track executed.")

    def previous_track(self) -> SystemActionResult:
        self.calls.append("previous_track")
        return SystemActionResult(True, "Previous track executed.")

    def mute(self) -> SystemActionResult:
        self.calls.append("mute")
        return SystemActionResult(True, "Mute executed.")

    def volume_up(self) -> SystemActionResult:
        self.calls.append("volume_up")
        return SystemActionResult(True, "Volume up executed.")

    def volume_down(self) -> SystemActionResult:
        self.calls.append("volume_down")
        return SystemActionResult(True, "Volume down executed.")

    def brightness_up(self) -> SystemActionResult:
        self.calls.append("brightness_up")
        return SystemActionResult(True, "Brightness up executed.")

    def brightness_down(self) -> SystemActionResult:
        self.calls.append("brightness_down")
        return SystemActionResult(True, "Brightness down executed.")

    def presentation_start(self) -> SystemActionResult:
        self.calls.append("presentation_start")
        return SystemActionResult(True, "Presentation start executed.")

    def presentation_next(self) -> SystemActionResult:
        self.calls.append("presentation_next")
        return SystemActionResult(True, "Next slide executed.")

    def presentation_previous(self) -> SystemActionResult:
        self.calls.append("presentation_previous")
        return SystemActionResult(True, "Previous slide executed.")

    def presentation_blank(self) -> SystemActionResult:
        self.calls.append("presentation_blank")
        return SystemActionResult(True, "Blank screen executed.")

    def presentation_unblank(self) -> SystemActionResult:
        self.calls.append("presentation_unblank")
        return SystemActionResult(True, "Unblank screen executed.")

    def presentation_zoom_in(self) -> SystemActionResult:
        self.calls.append("presentation_zoom_in")
        return SystemActionResult(True, "Zoom in executed.")

    def presentation_zoom_out(self) -> SystemActionResult:
        self.calls.append("presentation_zoom_out")
        return SystemActionResult(True, "Zoom out executed.")


def make_hand(wrist_y: float = 0.50) -> FakeHand:
    landmarks = [NormalizedLandmark(index=i, x=0.5, y=0.5, z=0.0) for i in range(21)]
    landmarks[0] = NormalizedLandmark(index=0, x=0.5, y=wrist_y, z=0.0)
    landmarks[8] = NormalizedLandmark(index=8, x=0.40, y=0.30, z=0.0)

    return FakeHand(handedness="Right", confidence=0.95, landmarks=tuple(landmarks))


def make_dispatcher() -> tuple[ActionDispatcher, FakeMouse, FakeSystem, SafetyManager, ModeManager]:
    safety = SafetyManager(safe_mode=True, require_permission=True, control_enabled=True)
    mode_manager = ModeManager()
    profile_manager = ProfileManager.from_yaml(path="config/gestures.yaml", active_profile="default")

    mouse = FakeMouse()
    system = FakeSystem()

    dispatcher = ActionDispatcher(
        mode_manager=mode_manager,
        profile_manager=profile_manager,
        safety_manager=safety,
        cooldown_manager=CooldownManager(default_seconds=0.1),
        mouse_controller=mouse,
        system_controller=system,
        config=ActionDispatcherConfig(
            click_cooldown_seconds=0.1,
            right_click_cooldown_seconds=0.1,
            scroll_cooldown_seconds=0.0,
            system_action_cooldown_seconds=0.0,
            brightness_cooldown_seconds=0.0,
            presentation_cooldown_seconds=0.0,
            two_hand_cooldown_seconds=0.0,
        ),
    )

    return dispatcher, mouse, system, safety, mode_manager


def test_index_point_moves_cursor() -> None:
    dispatcher, mouse, _, _, _ = make_dispatcher()

    result = dispatcher.dispatch(
        gesture=RecognizedGesture(GestureType.INDEX_POINT, confidence=0.90),
        hand=make_hand(),
    )

    assert result.action_name == "move_cursor"
    assert result.cursor_position == CursorPosition(x=400, y=300)
    assert mouse.last_position == CursorPosition(x=400, y=300)


def test_presentation_next_slide() -> None:
    dispatcher, _, system, _, mode_manager = make_dispatcher()
    mode_manager.set_mode("presentation")

    result = dispatcher.dispatch(
        gesture=RecognizedGesture(GestureType.INDEX_POINT, confidence=0.90),
        hand=make_hand(),
    )

    assert result.action_name == "presentation_next"
    assert system.calls == ["presentation_next"]


def test_drawing_action_is_local() -> None:
    dispatcher, _, _, _, mode_manager = make_dispatcher()
    mode_manager.set_mode("drawing")

    result = dispatcher.dispatch(
        gesture=RecognizedGesture(GestureType.INDEX_POINT, confidence=0.90),
        hand=make_hand(),
    )

    assert result.action_name == "draw_air"
    assert result.executed is True


def test_two_hand_lock_pauses_control() -> None:
    dispatcher, _, _, safety, mode_manager = make_dispatcher()
    mode_manager.set_mode("mouse")

    result = dispatcher.dispatch(
        gesture=RecognizedGesture(GestureType.TWO_HAND_LOCK, confidence=0.95),
        hand=None,
    )

    assert result.action_name == "emergency_pause"
    assert safety.control_enabled is False


def test_two_hand_zoom_in_controls_presentation() -> None:
    dispatcher, _, system, _, mode_manager = make_dispatcher()
    mode_manager.set_mode("presentation")

    result = dispatcher.dispatch(
        gesture=RecognizedGesture(GestureType.TWO_HAND_ZOOM_IN, confidence=0.90),
        hand=None,
    )

    assert result.action_name == "presentation_zoom_in"
    assert system.calls == ["presentation_zoom_in"]