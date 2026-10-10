from __future__ import annotations

import yaml
from pathlib import Path


class UserCalibration:
    def __init__(
        self,
        calibration_path: str = "config/calibration.yaml",
    ) -> None:
        self.calibration_path = Path(
            calibration_path
        )

        with open(self.calibration_path, "r") as file:
            self.data = yaml.safe_load(file)

    def dominant_hand(self) -> str:
        return self.data.get(
            "dominant_hand",
            "right",
        )

    def smoothing_factor(self) -> float:
        return self.data["gesture_preferences"].get(
            "smoothing_factor",
            0.7,
        )