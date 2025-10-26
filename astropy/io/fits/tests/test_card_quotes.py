import pytest

from astropy.io.fits import Card


def roundtrip_value(val):
    # Create card, stringify, parse back, and return value
    c = Card('TEST', val, 'comment here')
    s = str(c)
    c2 = Card.fromstring(s)
    return c2.value


def test_trailing_double_quote_ranges():
    for n in list(range(50, 81)) + list(range(120, 141)):
        val = 'x' * n + "''"
        assert roundtrip_value(val) == val


def test_embedded_double_quote_ranges():
    for n in list(range(50, 81)) + list(range(120, 141)):
        val = 'x' * n + "''" + 'x' * 10
        assert roundtrip_value(val) == val


@pytest.mark.parametrize(
    'val',
    [
        "''",
        "a''b",
        "a''''b",
        'x' * 66 + "''",
        'x' * 67 + "''",
        'x' * 68 + "''",
        'x' * 66 + "''" + 'y' * 20,
    ],
)
def test_boundary_cases_and_multiples(val):
    assert roundtrip_value(val) == val


def test_long_strings_require_continue():
    val = "long value " * 10 + "''" + " more"
    assert roundtrip_value(val) == val


def test_no_regression_empty_and_ordinary():
    assert roundtrip_value("") == ""
    assert roundtrip_value("simple") == "simple"
    assert roundtrip_value("it's fine") == "it's fine"
