import pytest

from astropy.io.fits import Card
from astropy.io.fits.card import _format_float


def _extract_card_value(card):
    line = str(card)
    after_equals = line.split("=", 1)[1]
    return after_equals.split("/", 1)[0].strip()


def test_format_float_regression_value_preserved():
    card = Card("FOO", 0.009125, "Gaussian width")
    value_field = _extract_card_value(card)
    assert value_field == "0.009125"
    assert "Gaussian width" in str(card)


@pytest.mark.parametrize("exp", [-60, 0, 60])
def test_format_float_stays_within_20_characters(exp):
    value = (1 - 2 ** -53) * (2 ** exp)
    token = _format_float(value)
    assert len(token) <= 20

    card_value = _extract_card_value(Card("EDGE", value))
    assert card_value == token

    rel_error = abs(float(token) - value)
    if value:
        rel_error /= abs(value)
    assert rel_error <= 1e-12


def test_format_float_exponent_normalization():
    assert _format_float(1e-6) == "1.0E-06"


def test_format_float_adds_decimal_for_non_exponent():
    assert _format_float(42.0).endswith(".0")


def test_complex_numbers_use_updated_formatter():
    complex_value = complex((1 - 2 ** -53) * (2 ** 60), 0.009125)
    card = Card("CMPLX", complex_value)
    text = str(card)
    assert _format_float(complex_value.real) in text
    assert _format_float(complex_value.imag) in text
