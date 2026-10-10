import time

from aegishand.safety.cooldown import CooldownManager


def test_cooldown_is_ready_before_first_use() -> None:
    cooldown = CooldownManager(default_seconds=1.0)

    assert cooldown.is_ready("left_click") is True


def test_cooldown_blocks_immediate_repeat() -> None:
    cooldown = CooldownManager(default_seconds=1.0)

    cooldown.mark_used("left_click")

    assert cooldown.is_ready("left_click") is False


def test_cooldown_reset_allows_action_again() -> None:
    cooldown = CooldownManager(default_seconds=1.0)

    cooldown.mark_used("left_click")
    cooldown.reset("left_click")

    assert cooldown.is_ready("left_click") is True


def test_use_if_ready_marks_action() -> None:
    cooldown = CooldownManager(default_seconds=1.0)

    assert cooldown.use_if_ready("scroll") is True
    assert cooldown.use_if_ready("scroll") is False


def test_custom_cooldown_can_be_shorter() -> None:
    cooldown = CooldownManager(default_seconds=10.0)

    cooldown.mark_used("test_action")
    time.sleep(0.02)

    assert cooldown.is_ready("test_action", cooldown_seconds=0.01) is True