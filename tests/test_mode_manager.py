import pytest

from aegishand.modes.mode_manager import ControlMode, ModeManager


def test_default_mode_is_mouse() -> None:
    manager = ModeManager()

    assert manager.get_mode() == ControlMode.MOUSE


def test_mode_can_be_changed_with_enum() -> None:
    manager = ModeManager()

    manager.set_mode(ControlMode.MEDIA)

    assert manager.is_mode(ControlMode.MEDIA)


def test_mode_can_be_changed_with_string() -> None:
    manager = ModeManager()

    manager.set_mode("presentation")

    assert manager.get_mode() == ControlMode.PRESENTATION


def test_invalid_mode_is_rejected() -> None:
    manager = ModeManager()

    with pytest.raises(ValueError):
        manager.set_mode("chaos_mode")


def test_mode_can_cycle() -> None:
    manager = ModeManager()

    next_mode = manager.cycle_next()

    assert next_mode == ControlMode.SCROLL


def test_mode_shortcut_changes_to_drawing() -> None:
    manager = ModeManager()

    selected = manager.set_from_shortcut("6")

    assert selected == ControlMode.DRAWING
    assert manager.get_mode() == ControlMode.DRAWING


def test_unknown_shortcut_returns_none() -> None:
    manager = ModeManager()

    selected = manager.set_from_shortcut("x")

    assert selected is None
    assert manager.get_mode() == ControlMode.MOUSE