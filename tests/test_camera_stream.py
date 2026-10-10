import pytest

from aegishand.camera.camera_stream import CameraStreamConfig, CameraStreamError


def test_camera_config_accepts_valid_values() -> None:
    config = CameraStreamConfig(
        index=0,
        width=1280,
        height=720,
        fps_limit=30,
    )

    config.validate()


def test_camera_config_rejects_negative_index() -> None:
    config = CameraStreamConfig(
        index=-1,
        width=1280,
        height=720,
        fps_limit=30,
    )

    with pytest.raises(CameraStreamError):
        config.validate()


def test_camera_config_rejects_tiny_resolution() -> None:
    config = CameraStreamConfig(
        index=0,
        width=100,
        height=100,
        fps_limit=30,
    )

    with pytest.raises(CameraStreamError):
        config.validate()


def test_camera_config_rejects_invalid_fps() -> None:
    config = CameraStreamConfig(
        index=0,
        width=1280,
        height=720,
        fps_limit=0,
    )

    with pytest.raises(CameraStreamError):
        config.validate()