from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from aegishand.configuration.settings_loader import SettingsError, load_settings
from aegishand.profiles.profile_manager import ProfileError, ProfileManager


CORE_REQUIRED_PATHS = (
    "main.py",
    "requirements.txt",
    "config/settings.yaml",
    "config/gestures.yaml",
    "src/aegishand",
    "src/aegishand/camera/camera_stream.py",
    "src/aegishand/vision/hand_tracker.py",
    "src/aegishand/gestures/rule_based_recognizer.py",
    "src/aegishand/control/action_dispatcher.py",
    "src/aegishand/control/mouse_controller.py",
    "src/aegishand/control/system_controller.py",
    "src/aegishand/safety/safety_manager.py",
    "src/aegishand/modes/mode_manager.py",
    "src/aegishand/ui/hud.py",
    "docs",
    "tests",
)

OPTIONAL_ADVANCED_PATHS = (
    "src/aegishand/gestures/ml_recognizer.py",
    "src/aegishand/dashboard/control_panel.py",
    "src/aegishand/drawing/air_canvas.py",
    "src/aegishand/diagnostics/event_logger.py",
)


def main() -> int:
    console = Console()

    table = Table(title="AegisHand AI Health Check")
    table.add_column("Check", style="bold")
    table.add_column("Result")

    passed = True

    for relative_path in CORE_REQUIRED_PATHS:
        path = PROJECT_ROOT / relative_path
        exists = path.exists()
        table.add_row(relative_path, "OK" if exists else "Missing")

        if not exists:
            passed = False

    for relative_path in OPTIONAL_ADVANCED_PATHS:
        path = PROJECT_ROOT / relative_path
        exists = path.exists()
        table.add_row(relative_path, "OK" if exists else "Optional missing")

    try:
        settings = load_settings(PROJECT_ROOT / "config/settings.yaml")
        table.add_row("settings.yaml", "Loaded")
    except SettingsError as exc:
        table.add_row("settings.yaml", f"Failed: {exc}")
        passed = False
        settings = None

    if settings is not None:
        try:
            gestures_path = Path(settings.profiles.gestures_path)

            if not gestures_path.is_absolute():
                gestures_path = PROJECT_ROOT / gestures_path

            profile_manager = ProfileManager.from_yaml(
                path=gestures_path,
                active_profile=settings.profiles.default_profile,
            )

            table.add_row(
                "gesture profiles",
                f"Loaded: {', '.join(profile_manager.list_profiles())}",
            )
        except ProfileError as exc:
            table.add_row("gesture profiles", f"Failed: {exc}")
            passed = False

    for folder_name in ("logs", "data", "models"):
        folder = PROJECT_ROOT / folder_name
        folder.mkdir(exist_ok=True)
        table.add_row(f"{folder_name}/", "Ready")

    console.print(table)

    if passed:
        console.print("[bold green]Health check passed. Project foundation is ready.[/bold green]")
        return 0

    console.print("[bold red]Health check failed. Fix the missing or invalid parts above.[/bold red]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())