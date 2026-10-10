from pathlib import Path

from aegishand.configuration.settings_loader import load_settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_settings_contract_loads_successfully() -> None:
    settings = load_settings(PROJECT_ROOT / "config/settings.yaml")

    assert settings.app.name == "AegisHand AI"
    assert settings.runtime.safe_mode is True
    assert settings.runtime.require_control_permission is True
    assert settings.control.enabled_on_startup is False
    assert settings.tracking.max_hands in (1, 2)
    assert settings.ml.model_path.endswith(".joblib")


def test_safety_defaults_are_secure() -> None:
    settings = load_settings(PROJECT_ROOT / "config/settings.yaml")

    assert settings.safety.pyautogui_failsafe is True
    assert settings.safety.dangerous_action_confirmation is True
    assert settings.control.enabled_on_startup is False


def test_data_and_model_paths_are_local() -> None:
    settings = load_settings(PROJECT_ROOT / "config/settings.yaml")

    assert settings.data_collection.dataset_path.startswith("data/")
    assert settings.ml.model_path.startswith("models/")
    assert settings.diagnostics.log_path.startswith("logs/")