from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ProfileError(RuntimeError):
    """Raised when gesture profiles cannot be loaded or resolved safely."""


@dataclass(frozen=True)
class GestureProfile:
    name: str
    description: str
    default_mode: str
    modes: dict[str, dict[str, str]]

    def __call__(self) -> GestureProfile:
        return self

    def get_actions_for_mode(self, mode: str) -> dict[str, str]:
        selected_mode = str(mode).strip().lower()
        return dict(self.modes.get(selected_mode, {}))

    def resolve_action(self, mode: str, gesture_name: str) -> str:
        selected_mode = str(mode).strip().lower()
        selected_gesture = str(gesture_name).strip().lower()

        actions = self.get_actions_for_mode(selected_mode)

        if selected_gesture in actions:
            return actions[selected_gesture]

        aliases = {
            "peace": ["peace", "peace_sign", "two_fingers", "two_finger"],
            "peace_sign": ["peace_sign", "peace", "two_fingers", "two_finger"],
            "two_fingers": ["two_fingers", "peace", "peace_sign", "two_finger"],
            "two_finger": ["two_finger", "two_fingers", "peace", "peace_sign"],
            "three_fingers": ["three_fingers", "three_finger"],
            "three_finger": ["three_finger", "three_fingers"],
            "index_point": ["index_point", "point", "pointing", "index_finger"],
            "point": ["point", "index_point", "pointing", "index_finger"],
            "pointing": ["pointing", "point", "index_point", "index_finger"],
            "index_finger": ["index_finger", "index_point", "point", "pointing"],
            "open_palm": ["open_palm", "palm", "five_fingers"],
            "palm": ["palm", "open_palm", "five_fingers"],
            "five_fingers": ["five_fingers", "open_palm", "palm"],
            "pinch": ["pinch", "pinch_start", "drag"],
            "pinch_start": ["pinch_start", "pinch", "drag"],
            "drag": ["drag", "pinch", "pinch_start"],
            "pinch_release": ["pinch_release", "release_pinch", "drag_release"],
            "release_pinch": ["release_pinch", "pinch_release", "drag_release"],
            "drag_release": ["drag_release", "pinch_release", "release_pinch"],
            "fist": ["fist", "closed_fist"],
            "closed_fist": ["closed_fist", "fist"],
            "stop": ["stop", "pause", "pause_control"],
            "pause": ["pause", "stop", "pause_control"],
            "pause_control": ["pause_control", "pause", "stop"],
            "thumbs_up": ["thumbs_up", "thumb_up"],
            "thumb_up": ["thumb_up", "thumbs_up"],
            "thumbs_down": ["thumbs_down", "thumb_down"],
            "thumb_down": ["thumb_down", "thumbs_down"],
        }

        for alias in aliases.get(selected_gesture, []):
            if alias in actions:
                return actions[alias]

        fallback_actions = {
            "index_point": "move_cursor",
            "point": "move_cursor",
            "pointing": "move_cursor",
            "index_finger": "move_cursor",
            "peace": "left_click",
            "peace_sign": "left_click",
            "two_fingers": "left_click",
            "two_finger": "left_click",
            "three_fingers": "right_click",
            "three_finger": "right_click",
            "pinch": "start_drag",
            "pinch_start": "start_drag",
            "drag": "start_drag",
            "pinch_release": "end_drag",
            "release_pinch": "end_drag",
            "drag_release": "end_drag",
            "open_palm": "scroll",
            "palm": "scroll",
            "five_fingers": "scroll",
            "fist": "pause_control",
            "closed_fist": "pause_control",
            "stop": "pause_control",
        }

        return fallback_actions.get(selected_gesture, "no_action")


