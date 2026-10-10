from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ControlMode(str, Enum):
    MOUSE = "mouse"
    SCROLL = "scroll"
    MEDIA = "media"
    VOLUME = "volume"
    DRAWING = "drawing"
    PRESENTATION = "presentation"
    ACCESSIBILITY = "accessibility"
    SECURITY = "security"
    DEVELOPER_DEMO = "developer_demo"


@dataclass
class ModeManager:
    active_mode: ControlMode = ControlMode.MOUSE
    ordered_modes: tuple[ControlMode, ...] = field(
        default_factory=lambda: (
            ControlMode.MOUSE,
            ControlMode.SCROLL,
            ControlMode.MEDIA,
            ControlMode.VOLUME,
            ControlMode.PRESENTATION,
            ControlMode.DRAWING,
            ControlMode.DEVELOPER_DEMO,
        )
    )

    def set_mode(self, mode: ControlMode | str) -> ControlMode:
        self.active_mode = self._normalize_mode(mode)
        return self.active_mode

    def get_mode(self) -> ControlMode:
        return self.active_mode

    def is_mode(self, mode: ControlMode | str) -> bool:
        return self.active_mode == self._normalize_mode(mode)

    def cycle_next(self) -> ControlMode:
        current_index = self.ordered_modes.index(self.active_mode)
        next_index = (current_index + 1) % len(self.ordered_modes)
        self.active_mode = self.ordered_modes[next_index]
        return self.active_mode

    def set_from_shortcut(self, key: str) -> ControlMode | None:
        shortcut_map = {
            "1": ControlMode.MOUSE,
            "2": ControlMode.SCROLL,
            "3": ControlMode.MEDIA,
            "4": ControlMode.VOLUME,
            "5": ControlMode.PRESENTATION,
            "6": ControlMode.DRAWING,
            "7": ControlMode.DEVELOPER_DEMO,
        }

        selected_mode = shortcut_map.get(key)

        if selected_mode is None:
            return None

        return self.set_mode(selected_mode)

    @staticmethod
    def _normalize_mode(mode: ControlMode | str) -> ControlMode:
        if isinstance(mode, ControlMode):
            return mode

        try:
            return ControlMode(mode)
        except ValueError as exc:
            valid_modes = ", ".join(item.value for item in ControlMode)
            raise ValueError(f"Unknown control mode '{mode}'. Valid modes: {valid_modes}") from exc