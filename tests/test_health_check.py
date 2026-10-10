import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_health_check_command_runs() -> None:
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "tools" / "health_check.py")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0
    assert "Health check" in result.stdout