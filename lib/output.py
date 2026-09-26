from pathlib import Path

_DATA = Path("data")
_FIGURES = Path("figures")


def auto_save_path(input_path: str, plot_name: str, ext: str = ".png") -> str:
    """
    Derive an output path for a plot based on the input file location.
    The ./data/ prefix is replaced with ./figures/ and the file stem
    becomes a subdirectory.
    """
    p = Path(input_path)
    rel = p.relative_to(_DATA)
    out_dir = _FIGURES / rel.parent / p.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    return str(out_dir / f"{plot_name}{ext}")
