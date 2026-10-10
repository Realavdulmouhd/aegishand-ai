from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import yaml


class SettingsError(RuntimeError):
    """Raised when application settings cannot be loaded safely."""


@dataclass(frozen=True)
class AppSettings:
    name: str
    version: str
    environment: str


@dataclass(frozen=True)
class RuntimeSettings:
    debug: bool
    safe_mode: bool
    require_control_permission: bool


@dataclass(frozen=True)
class CameraSettings:
    index: int
    width: int
    height: int
    fps_limit: int


@dataclass(frozen=True)
class TrackingSettings:
    max_hands: int
    min_detection_confidence: float
    min_tracking_confidence: float


@dataclass(frozen=True)
class ControlSettings:
    enabled_on_startup: bool
    preferred_hand: str
    smoothing_factor: float
    dead_zone_pixels: int
    edge_protection_pixels: int
    screen_width: int
    screen_height: int
    mirror_cursor: bool


@dataclass(frozen=True)
class SystemControlSettings:
    volume_step: int
    brightness_step: int
    allow_media_keys: bool
    allow_brightness_control: bool
    allow_security_lock: bool


@dataclass(frozen=True)
class DrawingSettings:
    enabled: bool
    brush_radius: int
    min_draw_distance: int
    overlay_opacity: float


@dataclass(frozen=True)
class ProfileSettings:
    default_profile: str
    gestures_path: str


@dataclass(frozen=True)
class DiagnosticsSettings:
    enabled: bool
    log_path: str
    log_gestures: bool
    log_actions: bool
    log_mode_changes: bool


@dataclass(frozen=True)
class DataCollectionSettings:
    enabled: bool
    dataset_path: str


@dataclass(frozen=True)
class MLSettings:
    enabled: bool
    model_path: str
    min_training_samples: int


@dataclass(frozen=True)
class DashboardSettings:
    enabled: bool
    launch_new_terminal: bool


@dataclass(frozen=True)
class SafetySettings:
    emergency_key: str
    action_cooldown_seconds: float
    dangerous_action_confirmation: bool
    pyautogui_failsafe: bool
    pause_on_no_hand: bool


@dataclass(frozen=True)
class LoggingSettings:
    level: str
    file_enabled: bool
    file_path: str


@dataclass(frozen=True)
class Settings:
    app: AppSettings
    runtime: RuntimeSettings
    camera: CameraSettings
    tracking: TrackingSettings
    control: ControlSettings
    system_control: SystemControlSettings
    drawing: DrawingSettings
    profiles: ProfileSettings
    diagnostics: DiagnosticsSettings
    data_collection: DataCollectionSettings
    ml: MLSettings
    dashboard: DashboardSettings
    safety: SafetySettings
    logging: LoggingSettings


