from aegishand.core.events import StableGesture
from aegishand.core.types import Handedness
from aegishand.intent.intent_resolver import IntentResolver

from aegishand.runtime.session_context import SessionContext
from aegishand.safety.safety_gate import SafetyGate

from aegishand.sandbox.sandbox_controller import SandboxController

from aegishand.interaction.gesture_grammar import GestureGrammar


print("=" * 60)
print("STEP 1 — INTENT RESOLUTION")
print("=" * 60)

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


print()
print("=" * 60)
print("STEP 2 — SAFETY GATE")
print("=" * 60)

context = SessionContext()
context.control_enabled = True

gate = SafetyGate(context)

decision = gate.evaluate(intent)

print(decision)


print()
print("=" * 60)
print("STEP 3 — SANDBOX MODE")
print("=" * 60)

sandbox = SandboxController()

print(
    sandbox.simulate(intent)
)


print()
print("=" * 60)
print("STEP 4 — INTERACTION GRAMMAR")
print("=" * 60)

grammar = GestureGrammar()

print(
    grammar.transition("open_palm")
)

print(
    grammar.transition("index_point")
)
