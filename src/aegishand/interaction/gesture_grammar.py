from __future__ import annotations

from aegishand.runtime.app_state import (
    InteractionState,
)


class GestureGrammar:
    """
    Defines legal interaction transitions.
    """

    def __init__(self) -> None:
        self.state = InteractionState.IDLE

    def transition(
        self,
        gesture_name: str,
    ) -> InteractionState:

        if (
            self.state == InteractionState.IDLE
            and gesture_name == "open_palm"
        ):
            self.state = (
                InteractionState.ARMED
            )

        elif (
            self.state
            == InteractionState.ARMED
            and gesture_name == "index_point"
        ):
            self.state = (
                InteractionState.CONTROLLING
            )

        elif (
            gesture_name == "stop"
        ):
            self.state = (
                InteractionState.PAUSED
            )

        return self.state