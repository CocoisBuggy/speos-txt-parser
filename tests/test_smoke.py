"""Lightweight smoke tests: parse example files and run basic operations."""

import sys
from pathlib import Path

import numpy as np
import pytest

from lib.args import get_args
from lib.data import read_data
from lib.geometry import center_indices, compute_centers, extract_cuts

# Ensure the project root is on sys.path so we can import lib.* and plot_*.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

REPO = _HERE.parent


# ---------------------------------------------------------------------------
# Session fixture -- parsed landscape data, reused across tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def landscape():
    return read_data(str(_HERE / "example_landscape.txt"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _portrait():
    return read_data(str(_HERE / "example_portrait.txt"))


def _landscape():
    return read_data(str(_HERE / "example_landscape.txt"))


class TestReadData:
    def test_returns_tuple(self):
        result = _portrait()
        assert len(result) == 5  # norm, extent, datasets, bands, unit

    def test_norm(self):
        norm, *_ = _portrait()
        assert norm is not None
        assert norm.vmin == 1.0
        assert norm.vmax == 16.0

    def test_extent_parsed(self):
        _, extent, *_ = _portrait()
        # Original extent [0,3,0,5] is swapped to landscape
        assert extent == [0, 5, 0, 3]

    def test_datasets_count(self):
        _, _, datasets, _, _ = _portrait()
        assert len(datasets) == 2

    def test_bands_labels(self):
        *_, bands, _ = _portrait()
        assert bands == ["0", "10"]

    def test_landscape_stays_landscape(self):
        """Already landscape data should not be transposed."""
        _, extent, datasets, _, _ = _landscape()
        assert extent == [0, 5, 0, 3]
        for d in datasets:
            assert d.shape == (3, 5)  # rows < cols already

    def test_portrait_rotates_to_landscape(self):
        """Portrait data is transposed so shape[0] <= shape[1]."""
        _, extent, datasets, _, _ = _portrait()
        # Original was 5x3 -> after transpose is 3x5
        assert extent == [
            0,
            5,
            0,
            3,
        ], "Extent should swap X and Y after landscape rotation"
        for d in datasets:
            assert d.shape == (3, 5), f"Expected (3, 5) landscape, got {d.shape}"


class TestComputeCenters:
    def test_basic(self):
        cx, cy = compute_centers([0, 3, 0, 5])
        assert cx == 1.5
        assert cy == 2.5


class TestCenterIndices:
    def test_landscape_data(self):
        _, extent, datasets, _, _ = _landscape()
        row, col = center_indices(datasets[0], extent)
        # 3 rows, 5 cols; extent [0,5,0,3]; centre (2.5, 1.5)
        assert 0 <= row < datasets[0].shape[0]
        assert 0 <= col < datasets[0].shape[1]
        assert row == 1  # middle row
        assert col == 2  # middle col


class TestExtractCuts:
    def test_returns_correct_lengths(self, landscape):
        _, extent, datasets, _, _ = landscape
        x, y, v, h = extract_cuts(datasets[0], extent)
        assert len(x) == datasets[0].shape[1]
        assert len(y) == datasets[0].shape[0]
        assert len(v) == datasets[0].shape[0]
        assert len(h) == datasets[0].shape[1]

    def test_portrait_return_lengths(self):
        _, extent, datasets, _, _ = _portrait()
        # After rotation: (3, 5) landscape
        x, y, v, h = extract_cuts(datasets[0], extent)
        assert len(x) == 5
        assert len(y) == 3
        assert len(v) == 3
        assert len(h) == 5


class TestArgs:
    def test_default_ylabel(self):
        args = get_args(["--path", "irrelevant.txt"])
        assert args.ylabel is None
        assert args.cmap == "viridis"
        assert args.path == "irrelevant.txt"
        assert args.save is None

    def test_custom_ylabel(self):
        args = get_args(["--path", "irrelevant.txt", "--ylabel", "W/m^2"])
        assert args.ylabel == "W/m^2"

    def test_cmap(self):
        args = get_args(["--path", "irrelevant.txt", "--cmap", "magma"])
        assert args.cmap == "magma"

    def test_save_default_name(self):
        args = get_args(["--path", "irrelevant.txt", "--save"])
        assert args.save == "plot.png"

    def test_save_custom_path(self):
        args = get_args(["--path", "irrelevant.txt", "--save", "out.png"])
        assert args.save == "out.png"


class TestIntegration:
    """Exercise the full pipeline with example data (no GUI)."""

    def test_line_cuts_runs(self, landscape):
        """line_cuts should return a figure without crashing."""
        from plot_irradiance import line_cuts

        _, extent, datasets, _, _ = landscape
        total = np.sum(datasets, axis=0)
        fig, axes = line_cuts(total, extent, "viridis", "w/m2")
        assert fig is not None
        assert len(axes) == 3
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.close(fig)


HEADER_TMPL = """3\n0\n{unit_type}\n1\n0 1 0 1\n2 2\n0 - 10 degrees\n1 2\n3 4\n"""


class TestUnitDetection:
    """The header's UnitType line selects the value-unit label."""

    def test_radiometric(self, tmp_path):
        f = tmp_path / "radiometric.txt"
        f.write_text(HEADER_TMPL.format(unit_type=0))
        assert read_data(str(f)).unit == "W/m^2"

    def test_photometric(self, tmp_path):
        f = tmp_path / "photometric.txt"
        f.write_text(HEADER_TMPL.format(unit_type=1))
        assert read_data(str(f)).unit == "lm/m^2"

    def test_unknown_unit_type_falls_back(self, tmp_path):
        f = tmp_path / "unknown.txt"
        f.write_text(HEADER_TMPL.format(unit_type=7))
        assert read_data(str(f)).unit == "W/m^2"

    def test_prose_header_falls_back(self):
        """Hand-written fixture files without a numeric header default to W/m^2."""
        assert _landscape().unit == "W/m^2"

    def test_real_data_files(self):
        """The real ./data exports: .Irradiance files are radiometric, .Flux photometric."""
        for f in REPO.joinpath("data").rglob("*.txt"):
            expected = "lm/m^2" if "Flux" in f.name else "W/m^2"
            assert read_data(str(f)).unit == expected, f.name
