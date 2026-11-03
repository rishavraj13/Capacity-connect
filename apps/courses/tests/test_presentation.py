"""Exercise layout without fixtures or database access."""

import pytest

from apps.courses.constants import StationState
from apps.courses.dataclasses import Line, Station
from apps.courses.presentation import station_layout


def line(size: int, subject: int = 1) -> Line:
    """Build ordered stations with one interchange and one completed stop."""
    stations = tuple(
        Station(
            i,
            f"Module with a long title {i}",
            i,
            1,
            "Course",
            StationState.DONE if i == 1 else StationState.LOCKED,
            i == 1,
        )
        for i in range(1, size + 1)
    )
    return Line(subject, f"Subject {subject}", stations)


@pytest.mark.parametrize("size", (0, 1, 2, 6, 7, 20))
def test_station_layout_preserves_order_and_wraps(size: int) -> None:
    """Keep all stops within bounds and connect wraps without a diagonal."""
    source = line(size)
    layout = station_layout((source,))
    track = layout.tracks[0]
    assert tuple(stop.station for stop in track.stops) == source.stations
    assert all(0 < stop.x < layout.width for stop in track.stops)
    assert all(0 < stop.y < layout.height for stop in track.stops)
    for before, after in zip(track.stops, track.stops[1:], strict=False):
        assert before.x == after.x or before.y == after.y
    if size > 6:
        assert track.stops[5].x == track.stops[6].x
        assert track.stops[5].y < track.stops[6].y


def test_station_layout_cycles_lines_and_is_stable() -> None:
    """Separate tracks and retain an interchange's larger hit target."""
    lines = (line(7), line(2, 2), line(2, 3), line(1, 4))
    result = station_layout(lines)
    assert result == station_layout(lines)
    assert [track.color for track in result.tracks] == [
        "line-1",
        "line-2",
        "line-3",
        "line-1",
    ]
    first, second, *_ = result.tracks
    assert first.done == 1
    assert first.stops[-1].y < second.stops[0].y
    assert first.stops[0].radius > first.stops[1].radius
    assert first.stops[0].label.endswith("…")
    assert station_layout(()).tracks == ()
