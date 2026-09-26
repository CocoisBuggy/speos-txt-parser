import warnings
from typing import NamedTuple

import numpy as np
from matplotlib.colors import Normalize


class IrradianceData(NamedTuple):
    """Parsed contents of one SPEOS irradiance cross-section file."""

    norm: Normalize
    extent: list[float]
    datasets: list[np.ndarray]
    bands: list[str]
    unit: str
    axis_unit: str


# The export header follows the Ansys "TXT File Format" documentation
# (https://ansyshelp.ansys.com/public/Views/Secured/corp/v2521/en/Optis_UG_LAB/Optis/UG_Lab/txt_file_format_160517.html).
# Header line 2 is the ValueType field and line 3 the UnitType field. The
# UnitType labels below are the documented codes expressed for irradiance
# maps (ValueType 0):
#   0 = Radiometric, 1 = Photometric, 2 = Temperature, 3 = Unknown,
#   4 = FTM, 5 = Degree, 6 = Inverse Meter, 7 = Inverse Square Meter,
#   8 = Percent, 9 = Diopter, 10 = Meter, 11 = 1/sr
_UNIT_LABELS = {
    0: "W/m^2",  # radiometric irradiance
    1: "lm/m^2",  # photometric irradiance (lux)
    2: "K",  # temperature
    5: "deg",
    6: "1/m",
    7: "1/m^2",
    8: "%",
    9: "dpt",  # diopter
    10: "m",
    11: "1/sr",
}
# UnitType 3 (Unknown) and 4 (FTM) have no meaningful label; they fall back.
_DEFAULT_UNIT = "W/m^2"

# Header line 4 is the AxisUnit field. Codes:
#   0 = Default, 1 = Millimeter, 2 = Degree, 3 = Radian, 4 = Feet,
#   5 = Micrometer, 6 = Nanometer, 7 = Meter, 8 = Percent, 9 = dB,
#   10 = Invert Millimeter, 11 = No Unit, 12 = Wave
_AXIS_UNIT_LABELS = {
    1: "mm",
    2: "deg",
    3: "rad",
    4: "ft",
    5: "um",
    6: "nm",
    7: "m",
    8: "%",
    9: "dB",
    10: "1/mm",
    11: "",  # No Unit
}
_DEFAULT_AXIS_UNIT = "deg"  # historical assumption for files without the field


def _header_int(header_lines: list[str], index: int) -> int | None:
    """Parse a header line as an int, returning None if it is not one."""
    try:
        return int(header_lines[index])
    except (IndexError, ValueError):
        return None


def _detect_units(header_lines: list[str]) -> tuple[str, str]:
    """Map the header's ValueType/UnitType/AxisUnit values to labels.

    Falls back to W/m^2 / degrees when the header lines are missing or not
    plain integers (e.g. prose headers in hand-written files). Warns when
    the ValueType is present but not 0 (irradiance), since the labels
    assume irradiance maps.

    Returns:
        (unit, axis_unit) labels for the value and spatial axes.
    """
    value_type = _header_int(header_lines, 1)
    if value_type is not None and value_type != 0:
        warnings.warn(
            f"ValueType {value_type} is not 0 (irradiance); "
            "unit labels assume irradiance maps",
            stacklevel=3,
        )

    unit_type = _header_int(header_lines, 2)
    unit = (
        _UNIT_LABELS.get(unit_type, _DEFAULT_UNIT)
        if unit_type is not None
        else _DEFAULT_UNIT
    )

    axis_type = _header_int(header_lines, 3)
    axis_unit = (
        _AXIS_UNIT_LABELS.get(axis_type, _DEFAULT_AXIS_UNIT)
        if axis_type is not None
        else _DEFAULT_AXIS_UNIT
    )

    return unit, axis_unit


# Header line 1 is the MapType field; the band-section layout this parser
# expects is that of an extended map.
_EXPECTED_MAP_TYPE = 3


def _band_label(marker_line: str) -> str:
    """Extract the band range from a ``N - M degrees`` marker line.

    Keeps the full ``N - M`` range when present, falling back to the first
    token for other marker styles.
    """
    label = marker_line.replace("degrees", "").strip()
    if " - " in label:
        return label
    return label.split()[0]


