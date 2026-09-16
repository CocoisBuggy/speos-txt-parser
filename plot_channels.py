import matplotlib.pyplot as plt

from lib.args import get_args
from lib.data import read_data


def main():
    args = get_args()

    norm, extent, datasets, bands = read_data(args.path)

    fig, axes = plt.subplots(2, 5, figsize=(20, 9), constrained_layout=True)
    for i, (tag, ax) in enumerate(zip(bands, axes.flat)):
        im = ax.imshow(
            datasets[i],
            cmap=args.cmap,
            norm=norm,
            origin="lower",
            extent=extent,
            aspect="equal",
        )
        ax.set_title(f"{tag} - {(i + 1) * 9} deg")
        ax.set_xlabel("X (deg)")
        ax.set_ylabel("Y (deg)")

        if i == len(bands) - 1:
            fig.colorbar(im, ax=axes[:, -1], label="W/m$^2$")

    fig.suptitle("Irradiance by elevation band (shared scale)")

    if args.save:
        fig.savefig(args.save, bbox_inches="tight")
    else:
        plt.show()


if __name__ == "__main__":
    main()
