from __future__ import annotations

from aegishand.intent.intent_types import (
    ResolvedIntent,
)


class SandboxController:
    """
    Simulates execution without touching
    the operating system.
    """

    def simulate(
        self,
        intent: ResolvedIntent,
    ) -> str:
        return (
            f"[SANDBOX] Intent simulated: "
            f"{intent.intent.value}"
        )