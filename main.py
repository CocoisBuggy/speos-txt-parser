"""Entry point that produces both the channel plot and the irradiance + cuts plot.

When ``--save`` is omitted the output is written to ``./figures/`` under a
subdirectory named after the input file — e.g. ``./data/plane.txt`` produces
``./figures/plane/channels.png`` and ``./figures/plane/irradiance.png``.

When ``--path`` is omitted, all ``.txt`` files in ``./data/`` are processed.
"""

from pathlib import Path

from tqdm import tqdm

from lib.args import get_args
from lib.output import auto_save_path
from plot_channels import main as plot_channels
from plot_irradiance import main as plot_irradiance

plotters = [plot_channels, plot_irradiance]


def main():
    args = get_args()
    base_save = args.save
    paths = [args.path] if args.path else sorted(Path("data").glob("*.txt"))
    for txt in tqdm(paths, desc="Generating plots"):
        args.path = str(txt)
        for plotter in plotters:
            args.save = base_save or auto_save_path(args.path, plotter.__name__)
            plotter(args)


if __name__ == "__main__":
    main()
