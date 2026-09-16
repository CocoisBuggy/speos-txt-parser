import matplotlib.pyplot as plt
import numpy as np

from lib.args import get_args
from lib.data import read_data
from lib.geometry import compute_centers, extract_cuts


def plot_map(ax, data, extent, centers, cmap):
    x_center, y_center = centers

    im = ax.imshow(
        data,
        cmap=cmap,
        origin="lower",
        extent=extent,
        aspect="auto",
    )
    ax.axvline(x_center, color="white", linestyle="--", linewidth=1.5)
    ax.axhline(y_center, color="white", linestyle="--", linewidth=1.5)
    ax.set_title("Total irradiance summed over all elevation bands")

    return im


def make_axes(fig):
    """
    Create a 2×2 GridSpec with a central map and side-line axes.
    """
    gs = fig.add_gridspec(
        2,
        2,
        width_ratios=[1, 3],
        height_ratios=[3, 1],
        hspace=0.08,
        wspace=0.08,
    )

    ax_map = fig.add_subplot(gs[0, 1])
    ax_vertical = fig.add_subplot(gs[0, 0], sharey=ax_map)
    ax_horizontal = fig.add_subplot(gs[1, 1], sharex=ax_map)

    return ax_map, ax_horizontal, ax_vertical


def plot_horizontal_cut(ax, x_coords, horizontal_profile, y_center):
    ax.plot(x_coords, horizontal_profile)
    ax.grid(True)
    ax.set_xlabel("X (deg)")
    ax.set_ylabel("W/m$^2$")
    ax.set_title(f"Y = {y_center:.2f} deg")


def plot_vertical_cut(ax, vertical_profile, y_coords, x_center, extent):
    _, _, ymin, ymax = extent

    ax.plot(vertical_profile, y_coords)
    ax.grid(True)
    ax.set_xlabel("W/m$^2$")
    ax.set_ylabel("Y (deg)")
    ax.set_title(f"X = {x_center:.2f} deg", pad=14)
    plt.setp(ax.get_xticklabels(), rotation=90)
    ax.set_ylim(ymin, ymax)


def line_cuts(data, extent, cmap):
    centers = compute_centers(extent)
    x_center, y_center = centers
    x_coords, y_coords, vertical_profile, horizontal_profile = extract_cuts(
        data, extent, centers
    )

    fig = plt.figure(figsize=(10, 9), constrained_layout=True)
    ax_map, ax_horizontal, ax_vertical = make_axes(fig)

    im = plot_map(ax_map, data, extent, (x_center, y_center), cmap)
    fig.colorbar(im, ax=ax_map, label="W/m$^2$")

    plot_horizontal_cut(ax_horizontal, x_coords, horizontal_profile, y_center)
    plot_vertical_cut(ax_vertical, vertical_profile, y_coords, x_center, extent)

    return fig, (ax_map, ax_horizontal, ax_vertical)


def main():
    args = get_args()

    extent, datasets, bands = read_data(args.path)[1:]

    total = np.sum(datasets, axis=0)

    line_cuts(total, extent, args.cmap)

    if args.save:
        plt.savefig(args.save, bbox_inches="tight")
    else:
        plt.show()


if __name__ == "__main__":
    main()
