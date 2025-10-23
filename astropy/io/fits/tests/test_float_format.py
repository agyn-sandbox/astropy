import pytest
from astropy.io import fits
from astropy.io.fits.verify import VerifyWarning


def _value_field(card_str):
    """
    Extract the fixed-width value field (up to 20 characters) after '='.
    For standard cards the field is exactly 20 characters and right-justified.
    """
    if '=' not in card_str:
        return ''
    eq = card_str.index('=')
    # After '=' there is typically a space before the field
    start = eq + 1
    if start < len(card_str) and card_str[start] == ' ':
        start += 1
    end = min(start + 20, len(card_str))
    return card_str[start:end]


def test_hierarch_float_minimal_repr_no_truncate():
    c = fits.Card(
        'HIERARCH ESO IFM CL RADIUS',
        0.009125,
        '[m] radius arround actuator to avoid'
    )
    with pytest.warns(None) as rec:
        s = str(c)
    # No VerifyWarning
    assert not any(isinstance(w.message, VerifyWarning) for w in rec)
    # Card is exactly 80 chars
    assert len(s) == 80
    # Value uses minimal representation and comment preserved
    assert '= 0.009125 /' in s
    assert s.endswith('[m] radius arround actuator to avoid')


def test_float_minimal_repr_exponent_uppercase():
    c = fits.Card('FOO', 1e-5)
    s = str(c)
    # Uppercase exponent with two digits
    assert 'E-05' in s
    # Value field is right-justified within 20 chars for standard card
    vf = _value_field(s)
    assert len(vf) == 20
    assert vf.endswith('E-05')
    # Leading spaces indicate right-justification
    assert vf[0] == ' '


def test_float_integer_like_has_decimal_point():
    c = fits.Card('BAR', 2.0)
    s = str(c)
    vf = _value_field(s)
    assert '2.0' in vf


def test_complex_minimal_repr():
    c = fits.Card('BAZ', complex(0.009125, -5e-6))
    s = str(c)
    # Real part minimal, imag part uses normalized small exponent
    assert '0.009125' in s
    assert 'E-06' in s
    vf = _value_field(s)
    # Entire complex literal should fit in the 20-char field in standard cards
    assert len(vf) <= 20


def test_hierarch_equal_sign_shortening():
    # Construct a HIERARCH card near the limit to force '='-shortening logic
    # The specific keyword and value combo aims to exceed by 1 char before shortening
    key = 'HIERARCH ESO VERY LONG KEYWORD TEST'
    comment = 'C' * 30
    c = fits.Card(key, 0.009125, comment)
    with pytest.warns(None) as rec:
        s = str(c)
    # Shortening occurs without raising errors; card length should be 80
    assert len(s) == 80
    # No VerifyWarning
    assert not any(isinstance(w.message, VerifyWarning) for w in rec)