DEFAULTS: dict[str, dict[str, Any]] = {
    "app": {
        "name": "AegisHand AI",
        "version": "0.1.0",
        "environment": "development",
    },
    "runtime": {
        "debug": True,
        "safe_mode": True,
        "require_control_permission": True,
    },
    "camera": {
        "index": 0,
        "width": 1280,
        "height": 720,
        "fps_limit": 30,
    },
    "tracking": {
        "max_hands": 2,
        "min_detection_confidence": 0.70,
        "min_tracking_confidence": 0.70,
    },
    "control": {
        "enabled_on_startup": False,
        "preferred_hand": "right",
        "smoothing_factor": 0.35,
        "dead_zone_pixels": 8,
        "edge_protection_pixels": 24,
        "screen_width": 1920,
        "screen_height": 1080,
        "mirror_cursor": True,
    },
    "system_control": {
        "volume_step": 5,
        "brightness_step": 8,
        "allow_media_keys": True,
        "allow_brightness_control": True,
        "allow_security_lock": True,
    },
    "drawing": {
        "enabled": True,
        "brush_radius": 6,
        "min_draw_distance": 8,
        "overlay_opacity": 0.85,
    },
    "profiles": {
        "default_profile": "default",
        "gestures_path": "config/gestures.yaml",
    },
    "diagnostics": {
        "enabled": True,
        "log_path": "logs/events.jsonl",
        "log_gestures": True,
        "log_actions": True,
        "log_mode_changes": True,
    },
    "data_collection": {
        "enabled": True,
        "dataset_path": "data/gesture_samples.csv",
    },
    "ml": {
        "enabled": True,
        "model_path": "models/gesture_model.joblib",
        "min_training_samples": 20,
    },
    "dashboard": {
        "enabled": True,
        "launch_new_terminal": False,
    },
    "safety": {
        "emergency_key": "esc",
        "action_cooldown_seconds": 0.45,
        "dangerous_action_confirmation": True,
        "pyautogui_failsafe": True,
        "pause_on_no_hand": True,
    },
    "logging": {
        "level": "INFO",
        "file_enabled": True,
        "file_path": "logs/aegishand.log",
    },
}


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SettingsError(f"Settings file was not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except yaml.YAMLError as exc:
        raise SettingsError(f"Invalid YAML inside {path}") from exc

    if not isinstance(data, dict):
        raise SettingsError(f"Settings file must contain a YAML object: {path}")

    return data


def _section(data: dict[str, Any], section_name: str) -> dict[str, Any]:
    raw_section = data.get(section_name, {})

    if raw_section is None:
        raw_section = {}

    if not isinstance(raw_section, dict):
        raise SettingsError(f"Settings section '{section_name}' must be a YAML object.")

    merged = dict(DEFAULTS[section_name])
    merged.update(raw_section)
    return merged


def _build_dataclass(cls: type[Any], values: dict[str, Any], section_name: str) -> Any:
    allowed_fields = {field.name for field in fields(cls)}
    filtered = {
        key: value
        for key, value in values.items()
        if key in allowed_fields
    }

    missing = allowed_fields - filtered.keys()

    if missing:
        missing_list = ", ".join(sorted(missing))
        raise SettingsError(
            f"Settings section '{section_name}' is missing required field(s): {missing_list}"
        )

    try:
        return cls(**filtered)
    except TypeError as exc:
        raise SettingsError(
            f"Settings section '{section_name}' contains invalid values."
        ) from exc


def load_settings(path: str | Path = "config/settings.yaml") -> Settings:
    data = _read_yaml(Path(path))

    return Settings(
        app=_build_dataclass(AppSettings, _section(data, "app"), "app"),
        runtime=_build_dataclass(RuntimeSettings, _section(data, "runtime"), "runtime"),
        camera=_build_dataclass(CameraSettings, _section(data, "camera"), "camera"),
        tracking=_build_dataclass(TrackingSettings, _section(data, "tracking"), "tracking"),
        control=_build_dataclass(ControlSettings, _section(data, "control"), "control"),
        system_control=_build_dataclass(
            SystemControlSettings,
            _section(data, "system_control"),
            "system_control",
        ),
        drawing=_build_dataclass(DrawingSettings, _section(data, "drawing"), "drawing"),
        profiles=_build_dataclass(ProfileSettings, _section(data, "profiles"), "profiles"),
        diagnostics=_build_dataclass(
            DiagnosticsSettings,
            _section(data, "diagnostics"),
            "diagnostics",
        ),
        data_collection=_build_dataclass(
            DataCollectionSettings,
            _section(data, "data_collection"),
            "data_collection",
        ),
        ml=_build_dataclass(MLSettings, _section(data, "ml"), "ml"),
        dashboard=_build_dataclass(
            DashboardSettings,
            _section(data, "dashboard"),
            "dashboard",
        ),
        safety=_build_dataclass(SafetySettings, _section(data, "safety"), "safety"),
        logging=_build_dataclass(LoggingSettings, _section(data, "logging"), "logging"),
    )