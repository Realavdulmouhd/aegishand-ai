from __future__ import annotations

from aegishand.core.events import SafetyDecision
from aegishand.core.types import RiskLevel, SafetyState
from aegishand.intent.intent_types import ResolvedIntent
from aegishand.runtime.session_context import SessionContext
from aegishand.safety.action_policy import ActionPolicy


class SafetyGate:
    def __init__(
        self,
        context: SessionContext,
    ) -> None:
        self.context = context
        self.policy_engine = ActionPolicy()

    def evaluate(
        self,
        intent: ResolvedIntent,
    ) -> SafetyDecision:

        if (
            self.context.safety_state
            == SafetyState.EMERGENCY_STOPPED
        ):
            return SafetyDecision(
                allowed=False,
                reason="Emergency stop active",
                risk_level=RiskLevel.BLOCKED,
            )

        if not self.context.control_enabled:
            return SafetyDecision(
                allowed=False,
                reason="Control permission not enabled",
                risk_level=RiskLevel.BLOCKED,
            )

        policy = self.policy_engine.get_policy(
            intent.intent.value
        )

        return SafetyDecision(
            allowed=True,
            reason="Action approved",
            risk_level=RiskLevel(
                policy.get("risk", "low")
            ),
            cooldown_remaining_ms=policy.get(
                "cooldown_ms",
                0,
            ),
        )