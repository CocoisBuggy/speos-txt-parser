import numpy as np
from matplotlib.colors import Normalize


def read_data(path):
    """Parse an Ansys SPEOS irradiance cross-section TXT file.

    The expected format is a short header followed by space-separated
    irradiance matrices, each labelled with a ``N - M degrees`` marker.
    Line 5 (0-indexed line 4) must contain four floats ``xmin xmax ymin ymax``
    defining the spatial extent.
    """
    with open(path) as file:
        raw = file.readlines()

    if len(raw) < 5:
        raise ValueError(
            f"File {path!r} has only {len(raw)} line(s); "
            "expected at least 5 (header + extent line + data)."
        )

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

    vmin = min(d.min() for d in datasets)
    vmax = max(d.max() for d in datasets)
    norm = Normalize(vmin=vmin, vmax=vmax)

    return norm, extent, datasets, bands
