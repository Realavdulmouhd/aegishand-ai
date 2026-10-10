from aegishand.control.system_controller import (
    SystemController,
    SystemControllerConfig,
)


def make_config() -> SystemControllerConfig:
    return SystemControllerConfig(
        volume_step=5,
        brightness_step=8,
        allow_media_keys=True,
        allow_brightness_control=True,
    )


def test_system_controller_previews_volume_without_desktop_control() -> None:
    controller = SystemController(
        config=make_config(),
        desktop_control_enabled=False,
    )

    result = controller.volume_up()

    assert result.executed is False
    assert "previewed" in result.message.lower()


def test_system_controller_previews_media_without_desktop_control() -> None:
    controller = SystemController(
        config=make_config(),
        desktop_control_enabled=False,
    )

    result = controller.play_pause()

    assert result.executed is False
    assert "previewed" in result.message.lower()


def test_system_controller_previews_brightness_without_desktop_control() -> None:
    controller = SystemController(
        config=make_config(),
        desktop_control_enabled=False,
    )

    result = controller.brightness_up()

    assert result.executed is False
    assert "previewed" in result.message.lower()