from pathlib import Path

from aegishand.configuration.settings_loader import load_settings


def test_settings_loader_reads_main_config() -> None:
    settings_path = Path("config/settings.yaml")

    settings = load_settings(settings_path)

    assert settings.app.name == "AegisHand AI"
    assert settings.runtime.safe_mode is True
    assert settings.control.enabled_on_startup is False
    assert settings.system_control.volume_step > 0
    assert settings.profiles.default_profile == "default"