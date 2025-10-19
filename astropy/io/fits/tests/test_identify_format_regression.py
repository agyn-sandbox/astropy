def test_identify_format_write_nonfits_path_no_raise_and_not_fits():
    from astropy.io.registry import identify_format
    from astropy.table import Table

    # Non-FITS filepath; no file I/O, no args
    formats = identify_format('write', Table, 'bububu.ecsv', None, [], {})
    assert 'fits' not in formats


def test_is_fits_write_with_nonfits_path_returns_false():
    from astropy.io.fits.connect import is_fits

    assert is_fits('write', 'bububu.ecsv', None) is False

