"""
Entry point that produces both the channel plot and the irradiance + cuts plot.
check --help or readme for more
"""

from pathlib import Path

import matplotlib.pyplot as plt
from tqdm import tqdm

from lib.args import get_args
from lib.data import read_data
from lib.output import auto_save_path
from lib.plotter import Plotter
from plot_channels import plot_channels
from plot_irradiance import plot_irradiance

plotters: list[Plotter] = [
    plot_channels,
    plot_irradiance,
]


def main():
    args = get_args()
    paths = [args.path] if args.path else sorted(Path("data").rglob("*.txt"))

    for txt in tqdm(paths, desc="Generating plots..."):
        data = read_data(str(txt))
        ylabel = args.ylabel or data.unit
        for plotter in plotters:
            fig = plotter.plot(data, cmap=args.cmap, ylabel=ylabel)
            save = args.save or auto_save_path(str(txt), plotter.name)
            if save:
                fig.savefig(save, bbox_inches="tight")
                plt.close(fig)
            else:
                plt.show()


if __name__ == "__main__":
    main()
