from __future__ import annotations

import yaml
from pathlib import Path


class ActionPolicy:
    def __init__(
        self,
        config_path: str = "config/action_policies.yaml",
    ) -> None:
        self.config_path = Path(config_path)

        with open(self.config_path, "r") as file:
            self.data = yaml.safe_load(file)

    def get_policy(
        self,
        action_name: str,
    ) -> dict:
        return self.data["actions"].get(action_name, {})