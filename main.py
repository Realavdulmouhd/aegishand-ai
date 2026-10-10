from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from aegishand.camera.camera_stream import (
    CameraStreamConfig,
    CameraStreamError,
    run_camera_preview,
)
from aegishand.configuration.settings_loader import Settings, SettingsError, load_settings
from aegishand.control.mouse_controller import CursorControllerConfig, MouseController, MouseControllerError
from aegishand.control.system_controller import (
    SystemController,
    SystemControllerConfig,
    SystemControllerError,
)
from aegishand.diagnostics.app_logger import build_logger
from aegishand.diagnostics.event_logger import DiagnosticEventLogger
from aegishand.drawing.air_canvas import AirCanvas, AirCanvasConfig
from aegishand.gestures.rule_based_recognizer import RuleBasedGestureRecognizer
from aegishand.gestures.two_hand_recognizer import TwoHandGestureRecognizer
from aegishand.modes.mode_manager import ModeManager
from aegishand.profiles.profile_manager import ProfileError, ProfileManager
from aegishand.runtime.gesture_runtime import run_gesture_runtime
from aegishand.safety.cooldown import CooldownManager
from aegishand.safety.safety_manager import SafetyManager
from aegishand.ui.hud import ProfessionalHUD
from aegishand.vision.hand_tracker import HandTrackerConfig, HandTrackerError


PERMISSION_PHRASE = "ENABLE AEGISHAND CONTROL"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="AegisHand AI",
        description="Secure webcam-based hand gesture control platform.",
    )

    parser.add_argument("--camera", action="store_true", help="Start the raw OpenCV webcam preview.")
    parser.add_argument("--hands", action="store_true", help="Start hand tracking with HUD.")
    parser.add_argument("--cursor", action="store_true", help="Start gesture action runtime in preview mode.")
    parser.add_argument("--control", action="store_true", help="Allow real desktop control after explicit permission.")
    parser.add_argument("--profile", default=None, help="Gesture profile to load from config/gestures.yaml.")

    return parser.parse_args()


def show_startup_summary(settings: Settings, profile_manager: ProfileManager) -> None:
    console = Console()

    mode_manager = ModeManager()
    cooldown_manager = CooldownManager(default_seconds=settings.safety.action_cooldown_seconds)
    safety_manager = SafetyManager(
        safe_mode=settings.runtime.safe_mode,
        require_permission=settings.runtime.require_control_permission,
        control_enabled=settings.control.enabled_on_startup,
    )

    console.print(
        Panel.fit(
            "[bold]AegisHand AI[/bold]\n"
            "Secure real-time hand gesture control foundation is ready.",
            border_style="green",
        )
    )

    status_table = Table(title="Startup Status")
    status_table.add_column("Component", style="bold")
    status_table.add_column("Status")

    status_table.add_row("Configuration", "Loaded")
    status_table.add_row("Active Profile", profile_manager.active_profile_name)
    status_table.add_row("Available Profiles", ", ".join(profile_manager.list_profiles()))
    status_table.add_row("Logger", "Ready")
    status_table.add_row("Active Mode", mode_manager.get_mode().value)
    status_table.add_row("Cooldown", f"{cooldown_manager.default_seconds:.2f}s")
    status_table.add_row("Safe Mode", str(safety_manager.safe_mode))
    status_table.add_row("Control Permission", str(safety_manager.control_enabled))
    status_table.add_row("Presentation Mode", "Available")
    status_table.add_row("Air Drawing Mode", "Available")
    status_table.add_row("Two-Hand Gestures", "Available")
    status_table.add_row("Diagnostics", "Available")
    status_table.add_row("Desktop Control", "Disabled by default")

    console.print(status_table)

    console.print(
        "\n[bold yellow]Safety note:[/bold yellow] Real desktop control requires "
        "`--cursor --control` and a typed permission phrase."
    )


def build_camera_config(settings: Settings) -> CameraStreamConfig:
    return CameraStreamConfig(
        index=settings.camera.index,
        width=settings.camera.width,
        height=settings.camera.height,
        fps_limit=settings.camera.fps_limit,
    )


def build_hand_tracker_config(settings: Settings) -> HandTrackerConfig:
    return HandTrackerConfig(
        max_hands=settings.tracking.max_hands,
        min_detection_confidence=settings.tracking.min_detection_confidence,
        min_tracking_confidence=settings.tracking.min_tracking_confidence,
    )


def build_cursor_config(settings: Settings) -> CursorControllerConfig:
    return CursorControllerConfig(
        screen_width=settings.control.screen_width,
        screen_height=settings.control.screen_height,
        smoothing_factor=settings.control.smoothing_factor,
        dead_zone_pixels=settings.control.dead_zone_pixels,
        edge_protection_pixels=settings.control.edge_protection_pixels,
        mirror_cursor=settings.control.mirror_cursor,
    )


def build_system_controller_config(settings: Settings) -> SystemControllerConfig:
    return SystemControllerConfig(
        volume_step=settings.system_control.volume_step,
        brightness_step=settings.system_control.brightness_step,
        allow_media_keys=settings.system_control.allow_media_keys,
        allow_brightness_control=settings.system_control.allow_brightness_control,
    )


def build_air_canvas_config(settings: Settings) -> AirCanvasConfig:
    return AirCanvasConfig(
        brush_radius=settings.drawing.brush_radius,
        min_draw_distance=settings.drawing.min_draw_distance,
        overlay_opacity=settings.drawing.overlay_opacity,
    )


