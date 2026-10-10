from aegishand.core.events import StableGesture
from aegishand.core.types import Handedness
from aegishand.intent.intent_resolver import IntentResolver

resolver = IntentResolver()

gesture = StableGesture(
    name="pinch",
    confidence=0.95,
    hold_time_ms=300,
    handedness=Handedness.RIGHT,
)

intent = resolver.resolve(
    gesture,
    current_mode="mouse",
)

print(intent)