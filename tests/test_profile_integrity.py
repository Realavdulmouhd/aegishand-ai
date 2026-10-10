from pathlib import Path

from aegishand.profiles.profile_manager import ProfileManager


PROJECT_ROOT = Path(__file__).resolve().parents[1]


IMPLEMENTED_ACTIONS = {
    "move_cursor",
    "left_click",
    "right_click",
    "drag",
    "scroll",
    "pause_control",
    "emergency_pause",
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
    "draw_air",
    "clear_canvas",
    "security_pause",
    "security_resume",
    "security_lock",
}


IMPLEMENTED_GESTURES = {
    "open_palm",
    "fist",
    "index_point",
    "peace",
    "three_fingers",
    "pinch",
    "two_hand_zoom_in",
    "two_hand_zoom_out",
    "two_hand_lock",
}


def test_all_profiles_load() -> None:
    manager = ProfileManager.from_yaml(
        path=PROJECT_ROOT / "config/gestures.yaml",
        active_profile="default",
    )

    assert "default" in manager.list_profiles()
    assert "accessibility" in manager.list_profiles()
    assert "media" in manager.list_profiles()
    assert "developer" in manager.list_profiles()


def test_profile_actions_are_implemented() -> None:
    manager = ProfileManager.from_yaml(
        path=PROJECT_ROOT / "config/gestures.yaml",
        active_profile="default",
    )

    for profile_name in manager.list_profiles():
        profile = manager.set_active_profile(profile_name)

        for mode_name, mapping in profile.modes.items():
            for gesture_name, action_name in mapping.items():
                assert gesture_name in IMPLEMENTED_GESTURES, (
                    f"Profile '{profile_name}', mode '{mode_name}' uses unimplemented gesture '{gesture_name}'."
                )
                assert action_name in IMPLEMENTED_ACTIONS, (
                    f"Profile '{profile_name}', mode '{mode_name}' maps to unimplemented action '{action_name}'."
                )


def test_default_profile_has_mouse_mode() -> None:
    manager = ProfileManager.from_yaml(
        path=PROJECT_ROOT / "config/gestures.yaml",
        active_profile="default",
    )

    profile = manager.active_profile

    assert "mouse" in profile.modes
    assert profile.resolve_action("mouse", "index_point") == "move_cursor"