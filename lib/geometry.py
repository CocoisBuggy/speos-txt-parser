import numpy as np


def compute_centers(extent):
    """Return the (x, y) centre point of an extent rectangle."""
    xmin, xmax, ymin, ymax = extent
    return (xmin + xmax) / 2.0, (ymin + ymax) / 2.0


def center_indices(data, extent, centers=None):
    """Return the (row, col) of the centre cell in *data* given *extent*.

    Parameters
    ----------
    centers : (float, float) or None
        Pre-computed (x_center, y_center) to avoid recomputation.
    """
    xmin, xmax, ymin, ymax = extent
    if centers is None:
        x_center, y_center = compute_centers(extent)
    else:
        x_center, y_center = centers

    col = round((x_center - xmin) / (xmax - xmin) * (data.shape[1] - 1))
    row = round((y_center - ymin) / (ymax - ymin) * (data.shape[0] - 1))

    return row, col


def extract_cuts(data, extent, centers=None):
    """Extract centre-row and centre-column line cuts from 2-D *data*.

    Parameters
    ----------
    centers : (float, float) or None
        Pre-computed (x_center, y_center).  When None the centre is derived
        from *extent*.

    Returns
    -------
    x_coords : ndarray
        1-D array of x-coordinate values (column-major order).
    y_coords : ndarray
        1-D array of y-coordinate values (row-major order).
    vertical_profile : ndarray
        Values along the centre column (varying Y, the *x*-axis cut).
    horizontal_profile : ndarray
        Values along the centre row (varying X, the *y*-axis cut).

    Notes
    -----
    ``vertical_profile`` is the column slice ``data[:, col]`` — it traces
    irradiance across rows (Y direction) at a fixed X position, so it is the
    **vertical** line cut.  ``horizontal_profile`` is the row slice
    ``data[row]`` — it traces irradiance across columns (X direction) at a
    fixed Y position, so it is the **horizontal** line cut.
    """
    xmin, xmax, ymin, ymax = extent
    if centers is None:
        centers = compute_centers(extent)
    row, col = center_indices(data, extent, centers)

    vertical_profile = data[:, col]
    horizontal_profile = data[row]
    x_coords = np.linspace(xmin, xmax, data.shape[1])
    y_coords = np.linspace(ymin, ymax, data.shape[0])

    return x_coords, y_coords, vertical_profile, horizontal_profile