class ProfileManager:
    def __init__(
        self,
        path: str | Path = "config/gestures.yaml",
        active_profile: str = "default",
        logger: Any | None = None,
        config_path: str | Path | None = None,
        profiles_path: str | Path | None = None,
    ) -> None:
        selected_path = profiles_path or config_path or path

        self.path = Path(selected_path)
        self.logger = logger
        self._profiles: dict[str, GestureProfile] = {}
        self._active_profile_name = str(active_profile).strip().lower()

        self.reload()

        if self._active_profile_name not in self._profiles:
            available = ", ".join(self.list_profiles())
            raise ProfileError(
                f"Unknown profile '{self._active_profile_name}'. "
                f"Available profiles: {available}"
            )

    @classmethod
    def from_yaml(
        cls,
        path: str | Path = "config/gestures.yaml",
        active_profile: str = "default",
        logger: Any | None = None,
        **kwargs: Any,
    ) -> ProfileManager:
        selected_path = (
            kwargs.get("profiles_path")
            or kwargs.get("config_path")
            or kwargs.get("path")
            or path
        )

        selected_profile = (
            kwargs.get("active_profile_name")
            or kwargs.get("profile_name")
            or kwargs.get("default_profile")
            or kwargs.get("active_profile")
            or active_profile
            or "default"
        )

        return cls(
            path=selected_path,
            active_profile=str(selected_profile),
            logger=logger,
        )

    @property
    def active_profile_name(self) -> str:
        return self._active_profile_name

    @property
    def profile_names(self) -> list[str]:
        return self.list_profiles()

    @property
    def profiles(self) -> dict[str, GestureProfile]:
        return dict(self._profiles)

    @property
    def active_profile(self) -> GestureProfile:
        return self.get_active_profile()

    def reload(self) -> None:
        data = self._read_yaml(self.path)
        profiles_data = data.get("profiles")

        if not isinstance(profiles_data, dict) or not profiles_data:
            raise ProfileError("No gesture profiles were found in config/gestures.yaml.")

        loaded_profiles: dict[str, GestureProfile] = {}

        for profile_name, profile_data in profiles_data.items():
            if not isinstance(profile_data, dict):
                raise ProfileError(f"Profile '{profile_name}' must be a YAML object.")

            normalized_name = str(profile_name).strip().lower()

            loaded_profiles[normalized_name] = self._build_profile(
                profile_name=normalized_name,
                profile_data=profile_data,
            )

        self._profiles = loaded_profiles
        self._log(f"Loaded {len(self._profiles)} gesture profile(s) from {self.path}")

    def list_profiles(self) -> list[str]:
        return sorted(self._profiles.keys())

    def available_profiles(self) -> list[str]:
        return self.list_profiles()

    def has_profile(self, profile_name: str) -> bool:
        return str(profile_name).strip().lower() in self._profiles

    def get_profile(self, profile_name: str | None = None) -> GestureProfile:
        selected_name = (
            str(profile_name).strip().lower()
            if profile_name is not None
            else self._active_profile_name
        )

        try:
            return self._profiles[selected_name]
        except KeyError as exc:
            available = ", ".join(self.list_profiles())
            raise ProfileError(
                f"Unknown profile '{selected_name}'. Available profiles: {available}"
            ) from exc

    def get_active_profile(self) -> GestureProfile:
        return self.get_profile(self._active_profile_name)

    def get_default_profile(self) -> GestureProfile:
        if "default" not in self._profiles:
            available = ", ".join(self.list_profiles())
            raise ProfileError(
                f"Default profile was not found. Available profiles: {available}"
            )

        return self._profiles["default"]

    def set_active_profile(self, profile_name: str) -> GestureProfile:
        selected_name = str(profile_name).strip().lower()

        if selected_name not in self._profiles:
            available = ", ".join(self.list_profiles())
            raise ProfileError(
                f"Unknown profile '{selected_name}'. Available profiles: {available}"
            )

        self._active_profile_name = selected_name
        profile = self._profiles[selected_name]

        self._log(f"Active gesture profile changed to {selected_name}")
        return profile

    def load_profile(self, profile_name: str) -> GestureProfile:
        return self.set_active_profile(profile_name)

    def get_active_profile_name(self) -> str:
        return self._active_profile_name

    def get_default_mode(self, profile_name: str | None = None) -> str:
        return self.get_profile(profile_name).default_mode

    def get_active_mode(self) -> str:
        return self.get_active_profile().default_mode

    def get_mode_actions(
        self,
        mode: str,
        profile_name: str | None = None,
    ) -> dict[str, str]:
        profile = self.get_profile(profile_name)
        return profile.get_actions_for_mode(mode)

    def mode_actions(
        self,
        mode: str,
        profile_name: str | None = None,
    ) -> dict[str, str]:
        return self.get_mode_actions(mode=mode, profile_name=profile_name)

    def get_action(
        self,
        gesture_name: str | None = None,
        mode: str | None = None,
        profile_name: str | None = None,
        gesture: str | None = None,
        **_: Any,
    ) -> str:
        selected_gesture = gesture_name or gesture

        if selected_gesture is None:
            raise ProfileError("Gesture name was not provided.")

        profile = self.get_profile(profile_name)
        selected_mode = mode or profile.default_mode

        return profile.resolve_action(
            mode=selected_mode,
            gesture_name=selected_gesture,
        )

    def resolve_action(
        self,
        gesture_name: str | None = None,
        mode: str | None = None,
        profile_name: str | None = None,
        gesture: str | None = None,
        **kwargs: Any,
    ) -> str:
        return self.get_action(
            gesture_name=gesture_name,
            gesture=gesture,
            mode=mode,
            profile_name=profile_name,
            **kwargs,
        )

    def describe(self, profile_name: str | None = None) -> dict[str, Any]:
        profile = self.get_profile(profile_name)

        return {
            "name": profile.name,
            "description": profile.description,
            "default_mode": profile.default_mode,
            "modes": sorted(profile.modes.keys()),
        }

    def _build_profile(
        self,
        profile_name: str,
        profile_data: dict[str, Any],
    ) -> GestureProfile:
        description = str(
            profile_data.get(
                "description",
                f"Gesture profile for {profile_name}.",
            )
        )

        default_mode = str(profile_data.get("default_mode", "mouse")).strip().lower()

        modes: dict[str, dict[str, str]] = {}

        nested_modes = profile_data.get("modes")

        if isinstance(nested_modes, dict):
            for mode_name, mode_actions in nested_modes.items():
                if isinstance(mode_actions, dict):
                    modes[str(mode_name).strip().lower()] = self._normalize_actions(
                        mode_actions
                    )

        for key, value in profile_data.items():
            if key in {"description", "default_mode", "modes"}:
                continue

            if isinstance(value, dict):
                modes[str(key).strip().lower()] = self._normalize_actions(value)

        return GestureProfile(
            name=profile_name,
            description=description,
            default_mode=default_mode,
            modes=modes,
        )

    def _normalize_actions(self, actions: dict[Any, Any]) -> dict[str, str]:
        normalized_actions: dict[str, str] = {}

        for gesture_name, action_name in actions.items():
            normalized_gesture = str(gesture_name).strip().lower()
            normalized_action = str(action_name).strip().lower()

            if normalized_gesture:
                normalized_actions[normalized_gesture] = normalized_action

        return normalized_actions

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise ProfileError(f"Gesture profile file was not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
        except yaml.YAMLError as exc:
            raise ProfileError(f"Invalid YAML inside {path}") from exc

        if not isinstance(data, dict):
            raise ProfileError(f"Gesture profile file must contain a YAML object: {path}")

        return data

    def _log(self, message: str) -> None:
        if self.logger is not None:
            self.logger.info(message)