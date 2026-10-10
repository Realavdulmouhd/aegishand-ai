from aegishand.safety.safety_manager import SafetyManager


def test_permission_required_blocks_action_before_control_enabled() -> None:
    safety = SafetyManager(
        safe_mode=True,
        require_permission=True,
        control_enabled=False,
    )

    assert safety.can_execute_action("move_cursor") is False
    assert "permission" in safety.last_block_reason.lower()


def test_permission_allows_action_after_request() -> None:
    safety = SafetyManager(
        safe_mode=True,
        require_permission=True,
        control_enabled=False,
    )

    safety.request_control_permission()

    assert safety.can_execute_action("move_cursor") is True


def test_emergency_stop_blocks_action() -> None:
    safety = SafetyManager(
        safe_mode=True,
        require_permission=True,
        control_enabled=True,
    )

    safety.trigger_emergency_stop()

    assert safety.can_execute_action("left_click") is False
    assert safety.control_enabled is False
    assert safety.emergency_stopped is True


def test_safe_mode_blocks_dangerous_action() -> None:
    safety = SafetyManager(
        safe_mode=True,
        require_permission=True,
        control_enabled=True,
    )

    assert safety.can_execute_action("dangerous_test", is_dangerous=True) is False
    assert "dangerous" in safety.last_block_reason.lower()