def confirm_desktop_control(console: Console) -> bool:
    console.print("\n[bold red]Desktop control is about to be enabled.[/bold red]")
    console.print("AegisHand AI may move, click, drag, scroll, control slides, media, volume, or brightness.")
    console.print("Air drawing remains local to the preview window.")
    console.print("Use keyboard [bold]E[/bold] for emergency stop. Use [bold]Q[/bold] or [bold]ESC[/bold] to close.")
    console.print("PyAutoGUI failsafe is enabled. Moving the mouse to a screen corner can stop control.")
    console.print(f"To continue, type exactly: [bold]{PERMISSION_PHRASE}[/bold]\n")

    typed = input("Permission phrase: ").strip()

    return typed == PERMISSION_PHRASE


def load_profile_manager(settings: Settings, requested_profile: str | None) -> ProfileManager:
    active_profile = requested_profile or settings.profiles.default_profile

    return ProfileManager.from_yaml(
        path=settings.profiles.gestures_path,
        active_profile=active_profile,
    )


def build_event_logger(settings: Settings) -> DiagnosticEventLogger:
    return DiagnosticEventLogger(
        enabled=settings.diagnostics.enabled,
        log_path=settings.diagnostics.log_path,
    )


def main() -> int:
    args = parse_args()
    console = Console()

    try:
        settings = load_settings()
        profile_manager = load_profile_manager(settings=settings, requested_profile=args.profile)
    except (SettingsError, ProfileError) as exc:
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        return 1

    logger = build_logger(
        name=settings.app.name,
        level=settings.logging.level,
        file_path=settings.logging.file_path if settings.logging.file_enabled else None,
    )

    event_logger = build_event_logger(settings)

    event_logger.log(
        "app_started",
        "Application started.",
        profile=profile_manager.active_profile_name,
        control_flag=args.control,
    )

    logger.info("Application started")
    logger.info("Active profile: %s", profile_manager.active_profile_name)

    show_startup_summary(settings, profile_manager)

    mode_manager = ModeManager()
    mode_manager.set_mode(profile_manager.active_profile.default_mode)

    cooldown_manager = CooldownManager(default_seconds=settings.safety.action_cooldown_seconds)

    safety_manager = SafetyManager(
        safe_mode=settings.runtime.safe_mode,
        require_permission=settings.runtime.require_control_permission,
        control_enabled=settings.control.enabled_on_startup,
    )

    try:
        if args.cursor:
            desktop_control_enabled = False

            if args.control:
                if not confirm_desktop_control(console):
                    console.print("[bold yellow]Permission was not granted. Desktop control stays OFF.[/bold yellow]")
                    logger.warning("Desktop control permission was rejected")
                    event_logger.log("permission_rejected", "Desktop control permission was rejected.")
                    return 1

                safety_manager.request_control_permission()
                desktop_control_enabled = True
                logger.info("Desktop control permission granted")
                event_logger.log("permission_granted", "Desktop control permission was granted.")

            mouse_controller = MouseController(
                config=build_cursor_config(settings),
                desktop_control_enabled=desktop_control_enabled,
                pyautogui_failsafe=settings.safety.pyautogui_failsafe,
            )

            system_controller = SystemController(
                config=build_system_controller_config(settings),
                desktop_control_enabled=desktop_control_enabled,
            )

            air_canvas = AirCanvas(
                config=build_air_canvas_config(settings),
            ) if settings.drawing.enabled else None

            console.print("\n[bold cyan]Starting AegisHand advanced runtime...[/bold cyan]")
            console.print(f"Active profile: [bold]{profile_manager.active_profile_name}[/bold]")
            console.print("Keys: E emergency, P pause/resume, M mode, 5 presentation, 6 drawing, C clear canvas, Q close.\n")

            run_gesture_runtime(
                camera_config=build_camera_config(settings),
                tracker_config=build_hand_tracker_config(settings),
                mode_manager=mode_manager,
                profile_manager=profile_manager,
                safety_manager=safety_manager,
                cooldown_manager=cooldown_manager,
                recognizer=RuleBasedGestureRecognizer(),
                two_hand_recognizer=TwoHandGestureRecognizer(),
                hud=ProfessionalHUD(),
                mouse_controller=mouse_controller,
                system_controller=system_controller,
                air_canvas=air_canvas,
                event_logger=event_logger,
                logger=logger,
            )

        elif args.hands:
            console.print("\n[bold cyan]Starting AegisHand hand tracking HUD...[/bold cyan]")
            console.print("Show your hand to the camera. Press [bold]Q[/bold] or [bold]ESC[/bold] to close.\n")

            run_gesture_runtime(
                camera_config=build_camera_config(settings),
                tracker_config=build_hand_tracker_config(settings),
                mode_manager=mode_manager,
                profile_manager=profile_manager,
                safety_manager=safety_manager,
                cooldown_manager=cooldown_manager,
                recognizer=RuleBasedGestureRecognizer(),
                two_hand_recognizer=TwoHandGestureRecognizer(),
                hud=ProfessionalHUD(),
                mouse_controller=None,
                system_controller=None,
                air_canvas=AirCanvas(config=build_air_canvas_config(settings)) if settings.drawing.enabled else None,
                event_logger=event_logger,
                logger=logger,
            )

        elif args.camera:
            console.print("\n[bold cyan]Starting raw camera preview...[/bold cyan]")
            console.print("Press [bold]Q[/bold] or [bold]ESC[/bold] inside the camera window to close it.\n")

            run_camera_preview(config=build_camera_config(settings), logger=logger)

    except (CameraStreamError, HandTrackerError, MouseControllerError, SystemControllerError) as exc:
        logger.error("Runtime error: %s", exc)
        event_logger.log("runtime_error", "Runtime error occurred.", error=str(exc))
        console.print(f"[bold red]Runtime error:[/bold red] {exc}")
        return 1

    logger.info("Application closed")
    event_logger.log("app_closed", "Application closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())