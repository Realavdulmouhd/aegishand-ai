import pytest

from aegishand.gestures.feature_extractor import FeatureExtractionError, HandFeatureExtractor
from aegishand.vision.landmark_utils import NormalizedLandmark


def make_landmarks() -> tuple[NormalizedLandmark, ...]:
    return tuple(
        NormalizedLandmark(
            index=index,
            x=0.1 + (index * 0.01),
            y=0.2 + (index * 0.01),
            z=0.0,
        )
        for index in range(21)
    )


def test_feature_extractor_returns_expected_size() -> None:
    extractor = HandFeatureExtractor()

    features = extractor.extract(make_landmarks())

    assert features.size == 68


def test_feature_names_match_feature_count() -> None:
    extractor = HandFeatureExtractor()

    features = extractor.extract(make_landmarks())

    assert len(extractor.feature_names) == features.size


def test_feature_vector_can_convert_to_numpy() -> None:
    extractor = HandFeatureExtractor()

    array = extractor.extract(make_landmarks()).as_numpy()

    assert array.shape == (68,)


def test_feature_extractor_rejects_wrong_landmark_count() -> None:
    extractor = HandFeatureExtractor()

    with pytest.raises(FeatureExtractionError):
        extractor.extract(make_landmarks()[:10])