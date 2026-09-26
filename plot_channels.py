import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from lib.data import IrradianceData
from lib.plotter import plotter


@plotter(name="channels")
def plot_channels(data: IrradianceData, cmap: str, ylabel: str) -> Figure:
    """First six elevation bands, one per subplot on a shared colour scale.

    High-angle bands beyond the sixth are discarded.
    """
    norm, extent, datasets, bands, _, axis_unit = data

    shown = min(len(datasets), len(bands), 6)

    fig, axes = plt.subplots(2, 3, figsize=(20, 9), constrained_layout=True)

    for i, (tag, ax) in enumerate(zip(bands[:shown], axes.flat)):
        im = ax.imshow(
            datasets[i],
            cmap=cmap,
            norm=norm,
            origin="lower",
            extent=extent,
            aspect="equal",
        )
        ax.set_title(f"{tag} degrees")
        ax.set_xlabel(f"X ({axis_unit})")
        ax.set_ylabel(f"Y ({axis_unit})")

        if i == shown - 1:
            fig.colorbar(im, ax=axes[:, -1], label=ylabel)

    for ax in axes.flat[shown:]:
        ax.set_visible(False)

    fig.suptitle("Irradiance by elevation band (shared scale)")

    return fig
