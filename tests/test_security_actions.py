from aegishand.control.system_controller import SystemController, SystemControllerConfig


def make_config(allow_security_lock: bool = True) -> SystemControllerConfig:
    return SystemControllerConfig(
        volume_step=5,
        brightness_step=8,
        allow_media_keys=True,
        allow_brightness_control=True,
        allow_security_lock=allow_security_lock,
    )


def test_security_lock_is_previewed_without_desktop_control() -> None:
    controller = SystemController(
        config=make_config(),
        desktop_control_enabled=False,
    )

    result = controller.security_lock()

    assert result.executed is False
    assert "previewed" in result.message.lower()


def test_security_lock_can_be_disabled_in_settings() -> None:
    controller = SystemController(
        config=make_config(allow_security_lock=False),
        desktop_control_enabled=False,
    )

    result = controller.security_lock()

    assert result.executed is False
    assert "disabled" in result.message.lower()


def test_media_action_is_previewed_without_desktop_control() -> None:
    controller = SystemController(
        config=make_config(),
        desktop_control_enabled=False,
    )

    result = controller.play_pause()

    assert result.executed is False
    assert "previewed" in result.message.lower()