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
        assert len(result) == 6  # norm, extent, datasets, bands, unit, axis_unit

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
        _, _, datasets, _, _, _ = _portrait()
        assert len(datasets) == 2

    def test_bands_labels(self):
        *_, bands, _, _ = _portrait()
        assert bands == ["0 - 9", "10 - 18"]

    def test_landscape_stays_landscape(self):
        """Already landscape data should not be transposed."""
        _, extent, datasets, _, _, _ = _landscape()
        assert extent == [0, 5, 0, 3]
        for d in datasets:
            assert d.shape == (3, 5)  # rows < cols already

    def test_portrait_rotates_to_landscape(self):
        """Portrait data is transposed so shape[0] <= shape[1]."""
        _, extent, datasets, _, _, _ = _portrait()
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
        _, extent, datasets, _, _, _ = _landscape()
        row, col = center_indices(datasets[0], extent)
        # 3 rows, 5 cols; extent [0,5,0,3]; centre (2.5, 1.5)
        assert 0 <= row < datasets[0].shape[0]
        assert 0 <= col < datasets[0].shape[1]
        assert row == 1  # middle row
        assert col == 2  # middle col


class TestExtractCuts:
    def test_returns_correct_lengths(self, landscape):
        _, extent, datasets, _, _, _ = landscape
        x, y, v, h = extract_cuts(datasets[0], extent)
        assert len(x) == datasets[0].shape[1]
        assert len(y) == datasets[0].shape[0]
        assert len(v) == datasets[0].shape[0]
        assert len(h) == datasets[0].shape[1]

    def test_portrait_return_lengths(self):
        _, extent, datasets, _, _, _ = _portrait()
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

        _, extent, datasets, _, _, _ = landscape
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
        """UnitType 3 (Unknown), 4 (FTM) and out-of-range codes fall back."""
        for unit_type in (3, 4, 99):
            f = tmp_path / f"fallback_{unit_type}.txt"
            f.write_text(HEADER_TMPL.format(unit_type=unit_type))
            assert read_data(str(f)).unit == "W/m^2", unit_type

    def test_all_documented_unit_types(self, tmp_path):
        """Every UnitType code listed by the Ansys documentation maps to a label."""
        cases = {
            0: "W/m^2",  # radiometric
            1: "lm/m^2",  # photometric
            2: "K",  # temperature
            5: "deg",
            6: "1/m",
            7: "1/m^2",
            8: "%",
            9: "dpt",
            10: "m",
            11: "1/sr",
        }
        for unit_type, expected in cases.items():
            f = tmp_path / f"unit_{unit_type}.txt"
            f.write_text(HEADER_TMPL.format(unit_type=unit_type))
            assert read_data(str(f)).unit == expected, unit_type

    def test_non_irradiance_value_type_warns(self, tmp_path):
        """A ValueType other than 0 (irradiance) triggers a warning."""
        f = tmp_path / "radiance.txt"
        f.write_text(HEADER_TMPL.format(unit_type=0).replace("\n0\n", "\n2\n", 1))
        with pytest.warns(UserWarning, match="ValueType"):
            read_data(str(f))

    def test_prose_header_falls_back(self):
        """Hand-written fixture files without a numeric header default to W/m^2 / deg."""
        assert _landscape().unit == "W/m^2"
        assert _landscape().axis_unit == "deg"

    def test_axis_unit_detected(self, tmp_path):
        """Every AxisUnit code listed by the Ansys documentation maps to a label."""
        cases = {
            1: "mm",
            2: "deg",
            3: "rad",
            4: "ft",
            5: "um",
            6: "nm",
            7: "m",
            8: "%",
            9: "dB",
            10: "1/mm",
            11: "",  # No Unit
        }
        for axis_type, expected in cases.items():
            lines = HEADER_TMPL.format(unit_type=0).split("\n")
            lines[3] = str(axis_type)
            f = tmp_path / f"axis_{axis_type}.txt"
            f.write_text("\n".join(lines))
            assert read_data(str(f)).axis_unit == expected, axis_type

    def test_axis_unit_fallback(self, tmp_path):
        """AxisUnit 0 (Default), 12 (Wave) and out-of-range codes fall back to deg."""
        for axis_type in (0, 12, 99):
            lines = HEADER_TMPL.format(unit_type=0).split("\n")
            lines[3] = str(axis_type)
            f = tmp_path / f"axis_fallback_{axis_type}.txt"
            f.write_text("\n".join(lines))
            assert read_data(str(f)).axis_unit == "deg", axis_type

    def test_real_data_files(self):
        """Real ./data exports: Flux photometric / Irradiance radiometric, axes in mm."""
        for f in REPO.joinpath("data").rglob("*.txt"):
            expected = "lm/m^2" if "Flux" in f.name else "W/m^2"
            parsed = read_data(str(f))
            assert parsed.unit == expected, f.name
            assert parsed.axis_unit == "mm", f.name


class TestHeaderValidation:
    """MapType / grid-dimension / band-content validation in read_data."""

    def test_map_type_warning(self, tmp_path):
        """MapType other than 3 (extended map) triggers a warning."""
        lines = HEADER_TMPL.format(unit_type=0).split("\n")
        lines[0] = "2"
        f = tmp_path / "spectral.txt"
        f.write_text("\n".join(lines))
        with pytest.warns(UserWarning, match="MapType"):
            read_data(str(f))

    def test_grid_dims_mismatch_raises(self, tmp_path):
        """A band matrix whose shape contradicts the NbX NbY header line fails."""
        lines = HEADER_TMPL.format(unit_type=0).split("\n")
        lines[5] = "3 3"  # data rows are 2 x 2
        f = tmp_path / "mismatch.txt"
        f.write_text("\n".join(lines))
        with pytest.raises(ValueError, match="NbX"):
            read_data(str(f))

    def test_ragged_band_raises(self, tmp_path):
        """A truncated (non-rectangular) band matrix fails with context."""
        text = HEADER_TMPL.format(unit_type=0) + "1 2 3\n"
        f = tmp_path / "ragged.txt"
        f.write_text(text)
        with pytest.raises(ValueError, match="rectangular"):
            read_data(str(f))

    def test_non_numeric_data_raises(self, tmp_path):
        """Non-numeric values inside a band fail with line context."""
        lines = HEADER_TMPL.format(unit_type=0).split("\n")
        lines[7] = "1 abc"
        f = tmp_path / "nonnumeric.txt"
        f.write_text("\n".join(lines))
        with pytest.raises(ValueError, match="Non-numeric"):
            read_data(str(f))
