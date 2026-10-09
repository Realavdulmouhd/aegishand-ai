# AegisHand AI

**Your hand proposes the command. The system decides whether it is safe to execute.**

I began working on AegisHand AI in 2024 while studying cybersecurity at Bayero University Kano (BUK), Nigeria. My growing interest in software engineering pushed me toward a question that seemed simple at first: could I interact with my computer naturally, using only my hand and a webcam?

The first challenge was recognizing hand movements. The harder problem came afterward. A camera can misread a gesture, a hand can briefly leave the frame, and a single unintended click can be enough to ruin the experience. I became more interested in the decisions between recognition and execution than in adding another flashy gesture.

That is what AegisHand AI is about today: **hand-based computer interaction built around user permission, predictable behavior, and visible safety decisions.**

The work continued as my academic path moved beyond BUK and I pursued software engineering studies abroad. I have kept developing it as a practical meeting point between computer vision, cybersecurity, accessibility, and human-computer interaction.

## The idea that changed the project

A basic gesture controller asks: *Which gesture should perform a click?*

AegisHand AI asks a different question: *When is there enough evidence that the user intends to click, and should the computer allow it?*

The existing application combines hand tracking, gesture recognition, profiles, mode-aware desktop commands, and safety controls. A newer interaction engine is being developed to formalize this further:

```text
Camera frame
    |
Hand landmarks
    |
Gesture observation
    |
Temporal validation
    |
Intent proposal
    |
Safety policy
    |
Permission-aware execution
    |
Audit event and visible feedback
```

The full intent-first pipeline is an ongoing architectural upgrade. Some modules exist independently, but they should not be described as enforcing the live desktop path until integration and tests prove it.

## What is in the codebase

| Area | Current implementation |
| --- | --- |
| Vision | OpenCV webcam capture and MediaPipe hand landmarks |
| Recognition | Rule-based hand gestures, optional trained landmark classifier |
| Interaction | Cursor movement, clicks, drag, scroll, modes and profiles |
| System controls | Media keys, volume, supported brightness controls, presentation shortcuts |
| Visual tools | Hand skeleton HUD, local air drawing |
| Safety | Explicit desktop-control permission, pause, emergency stop, fail-safe corner, cooldowns |
| User interface | Tkinter control panel and terminal workflows |
| Diagnostics | Local event logging and development checks |
| Research work | Typed runtime events, gesture stabilization, intent resolution, safety policy, calibration and interaction grammar foundations |

This is an experimental Windows-first application. Hardware support, focus behavior, lighting, and recognition quality affect results. An implemented module is not the same thing as a validated real-world capability.

## Run it locally

Start in the repository directory with Python and PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Python 3.11 is a suggested starting point. Use a version supported by the MediaPipe release in your environment.

### Inspect before controlling

```powershell
python main.py --camera
python main.py --hands
python main.py --cursor
```

`--cursor` is a preview path. It should not move the real mouse or send desktop commands.

### Start the dashboard

```powershell
python main.py --dashboard
```

### Permit desktop control

```powershell
python main.py --cursor --control
```

The application requests the phrase `ENABLE AEGISHAND CONTROL` before allowing real actions. Keep the preview window visible, test with non-sensitive applications, and avoid running the program as administrator.

Within the focused OpenCV window, `E` triggers emergency stop, `P` pauses or resumes when allowed, and `Q` or `Esc` exits. Keyboard shortcuts depend on focus and are not a substitute for independent system-wide emergency controls. PyAutoGUI fail-safe corner behavior must remain enabled.

## Profiles change the interaction

Gesture mappings live in `config/gestures.yaml`. The project includes default, media, accessibility, and developer profiles. Modes separate interactions such as mouse navigation, scrolling, presentations, drawing, and security operations.

```powershell
python main.py --cursor --profile accessibility
python main.py --cursor --profile media
```

The accessibility profile currently reduces the number of available gestures. That is a useful beginning, not proof of accessibility for users with tremors or limited mobility. Dwell preferences, calibration, and usability studies need dedicated evaluation.

## Optional machine learning

The base system does not require a trained model. A separate workflow extracts normalized hand-landmark features into a local CSV dataset:

```powershell
python main.py --collect open_palm
python main.py --collect fist
python main.py --collect index_point
python main.py --collect peace
python main.py --collect three_fingers
python main.py --collect pinch
python main.py --train-gestures
python main.py --cursor --ml
```

The collector is intended to save numerical landmark features rather than webcam pictures. These features can still reveal personal characteristics, so local datasets are excluded from the public repository.

A random split of adjacent webcam frames can overstate performance. I will not report a recognition accuracy figure without an independent evaluation protocol.

## A few rules I refuse to compromise

**Recognition is not authorization.** A recognizer should propose what it sees; it should not directly call PyAutoGUI.

**Control must be obvious.** A user should know whether the program is only observing or is permitted to affect the desktop.

**Privacy is a design constraint.** Webcam processing is local by default. The project does not intentionally upload frames or collect credentials. Logs and saved datasets still require care.

**An emergency exit matters more than a clever gesture.** Safety mechanisms need real hardware tests, especially when tracking drops, the window loses focus, or OS automation fails.

**A green test run is not a usability study.** Automated tests verify specified behavior. They cannot establish false-trigger rates, emergency-stop response times, or long-session comfort on their own.

Further details are in the project's `docs/` directory and `SECURITY.md`.

## Verify the build

```powershell
python -m pytest -q
python tools\health_check.py
```

Do not assume either command passes on a fresh checkout until the current commit has been tested. The health check covers project files and configuration; it does not measure recognition reliability.

## Where the code lives

```text
config/                   Gesture profiles and runtime settings
src/aegishand/
  camera/                 Camera input
  vision/                 Landmarks and geometry
  gestures/               Rule-based and optional ML recognition
  modes/                  Interaction mode selection
  profiles/               Configurable gesture-action mapping
  safety/                 Permission, emergency and cooldown logic
  control/                Mouse and OS action interfaces
  runtime/                Application orchestration
  ui/                     On-camera status overlay
  drawing/                Local air canvas
  dashboard/              Desktop launcher
  diagnostics/            Local operational events
tests/                    Automated checks
tools/                    Project verification scripts
docs/                     Design notes and guides
```

The v2 `core/`, `intent/`, `interaction/`, `sandbox/`, and `calibration/` work is being introduced incrementally. Any folder or interface that has not yet been wired into the active runtime is still foundation work.

## What still needs engineering attention

My priority is no longer adding the largest number of gestures. It is proving that the existing ones can be trusted.

Next work includes temporal gesture stability, intent-first policy enforcement across every control path, safer drag-release behavior, calibration across different users and cameras, structured performance metrics, reliable sandbox demonstrations, and independent accessibility testing.

The long-term goal is a reusable hand interaction system that developers can understand and extend without weakening its safety boundary.

## About me

I'm **Abdurrahman Suleiman**, also known as [Realavdulmouhd](https://github.com/Realavdulmouhd). My route into this project began with cybersecurity studies at BUK Kano in 2024 and a strong interest in software engineering. I have continued the work while studying abroad.

AegisHand AI reflects the kind of engineering I want to keep doing: systems that are interesting to build, but more importantly, understandable, testable, and respectful of the person using them.

**Status:** Active development. Experimental software, not a certified assistive technology or a production security control.
