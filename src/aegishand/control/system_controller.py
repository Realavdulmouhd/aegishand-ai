from __future__ import annotations

import platform
from dataclasses import dataclass
from typing import Any


class SystemControllerError(RuntimeError):
    """Raised when system control cannot be prepared safely."""


@dataclass(frozen=True)
class SystemControllerConfig:
    volume_step: int
    brightness_step: int
    allow_media_keys: bool
    allow_brightness_control: bool
    allow_security_lock: bool = True

    def validate(self) -> None:
        if self.volume_step < 1 or self.volume_step > 20:
            raise SystemControllerError("Volume step must be between 1 and 20.")

        if self.brightness_step < 1 or self.brightness_step > 25:
            raise SystemControllerError("Brightness step must be between 1 and 25.")


@dataclass(frozen=True)
class SystemActionResult:
    executed: bool
    message: str


class SystemController:
    def __init__(
        self,
        config: SystemControllerConfig,
        desktop_control_enabled: bool,
    ) -> None:
        config.validate()

        self.config = config
        self.desktop_control_enabled = desktop_control_enabled
        self.platform_name = platform.system()
        self._pyautogui: Any | None = None

        if desktop_control_enabled:
            self._prepare_pyautogui()

    def play_pause(self) -> SystemActionResult:
        return self._press_media_key("playpause", "Play or pause")

    def next_track(self) -> SystemActionResult:
        return self._press_media_key("nexttrack", "Next track")

    def previous_track(self) -> SystemActionResult:
        return self._press_media_key("prevtrack", "Previous track")

    def mute(self) -> SystemActionResult:
        return self._press_media_key("volumemute", "Mute or unmute")

    def volume_up(self) -> SystemActionResult:
        return self._repeat_media_key("volumeup", self.config.volume_step, "Volume up")

    def volume_down(self) -> SystemActionResult:
        return self._repeat_media_key("volumedown", self.config.volume_step, "Volume down")

    def brightness_up(self) -> SystemActionResult:
        return self._change_brightness(self.config.brightness_step)

    def brightness_down(self) -> SystemActionResult:
        return self._change_brightness(-self.config.brightness_step)

    def presentation_start(self) -> SystemActionResult:
        return self._press_hotkey(("f5",), "Presentation start")

    def presentation_next(self) -> SystemActionResult:
        return self._press_media_key("right", "Next slide")

    def presentation_previous(self) -> SystemActionResult:
        return self._press_media_key("left", "Previous slide")

    def presentation_blank(self) -> SystemActionResult:
        return self._press_media_key("b", "Presentation blank screen")

    def presentation_unblank(self) -> SystemActionResult:
        return self._press_media_key("b", "Presentation unblank screen")

    def presentation_zoom_in(self) -> SystemActionResult:
        return self._press_hotkey(("ctrl", "+"), "Presentation zoom in")

    def presentation_zoom_out(self) -> SystemActionResult:
        return self._press_hotkey(("ctrl", "-"), "Presentation zoom out")

    def security_pause(self) -> SystemActionResult:
        return SystemActionResult(
            executed=False,
            message="Security pause is handled by the safety manager.",
        )

    def security_resume(self) -> SystemActionResult:
        return SystemActionResult(
            executed=False,
            message="Security resume is handled by the safety manager.",
        )

    def security_lock(self) -> SystemActionResult:
        if not self.config.allow_security_lock:
            return SystemActionResult(
                executed=False,
                message="Security lock is disabled in settings.",
            )

        if not self.desktop_control_enabled:
            return SystemActionResult(
                executed=False,
                message="Security lock previewed only.",
            )

        if self.platform_name == "Windows":
            return self._press_hotkey(("win", "l"), "Security lock")

        if self.platform_name == "Darwin":
            return self._press_hotkey(("ctrl", "command", "q"), "Security lock")

        return SystemActionResult(
            executed=False,
            message=f"Security lock is not implemented for {self.platform_name}.",
        )

    def _press_media_key(self, key_name: str, label: str) -> SystemActionResult:
        if not self.config.allow_media_keys:
            return SystemActionResult(
                executed=False,
                message=f"{label} is disabled in settings.",
            )

        if not self.desktop_control_enabled:
            return SystemActionResult(
                executed=False,
                message=f"{label} previewed only.",
            )

        self._require_pyautogui().press(key_name)

        return SystemActionResult(
            executed=True,
            message=f"{label} executed.",
        )

    def _press_hotkey(self, keys: tuple[str, ...], label: str) -> SystemActionResult:
        if not self.config.allow_media_keys:
            return SystemActionResult(
                executed=False,
                message=f"{label} is disabled in settings.",
            )

        if not self.desktop_control_enabled:
            return SystemActionResult(
                executed=False,
                message=f"{label} previewed only.",
            )

        pyautogui = self._require_pyautogui()

        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)

        return SystemActionResult(
            executed=True,
            message=f"{label} executed.",
        )

    def _repeat_media_key(
        self,
        key_name: str,
        count: int,
        label: str,
    ) -> SystemActionResult:
        if not self.config.allow_media_keys:
            return SystemActionResult(
                executed=False,
                message=f"{label} is disabled in settings.",
            )

        if not self.desktop_control_enabled:
            return SystemActionResult(
                executed=False,
                message=f"{label} previewed only.",
            )

        pyautogui = self._require_pyautogui()

        for _ in range(count):
            pyautogui.press(key_name)

        return SystemActionResult(
            executed=True,
            message=f"{label} executed.",
        )

    def _change_brightness(self, delta: int) -> SystemActionResult:
        label = "Brightness up" if delta > 0 else "Brightness down"

        if not self.config.allow_brightness_control:
            return SystemActionResult(
                executed=False,
                message=f"{label} is disabled in settings.",
            )

        if not self.desktop_control_enabled:
            return SystemActionResult(
                executed=False,
                message=f"{label} previewed only.",
            )

        try:
            import screen_brightness_control as brightness_control
        except ImportError:
            return SystemActionResult(
                executed=False,
                message="Brightness package is not installed.",
            )

        try:
            current = brightness_control.get_brightness()
            current_value = _extract_brightness_value(current)
            next_value = _clamp(current_value + delta, 0, 100)
            brightness_control.set_brightness(next_value)

            return SystemActionResult(
                executed=True,
                message=f"{label} executed. Brightness set to {next_value}%.",
            )
        except Exception as exc:
            return SystemActionResult(
                executed=False,
                message=f"Brightness control is not supported here: {exc}",
            )

    def _prepare_pyautogui(self) -> None:
        try:
            import pyautogui
        except ImportError as exc:
            raise SystemControllerError(
                "PyAutoGUI is not installed. Run: python -m pip install -r requirements.txt"
            ) from exc

        pyautogui.PAUSE = 0
        self._pyautogui = pyautogui

    def _require_pyautogui(self) -> Any:
        if self._pyautogui is None:
            raise SystemControllerError("PyAutoGUI is not ready for system control.")

        return self._pyautogui


def _extract_brightness_value(value: Any) -> int:
    if isinstance(value, list):
        if not value:
            return 50

        return int(value[0])

    return int(value)


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))