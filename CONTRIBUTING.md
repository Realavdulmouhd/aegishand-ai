# Contributing

Good contributions to AegisHand AI make the interaction more reliable, predictable, or easier to understand. Adding gestures is less important than proving that the existing ones behave safely.

## Before changing code

Read the README and the relevant module first. Keep capture, recognition, intent resolution, safety decisions, and desktop execution separate.

A recognizer should not call PyAutoGUI. New desktop actions must respect explicit permission, the active mode, emergency stop, and cooldown behavior.

Work in a focused branch, add tests when possible, and document hardware-specific behavior rather than assuming it works everywhere.

Run:

```powershell
python -m pytest -q
```

Explain the behavior you tested and what remains unverified. Do not commit credentials, raw images, local feature datasets, or runtime logs.

When updating the documentation, write in your own technical voice and distinguish completed work from future plans.
