import argparse


def get_args(argv=None):
    """Parse CLI arguments for Ansys SPEOS irradiance plotting."""
    parser = argparse.ArgumentParser(
        description="Parse and plot Ansys SPEOS irradiance cross-section data."
    )
    parser.add_argument("path", help="Path to the irradiance TXT file")
    parser.add_argument(
        "--cmap",
        default="viridis",
        help="Matplotlib colormap name (default: viridis)",
    )
    parser.add_argument(
        "--save",
        nargs="?",
        const="plot.png",
        default=None,
        metavar="FILE",
        help="Save the figure to FILE instead of displaying it (default: plot.png)",
    )
    return parser.parse_args(argv)