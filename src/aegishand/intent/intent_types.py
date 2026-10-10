from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IntentType(str, Enum):
    MOVE_CURSOR = "move_cursor"
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DRAG = "drag"
    SCROLL = "scroll"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    NEXT_SLIDE = "next_slide"
    PREVIOUS_SLIDE = "previous_slide"
    PAUSE_CONTROL = "pause_control"


@dataclass(frozen=True)
class ResolvedIntent:
    intent: IntentType
    confidence: float
    source_gesture: str
    mode: str