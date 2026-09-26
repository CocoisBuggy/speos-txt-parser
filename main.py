"""Entry point that produces both the channel plot and the irradiance + cuts plot.

When ``--save`` is omitted the output is written to ``./figures/`` under a
subdirectory named after the input file — e.g. ``./data/plane.txt`` produces
``./figures/plane/channels.png`` and ``./figures/plane/irradiance.png``.
"""

from tqdm import tqdm

from lib.args import get_args
from lib.output import auto_save_path
from plot_channels import main as plot_channels
from plot_irradiance import main as plot_irradiance

plotters = [plot_channels, plot_irradiance]


def main():
    args = get_args()
    base_save = args.save
    for plotter in tqdm(plotters, desc="Generating plots"):
        args.save = base_save or auto_save_path(args.path, plotter.__name__)
        plotter(args)


if __name__ == "__main__":
    main()
