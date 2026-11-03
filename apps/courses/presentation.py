"""Lay out detached station-map data for a responsive SVG."""

from dataclasses import dataclass

from apps.courses.constants import StationState
from apps.courses.dataclasses import Line, Station

WIDTH = 720
COLUMNS = 6
ROW_HEIGHT = 92
MARGIN = 60
STEP = (WIDTH - 2 * MARGIN) // (COLUMNS - 1)


@dataclass(frozen=True, slots=True)
class Stop:
    """Locate a station and retain its full text for accessible output."""

    station: Station
    x: int
    y: int
    radius: int
    label: str


@dataclass(frozen=True, slots=True)
class Track:
    """Carry one subject's positions and connected path."""

    line: Line
    color: str
    stops: tuple[Stop, ...]
    path: str
    done: int


@dataclass(frozen=True, slots=True)
class Map:
    """Expose dimensions and tracks without any ORM access."""

    width: int
    height: int
    tracks: tuple[Track, ...]


def _stop(station: Station, index: int, top: int) -> Stop:
    """Reverse alternate rows to connect them vertically at the edge."""
    row, column = divmod(index, COLUMNS)
    if row % 2:
        column = COLUMNS - 1 - column
    label = station.title
    if len(label) > 14:
        label = label[:13] + "…"
    return Stop(
        station,
        MARGIN + column * STEP,
        top + row * ROW_HEIGHT,
        17 if station.is_interchange else 12,
        label,
    )


def _track(line: Line, index: int, top: int) -> Track:
    """Connect stops in the original selector order."""
    stops = tuple(_stop(station, i, top) for i, station in enumerate(line.stations))
    path = " ".join(
        f"{'M' if i == 0 else 'L'} {stop.x} {stop.y}" for i, stop in enumerate(stops)
    )
    done = sum(station.state == StationState.DONE for station in line.stations)
    return Track(line, f"line-{index % 3 + 1}", stops, path, done)


def station_layout(lines: tuple[Line, ...]) -> Map:
    """Stack serpentine tracks in a fixed-width viewBox."""
    top = 54
    tracks = []
    for index, line in enumerate(lines):
        tracks.append(_track(line, index, top))
        rows = max(1, (len(line.stations) + COLUMNS - 1) // COLUMNS)
        top += rows * ROW_HEIGHT
    return Map(WIDTH, top - 24, tuple(tracks))
