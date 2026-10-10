from __future__ import annotations

from dataclasses import dataclass, field

from aegishand.core.types import RuntimeStatus, SafetyState


@dataclass
class SessionContext:
    control_enabled: bool = False
    current_mode: str = "mouse"
    active_profile: str = "default"
    safety_state: SafetyState = SafetyState.SANDBOX

    detected_gesture: str = "none"
    gesture_confidence: float = 0.0

    latest_fps: float = 0.0

    warnings: list[str] = field(default_factory=list)

    def get_runtime_status(self) -> RuntimeStatus:
        return RuntimeStatus(
            control_enabled=self.control_enabled,
            safety_state=self.safety_state,
            current_mode=self.current_mode,
            active_profile=self.active_profile,
        )