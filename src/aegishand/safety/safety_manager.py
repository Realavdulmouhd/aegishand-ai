from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SafetyManager:
    safe_mode: bool
    require_permission: bool
    control_enabled: bool = False
    emergency_stopped: bool = False
    last_block_reason: str = "none"

    def request_control_permission(self) -> None:
        if self.emergency_stopped:
            self.last_block_reason = "Emergency stop is active."
            return

        self.control_enabled = True
        self.last_block_reason = "none"

    def pause_control(self) -> None:
        self.control_enabled = False
        self.last_block_reason = "Control is paused."

    def resume_control(self) -> None:
        if self.emergency_stopped:
            self.last_block_reason = "Emergency stop is active. Restart the runtime to control again."
            return

        self.control_enabled = True
        self.last_block_reason = "none"

    def trigger_emergency_stop(self) -> None:
        self.emergency_stopped = True
        self.control_enabled = False
        self.last_block_reason = "Emergency stop was triggered."

    def can_execute_action(self, action_name: str, is_dangerous: bool = False) -> bool:
        if self.emergency_stopped:
            self.last_block_reason = f"Blocked '{action_name}' because emergency stop is active."
            return False

        if self.require_permission and not self.control_enabled:
            self.last_block_reason = f"Blocked '{action_name}' because control permission is not active."
            return False

        if self.safe_mode and is_dangerous:
            self.last_block_reason = f"Blocked dangerous action '{action_name}' while safe mode is active."
            return False

        self.last_block_reason = "none"
        return True