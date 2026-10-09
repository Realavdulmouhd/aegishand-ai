# Security

AegisHand AI can issue operating system commands after user permission. For testing, start in preview mode and avoid running the application with elevated privileges.

## Boundaries

Camera processing is local by default. The project is not designed to record credentials, capture keystrokes, or transmit webcam footage.

Desktop control requires explicit permission. Emergency stop, active mode checks, cooldowns, and PyAutoGUI fail-safe behavior are important protections. They are experimental and must be tested under real operating conditions, including loss of tracking or window focus.

Do not commit local landmark datasets, webcam captures, trained models, diagnostic logs, calibration records, or credentials.

## Reporting a problem

Please contact the maintainer privately through [GitHub](https://github.com/Realavdulmouhd) for vulnerabilities or unsafe desktop-control behavior. Do not include private user data or malicious reproduction steps in public issues.

The repository is under active development. It has not undergone an independent security audit.
