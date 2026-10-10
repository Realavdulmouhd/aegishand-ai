from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_core_project_files_exist() -> None:
    required_paths = [
        "main.py",
        "requirements.txt",
        "config/settings.yaml",
        "config/gestures.yaml",
        "src/aegishand/__init__.py",
        "src/aegishand/camera/camera_stream.py",
        "src/aegishand/vision/hand_tracker.py",
        "src/aegishand/gestures/rule_based_recognizer.py",
        "src/aegishand/gestures/ml_recognizer.py",
        "src/aegishand/control/action_dispatcher.py",
        "src/aegishand/safety/safety_manager.py",
        "src/aegishand/modes/mode_manager.py",
        "src/aegishand/ui/hud.py",
    ]

    for relative_path in required_paths:
        assert (PROJECT_ROOT / relative_path).exists(), f"Missing required path: {relative_path}"


def test_documentation_folder_exists() -> None:
    assert (PROJECT_ROOT / "docs").exists()


def test_tests_folder_exists() -> None:
    assert (PROJECT_ROOT / "tests").exists()