from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from aegishand.core.types import (
    Handedness,
    Point2D,
    RiskLevel,
)


@dataclass(frozen=True)
class HandObservation:
    frame_id: int
    timestamp: float
    handedness: Handedness
    landmarks: list[tuple[float, float]]
    palm_center: Point2D
    confidence: float
    is_visible: bool


@dataclass(frozen=True)
class GestureCandidate:
    name: str
    confidence: float
    handedness: Handedness
    duration_ms: int
    features: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class StableGesture:
    name: str
    confidence: float
    hold_time_ms: int
    handedness: Handedness


@dataclass(frozen=True)
class IntentEvent:
    mode: str
    gesture: str
    action: str
    confidence: float
    requires_confirmation: bool
    timestamp: float = field(default_factory=time)


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str
    risk_level: RiskLevel
    cooldown_remaining_ms: int = 0


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    details: dict[str, Any]
    timestamp: float = field(default_factory=time)