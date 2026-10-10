from __future__ import annotations

from enum import Enum


class InteractionState(str, Enum):
    IDLE = "idle"
    ARMED = "armed"
    CONTROLLING = "controlling"
    DRAGGING = "dragging"
    PAUSED = "paused"
    LOCKED = "locked"