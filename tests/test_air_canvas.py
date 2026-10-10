from aegishand.drawing.air_canvas import AirCanvas, AirCanvasConfig
from aegishand.vision.landmark_utils import NormalizedLandmark


def test_air_canvas_can_clear_without_existing_canvas() -> None:
    canvas = AirCanvas()

    status = canvas.clear()

    assert status.point_count == 0
    assert "cleared" in status.message.lower()


def test_air_canvas_draws_point() -> None:
    canvas = AirCanvas(
        config=AirCanvasConfig(
            brush_radius=4,
            min_draw_distance=2,
            overlay_opacity=0.8,
        )
    )

    status = canvas.draw_point(
        landmark=NormalizedLandmark(index=8, x=0.5, y=0.5, z=0.0),
        frame_width=640,
        frame_height=480,
    )

    assert status.active is True
    assert status.point_count == 1


def test_air_canvas_lift_pen_keeps_canvas() -> None:
    canvas = AirCanvas()

    canvas.draw_point(
        landmark=NormalizedLandmark(index=8, x=0.5, y=0.5, z=0.0),
        frame_width=640,
        frame_height=480,
    )
    canvas.lift_pen()

    status = canvas.draw_point(
        landmark=NormalizedLandmark(index=8, x=0.6, y=0.6, z=0.0),
        frame_width=640,
        frame_height=480,
    )

    assert status.active is True