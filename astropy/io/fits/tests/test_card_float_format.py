import sys

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


def test_format_float_stays_within_20_characters():
    value = 0.9999999999999999
    token = _format_float(value)
    assert len(token) <= 20
    assert float(token) == value

    card_value = _extract_card_value(Card("EDGE", value))
    assert card_value == token


def test_format_float_exponent_normalization():
    assert _format_float(1e-6) == "1.0E-06"


def test_format_float_adds_decimal_for_non_exponent():
    assert _format_float(42.0).endswith(".0")


def test_complex_numbers_use_updated_formatter():
    complex_value = complex(1.234567890123456e10, 0.009125)
    card = Card("CMPLX", complex_value)
    text = str(card)
    assert _format_float(complex_value.real) in text
    assert _format_float(complex_value.imag) in text


@pytest.mark.parametrize(
    "value",
    [
        (1 - 2 ** -53) * (2 ** 60),
        (1 - 2 ** -53) * (2 ** -60),
        sys.float_info.max,
    ],
)
def test_format_float_raises_when_unrepresentable(value):
    with pytest.raises(ValueError, match="Cannot represent float value"):
        _format_float(value)

    card = Card("BIG", value)
    with pytest.raises(ValueError, match="Cannot represent float value"):
        str(card)