def _header_dims(header_lines: list[str], index: int) -> tuple[int, int] | None:
    """Parse an ``NbX NbY`` grid-dimension line, if present."""
    try:
        nbx, nby = (int(v) for v in header_lines[index].split())
    except (IndexError, ValueError):
        return None
    return nbx, nby


def read_data(path):
    """Parse an Ansys SPEOS irradiance cross-section TXT file.

    The expected format is a short header followed by space-separated
    irradiance matrices, each labelled with a ``N - M degrees`` marker.
    Header lines 2-4 carry the exported map's ValueType, UnitType and
    AxisUnit, which are used to pick the value-unit and axis labels;
    header line 1 is the MapType and line 6 the ``NbX NbY`` grid size,
    which is validated against the parsed matrices when present.
    Line 5 (0-indexed line 4) must contain four floats
    ``xmin xmax ymin ymax`` defining the spatial extent.

    Returns:
        The parsed file contents (norm, extent, datasets, bands, unit,
        axis_unit).
    """
    with open(path) as file:
        raw = file.readlines()

    if len(raw) < 5:
        raise ValueError(
            f"File {path!r} has only {len(raw)} line(s); "
            "expected at least 5 (header + extent line + data)."
        )

    unit, axis_unit = _detect_units(raw)

    map_type = _header_int(raw, 0)
    if map_type is not None and map_type != _EXPECTED_MAP_TYPE:
        warnings.warn(
            f"MapType {map_type} is not {_EXPECTED_MAP_TYPE} (extended map); "
            "the band-section layout may not apply",
            stacklevel=2,
        )

    dims = _header_dims(raw, 5)

    try:
        xmin, xmax, ymin, ymax = [float(x) for x in raw[4].split()]
    except (ValueError, IndexError) as exc:
        raise ValueError(
            f"Line 5 of {path!r} does not contain four floats:\n{raw[4]!r}"
        ) from exc
    extent = [xmin, xmax, ymin, ymax]

    tags = [i for i, ln in enumerate(raw) if "degrees" in ln]
    if not tags:
        raise ValueError(
            f'No "degrees" markers found in {path!r}; '
            "is this a valid SPEOS irradiance cross-section file?"
        )

    bands = [_band_label(raw[t]) for t in tags]

    n = len(tags)

    datasets = []
    for i in range(n):
        lo = tags[i] + 1
        hi = tags[i + 1] if i + 1 < n else len(raw)
        try:
            rows = [[float(v) for v in raw[j].split()] for j in range(lo, hi)]
        except ValueError as exc:
            raise ValueError(
                f"Non-numeric data in {path!r} within band {i + 1} "
                f"(lines {lo + 1}-{hi}): {exc}"
            ) from exc
        try:
            matrix = np.array(rows)
        except ValueError as exc:
            raise ValueError(
                f"Band {i + 1} of {path!r} (lines {lo + 1}-{hi}) is not a "
                f"rectangular matrix; the file may be truncated: {exc}"
            ) from exc
        if matrix.ndim != 2:
            raise ValueError(
                f"Band {i + 1} of {path!r} (lines {lo + 1}-{hi}) is not a "
                "rectangular matrix; the file may be truncated"
            )
        if dims is not None and matrix.shape != (dims[1], dims[0]):
            raise ValueError(
                f"Band {i + 1} of {path!r} has shape {matrix.shape}, but the "
                f"header declares NbX={dims[0]} NbY={dims[1]}"
            )
        datasets.append(matrix)

    if not datasets:
        raise ValueError(f"No data matrices could be parsed from {path!r}.")

    # Rotate to landscape if the data matrix is taller than it is wide.
    shape = datasets[0].shape
    if shape[0] > shape[1]:
        xmin, xmax, ymin, ymax = extent
        extent = [ymin, ymax, xmin, xmax]
        datasets = [d.T for d in datasets]

    vmin = min(d.min() for d in datasets)
    vmax = max(d.max() for d in datasets)
    norm = Normalize(vmin=vmin, vmax=vmax)

    return IrradianceData(norm, extent, datasets, bands, unit, axis_unit)
