from __future__ import annotations

from aegishand.core.events import (
    GestureCandidate,
    IntentEvent,
    SafetyDecision,
)
from aegishand.runtime.session_context import SessionContext


class RuntimePipeline:
    """
    Coordinates high-level runtime flow.

    This class intentionally does not contain
    gesture math, rendering logic, or OS actions.

    Its responsibility is orchestration.
    """

    def __init__(self, context: SessionContext) -> None:
        self.context = context

    def update_gesture(
        self,
        candidate: GestureCandidate,
    ) -> None:
        self.context.detected_gesture = candidate.name
        self.context.gesture_confidence = candidate.confidence

    def evaluate_intent(
        self,
        intent: IntentEvent,
        decision: SafetyDecision,
    ) -> bool:
        if not decision.allowed:
            self.context.warnings.append(
                f"Blocked action: {decision.reason}"
            )
            return False

        return True