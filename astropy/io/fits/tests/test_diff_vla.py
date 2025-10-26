import numpy as np
import pytest

from astropy.io import fits
from astropy.io.fits import FITSDiff


def _write_qd_table(path, arrays):
    col = fits.Column(name="a", format="QD", array=arrays)
    hdu = fits.BinTableHDU.from_columns([col])
    hdul = fits.HDUList([fits.PrimaryHDU(), hdu])
    hdul.writeto(path, overwrite=True)


def _write_pd_table(path, arrays, fmt="PD"):
    col = fits.Column(name="a", format=fmt, array=arrays)
    hdu = fits.BinTableHDU.from_columns([col])
    hdul = fits.HDUList([fits.PrimaryHDU(), hdu])
    hdul.writeto(path, overwrite=True)


def test_identical_q_vla_same_file(tmp_path):
    path = tmp_path / "qd_same.fits"
    _write_qd_table(path, [[0], [0, 0]])

    diff = FITSDiff(str(path), str(path))
    report = diff.report()
    assert diff.identical is True
    assert "No differences found." in report


def test_identical_q_vla_two_files(tmp_path):
    path1 = tmp_path / "qd1.fits"
    path2 = tmp_path / "qd2.fits"
    arrays = [[0], [0, 0]]
    _write_qd_table(path1, arrays)
    _write_qd_table(path2, arrays)

    diff = FITSDiff(str(path1), str(path2))
    assert diff.identical is True


def test_q_vla_empty_and_varying_lengths_identical(tmp_path):
    path = tmp_path / "qd_empty_var.fits"
    arrays = [[], [1, 2], []]
    _write_qd_table(path, arrays)

    diff = FITSDiff(str(path), str(path))
    assert diff.identical is True


def test_q_vla_differences_reported(tmp_path):
    path1 = tmp_path / "qd_diff1.fits"
    path2 = tmp_path / "qd_diff2.fits"

    a1 = [[0], [0, 0]]
    a2 = [[1], [0, 0]]
    _write_qd_table(path1, a1)
    _write_qd_table(path2, a2)

    diff = FITSDiff(str(path1), str(path2))
    report = diff.report()
    assert diff.identical is False
    assert "Column a data differs in row 0:" in report


@pytest.mark.parametrize("fmt,arrays_same,arrays_diff", [
    ("PD", [[0.0], [0.0, 0.0]], [[1.0], [0.0, 0.0]]),
    ("PI", [[0], [0, 0]], [[1], [0, 0]]),
])
def test_p_vla_behavior_unchanged(tmp_path, fmt, arrays_same, arrays_diff):
    # Identical case
    p1 = tmp_path / f"p_same_{fmt}.fits"
    p2 = tmp_path / f"p_same2_{fmt}.fits"
    _write_pd_table(p1, arrays_same, fmt=fmt)
    _write_pd_table(p2, arrays_same, fmt=fmt)
    diff_same = FITSDiff(str(p1), str(p2))
    assert diff_same.identical is True

    # Differing case
    d1 = tmp_path / f"p_diff1_{fmt}.fits"
    d2 = tmp_path / f"p_diff2_{fmt}.fits"
    _write_pd_table(d1, arrays_diff, fmt=fmt)
    _write_pd_table(d2, arrays_same, fmt=fmt)
    diff = FITSDiff(str(d1), str(d2))
    report = diff.report()
    assert diff.identical is False
    assert "Column a data differs in row 0:" in report

