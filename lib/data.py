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


# Line 3 of the export header is the UnitType field (see the Ansys "TXT File
# Format" documentation: https://ansyshelp.ansys.com/public/Views/Secured/corp/v2521/en/Optis_UG_LAB/Optis/UG_Lab/txt_file_format_160517.html):
# 0 = radiometric, 1 = photometric.
_UNIT_LABELS = {
    0: "W/m^2",  # radiometric irradiance
    1: "lm/m^2",  # photometric irradiance (lux)
}
_DEFAULT_UNIT = "W/m^2"


def _detect_unit(header_lines: list[str]) -> str:
    """Map the header's UnitType value to an axis label.

    Falls back to W/m^2 when the header line is missing or not a plain
    integer (e.g. prose headers in hand-written files).
    """
    try:
        unit_type = int(header_lines[2])
    except (IndexError, ValueError):
        return _DEFAULT_UNIT
    return _UNIT_LABELS.get(unit_type, _DEFAULT_UNIT)


def read_data(path):
    """Parse an Ansys SPEOS irradiance cross-section TXT file.

    The expected format is a short header followed by space-separated
    irradiance matrices, each labelled with a ``N - M degrees`` marker.
    Line 3 of the header carries the exported map's UnitType (0 =
    radiometric, 1 = photometric), which is used to pick the value-unit
    label. Line 5 (0-indexed line 4) must contain four floats
    ``xmin xmax ymin ymax`` defining the spatial extent.

    Returns:
        The parsed file contents (norm, extent, datasets, bands, unit).
    """
    with open(path) as file:
        raw = file.readlines()

    if len(raw) < 5:
        raise ValueError(
            f"File {path!r} has only {len(raw)} line(s); "
            "expected at least 5 (header + extent line + data)."
        )

    unit = _detect_unit(raw)

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

    bands = [tag.split(" - ")[0] for tag in [raw[t] for t in tags]]

    n = len(tags)

    datasets = []
    for i in range(n):
        lo = tags[i] + 1
        hi = tags[i + 1] if i + 1 < n else len(raw)
        datasets.append(
            np.array([[float(v) for v in raw[j].split()] for j in range(lo, hi)])
        )

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

    return IrradianceData(norm, extent, datasets, bands, unit)
