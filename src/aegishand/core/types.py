from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Handedness(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    UNKNOWN = "unknown"


class SafetyState(str, Enum):
    DISABLED = "disabled"
    SANDBOX = "sandbox"
    ARMED = "armed"
    ACTIVE = "active"
    PAUSED = "paused"
    EMERGENCY_STOPPED = "emergency_stopped"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float


@dataclass(frozen=True)
class Vector2D:
    dx: float
    dy: float


@dataclass(frozen=True)
class FrameTiming:
    frame_id: int
    delta_time: float
    fps: float


@dataclass(frozen=True)
class RuntimeStatus:
    control_enabled: bool
    safety_state: SafetyState
    current_mode: str
    active_profile: str