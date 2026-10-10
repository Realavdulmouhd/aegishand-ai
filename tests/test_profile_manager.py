from pathlib import Path

import pytest

from aegishand.profiles.profile_manager import ProfileError, ProfileManager


def test_profile_manager_loads_default_profile() -> None:
    manager = ProfileManager.from_yaml(
        path=Path("config/gestures.yaml"),
        active_profile="default",
    )

    assert manager.active_profile_name == "default"
    assert "default" in manager.list_profiles()


def test_profile_manager_resolves_action() -> None:
    manager = ProfileManager.from_yaml(
        path=Path("config/gestures.yaml"),
        active_profile="default",
    )

    action = manager.resolve_action(
        mode="mouse",
        gesture="peace",
    )

    assert action == "left_click"


def test_profile_manager_rejects_unknown_profile() -> None:
    with pytest.raises(ProfileError):
        ProfileManager.from_yaml(
            path=Path("config/gestures.yaml"),
            active_profile="unknown_profile",
        )


def test_profile_manager_can_switch_profile() -> None:
    manager = ProfileManager.from_yaml(
        path=Path("config/gestures.yaml"),
        active_profile="default",
    )

    profile = manager.set_active_profile("media")

    assert profile.name == "media"
    assert manager.active_profile_name == "media"