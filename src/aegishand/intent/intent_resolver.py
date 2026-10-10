from __future__ import annotations

from aegishand.core.events import StableGesture
from aegishand.intent.intent_types import (
    IntentType,
    ResolvedIntent,
)


class IntentResolver:
    """
    Converts stable gestures into semantic intents.
    """

    def resolve(
        self,
        gesture: StableGesture,
        current_mode: str,
    ) -> ResolvedIntent | None:

        gesture_name = gesture.name

        if current_mode == "mouse":
            if gesture_name == "pinch":
                return ResolvedIntent(
                    intent=IntentType.LEFT_CLICK,
                    confidence=gesture.confidence,
                    source_gesture=gesture_name,
                    mode=current_mode,
                )

            if gesture_name == "peace":
                return ResolvedIntent(
                    intent=IntentType.RIGHT_CLICK,
                    confidence=gesture.confidence,
                    source_gesture=gesture_name,
                    mode=current_mode,
                )

        if current_mode == "presentation":
            if gesture_name == "swipe_right":
                return ResolvedIntent(
                    intent=IntentType.NEXT_SLIDE,
                    confidence=gesture.confidence,
                    source_gesture=gesture_name,
                    mode=current_mode,
                )

        return None