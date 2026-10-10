from __future__ import annotations

from dataclasses import dataclass, replace
from math import sqrt
from typing import Any


class MouseControllerError(RuntimeError):
    """Raised when desktop cursor control cannot run safely."""


@dataclass(frozen=True)
class CursorControllerConfig:
    screen_width: int
    screen_height: int
    smoothing_factor: float
    dead_zone_pixels: int
    edge_protection_pixels: int
    mirror_cursor: bool

    def validate(self) -> None:
        if self.screen_width <= 0 or self.screen_height <= 0:
            raise MouseControllerError("Screen width and height must be positive.")

        if not 0.0 < self.smoothing_factor <= 1.0:
            raise MouseControllerError("Smoothing factor must be between 0.0 and 1.0.")

        if self.dead_zone_pixels < 0:
            raise MouseControllerError("Dead zone cannot be negative.")

        if self.edge_protection_pixels < 0:
            raise MouseControllerError("Edge protection cannot be negative.")


@dataclass(frozen=True)
class CursorPosition:
    x: int
    y: int


class CursorSmoother:
    def __init__(self, smoothing_factor: float, dead_zone_pixels: int) -> None:
        self.smoothing_factor = smoothing_factor
        self.dead_zone_pixels = dead_zone_pixels
        self._current: CursorPosition | None = None

    def update(self, target: CursorPosition) -> CursorPosition:
        if self._current is None:
            self._current = target
            return target

        distance = sqrt(
            ((target.x - self._current.x) ** 2)
            + ((target.y - self._current.y) ** 2)
        )

        if distance < self.dead_zone_pixels:
            return self._current

        smoothed_x = int(
            self._current.x
            + ((target.x - self._current.x) * self.smoothing_factor)
        )
        smoothed_y = int(
            self._current.y
            + ((target.y - self._current.y) * self.smoothing_factor)
        )

        self._current = CursorPosition(x=smoothed_x, y=smoothed_y)
        return self._current

    def reset(self) -> None:
        self._current = None


def map_normalized_to_screen(
    normalized_x: float,
    normalized_y: float,
    config: CursorControllerConfig,
) -> CursorPosition:
    config.validate()

    x = 1.0 - normalized_x if config.mirror_cursor else normalized_x
    y = normalized_y

    raw_x = int(x * config.screen_width)
    raw_y = int(y * config.screen_height)

    min_x = config.edge_protection_pixels
    min_y = config.edge_protection_pixels
    max_x = config.screen_width - config.edge_protection_pixels - 1
    max_y = config.screen_height - config.edge_protection_pixels - 1

    return CursorPosition(
        x=_clamp(raw_x, min_x, max_x),
        y=_clamp(raw_y, min_y, max_y),
    )


class MouseController:
    def __init__(
        self,
        config: CursorControllerConfig,
        desktop_control_enabled: bool,
        pyautogui_failsafe: bool = True,
    ) -> None:
        config.validate()

        self.config = config
        self.desktop_control_enabled = desktop_control_enabled
        self.drag_active = False
        self._pyautogui: Any | None = None
        self._smoother = CursorSmoother(
            smoothing_factor=config.smoothing_factor,
            dead_zone_pixels=config.dead_zone_pixels,
        )

        if desktop_control_enabled:
            self._enable_pyautogui(pyautogui_failsafe=pyautogui_failsafe)

    def preview_target(self, normalized_x: float, normalized_y: float) -> CursorPosition:
        target = map_normalized_to_screen(
            normalized_x=normalized_x,
            normalized_y=normalized_y,
            config=self.config,
        )

        return self._smoother.update(target)

    def move_to(self, normalized_x: float, normalized_y: float) -> CursorPosition:
        cursor_position = self.preview_target(
            normalized_x=normalized_x,
            normalized_y=normalized_y,
        )

        if self.desktop_control_enabled:
            self._require_pyautogui().moveTo(cursor_position.x, cursor_position.y, duration=0)

        return cursor_position

    def left_click(self) -> bool:
        if not self.desktop_control_enabled:
            return False

        self._require_pyautogui().click(button="left")
        return True

    def right_click(self) -> bool:
        if not self.desktop_control_enabled:
            return False

        self._require_pyautogui().click(button="right")
        return True

    def start_drag(self) -> bool:
        if self.drag_active:
            return False

        self.drag_active = True

        if self.desktop_control_enabled:
            self._require_pyautogui().mouseDown(button="left")

        return True

    def update_drag(self, normalized_x: float, normalized_y: float) -> CursorPosition:
        return self.move_to(
            normalized_x=normalized_x,
            normalized_y=normalized_y,
        )

    def end_drag(self) -> bool:
        if not self.drag_active:
            return False

        self.drag_active = False

        if self.desktop_control_enabled:
            self._require_pyautogui().mouseUp(button="left")

        return True

    def scroll(self, amount: int) -> bool:
        if amount == 0:
            return False

        if not self.desktop_control_enabled:
            return False

        self._require_pyautogui().scroll(amount)
        return True

    def reset_smoothing(self) -> None:
        self._smoother.reset()

    def _enable_pyautogui(self, pyautogui_failsafe: bool) -> None:
        try:
            import pyautogui
        except ImportError as exc:
            raise MouseControllerError("PyAutoGUI is not installed. Run: pip install -r requirements.txt") from exc

        pyautogui.FAILSAFE = pyautogui_failsafe
        pyautogui.PAUSE = 0

        screen_width, screen_height = pyautogui.size()

        self.config = replace(
            self.config,
            screen_width=int(screen_width),
            screen_height=int(screen_height),
        )

        self._pyautogui = pyautogui

    def _require_pyautogui(self) -> Any:
        if self._pyautogui is None:
            raise MouseControllerError("PyAutoGUI is not ready for desktop control.")

        return self._pyautogui


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))