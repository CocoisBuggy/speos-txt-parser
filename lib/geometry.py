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


def extract_cuts(data, extent, centers=None, window=0):
    xmin, xmax, ymin, ymax = extent
    if centers is None:
        centers = compute_centers(extent)
    row, col = center_indices(data, extent, centers)

    vertical_profile = data[:, col]
    horizontal_profile = data[row]
    x_coords = np.linspace(xmin, xmax, data.shape[1])
    y_coords = np.linspace(ymin, ymax, data.shape[0])

    if window > 0:
        row_start = max(0, row - window)
        row_end = min(data.shape[0], row + window + 1)
        col_start = max(0, col - window)
        col_end = min(data.shape[1], col + window + 1)

        horizontal_avg_profile = data[row_start:row_end].mean(axis=0)
        vertical_avg_profile = data[:, col_start:col_end].mean(axis=1)
    else:
        horizontal_avg_profile = None
        vertical_avg_profile = None

    return (
        x_coords,
        y_coords,
        vertical_profile,
        horizontal_profile,
        vertical_avg_profile,
        horizontal_avg_profile,
    )
