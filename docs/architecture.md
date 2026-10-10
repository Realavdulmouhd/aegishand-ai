# AegisHand AI Architecture

AegisHand AI follows a safety-first pipeline:

Camera → Vision → Gesture Recognition → Mode Manager → Safety Manager → Action Dispatcher → Desktop Action

This structure prevents raw gesture detection from directly controlling the computer.

## Current runtime flow

At Priority 7, the system has this working flow:

CameraStream → MediaPipeHandTracker → Landmark Utilities → FingerStateDetector → RuleBasedGestureRecognizer → HUD → Optional MouseController

## Why the structure is strong

The camera module only owns webcam access.

The vision module only owns hand detection and landmark extraction.

The gesture module interprets finger states and classifies gestures.

The HUD module visualizes status without controlling the system.

The control module maps hand position to cursor position, but real cursor movement only happens when permission is granted.

The safety manager decides whether desktop actions are allowed.

This separation keeps the project maintainable, testable, and defendable.

## Current safety boundary

Desktop control is still disabled by default.

The command:

```bash
python main.py --cursor