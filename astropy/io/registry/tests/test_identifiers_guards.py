import pytest

from astropy.table import Table
from astropy.io import registry as io_registry


def test_fits_identifier_no_args_write_nonfits_path():
    # Should not raise and should not identify as FITS
    formats = io_registry.compat.identify_format(
        "write", Table, "bububu.ecsv", None, [], {}
    )
    assert "fits" not in formats


@pytest.mark.parametrize(
    "suffix",
    [".fits", ".fit", ".fts", ".fits.gz", ".fit.gz", ".fts.gz"],
)
def test_fits_identifier_suffixes(suffix):
    formats = io_registry.compat.identify_format(
        "read", Table, f"/tmp/foo{suffix}", None, [], {}
    )
    assert "fits" in formats


def test_fits_identifier_args_hdu_objects():
    from astropy.io.fits import HDUList, PrimaryHDU, BinTableHDU, TableHDU

    hdul = HDUList([PrimaryHDU()])
    bin_hdu = BinTableHDU.from_columns([])
    tbl_hdu = TableHDU.from_columns([])

    for obj in (hdul, bin_hdu, tbl_hdu):
        formats = io_registry.compat.identify_format(
            "read", Table, None, None, [obj], {}
        )
        assert "fits" in formats


def test_is_fits_nonfits_path_overrides_args_object():
    # Document precedence: non-FITS filepath takes precedence over args object
    from astropy.io.fits import HDUList, PrimaryHDU

    hdul = HDUList([PrimaryHDU()])
    formats = io_registry.compat.identify_format(
        "write", Table, "x.ecsv", None, [hdul], {}
    )
    assert "fits" not in formats


def test_hdf5_identifier_no_args_returns_false():
    from astropy.io.misc.hdf5 import is_hdf5 as is_hdf5_identifier

    assert is_hdf5_identifier("read", None, None) is False


def test_votable_identifier_no_args_returns_false():
    from astropy.io.votable.connect import is_votable as is_votable_identifier

    assert is_votable_identifier("read", None, None) is False
