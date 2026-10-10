from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aegishand.gestures.feature_extractor import HandFeatureExtractor
from aegishand.gestures.gesture_types import GestureType, RecognizedGesture


class MLRecognizerError(RuntimeError):
    """Raised when the ML recognizer cannot be loaded or used safely."""


@dataclass(frozen=True)
class MLRecognizerConfig:
    model_path: str = "models/gesture_model.joblib"
    min_confidence: float = 0.70
    enabled: bool = True


class MLGestureRecognizer:
    """
    Optional ML recognizer wrapper.

    This class is intentionally safe:
    - It does not require a trained model to exist.
    - It does not store camera frames.
    - If no model is available, it returns UNKNOWN instead of crashing.
    """

    def __init__(
        self,
        config: MLRecognizerConfig | None = None,
        feature_extractor: HandFeatureExtractor | None = None,
    ) -> None:
        self.config = config or MLRecognizerConfig()
        self.feature_extractor = feature_extractor or HandFeatureExtractor()
        self.model: Any | None = None
        self.model_loaded = False

        if self.config.enabled:
            self.load_model_if_available()

    def load_model_if_available(self) -> bool:
        model_path = Path(self.config.model_path)

        if not model_path.exists():
            self.model = None
            self.model_loaded = False
            return False

        try:
            import joblib
        except ImportError as exc:
            raise MLRecognizerError(
                "joblib is not installed. Run: python -m pip install -r requirements.txt"
            ) from exc

        try:
            self.model = joblib.load(model_path)
        except Exception as exc:
            raise MLRecognizerError(f"Failed to load ML model: {model_path}") from exc

        self.model_loaded = True
        return True

    def recognize(self, hand: Any | None) -> RecognizedGesture:
        if hand is None:
            return RecognizedGesture.no_hand()

        if not self.config.enabled:
            return RecognizedGesture.unknown()

        if self.model is None:
            return RecognizedGesture.unknown()

        features = self.feature_extractor.extract(hand).as_numpy().reshape(1, -1)

        try:
            prediction = self.model.predict(features)[0]
        except Exception as exc:
            raise MLRecognizerError("ML model prediction failed.") from exc

        confidence = self._predict_confidence(features)

        if confidence < self.config.min_confidence:
            return RecognizedGesture.unknown()

        gesture = self._to_gesture_type(str(prediction))

        return RecognizedGesture(
            gesture=gesture,
            confidence=confidence,
        )

    def _predict_confidence(self, features: Any) -> float:
        if self.model is None:
            return 0.0

        predict_proba = getattr(self.model, "predict_proba", None)

        if callable(predict_proba):
            probabilities = predict_proba(features)

            try:
                return float(max(probabilities[0]))
            except Exception:
                return 1.0

        return 1.0

    def _to_gesture_type(self, value: str) -> GestureType:
        normalized = value.strip().lower()

        try:
            return GestureType(normalized)
        except ValueError:
            return GestureType.UNKNOWN