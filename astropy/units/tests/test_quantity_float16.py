import numpy as np
import numpy.ma as ma

import astropy.units as u


def test_float16_mul_unit_preserves_dtype():
    q = np.float16(1) * u.km
    assert q.dtype == np.float16


def test_float16_quantity_creation_preserves_dtype():
    q = u.Quantity(np.float16(2), u.m)
    assert q.dtype == np.float16


def test_float16_array_mul_unit_preserves_dtype():
    q = np.array([1], dtype=np.float16) * u.km
    assert q.dtype == np.float16


def test_float16_arithmetic_promotion_rules():
    q16 = u.Quantity(np.float16(1), u.m)
    q64 = u.Quantity(np.float64(1), u.m)
    assert (q16 + q64).dtype == np.float64


def test_float16_masked_array_preserves_dtype():
    masked = ma.MaskedArray(np.array([1], dtype=np.float16), mask=[False])
    q = u.Quantity(masked, u.m)
    assert q.dtype == np.float16


def test_float16_conversion_value_correct():
    q = (np.float16(1) * u.km).to(u.m)
    # dtype may remain float16; ensure numerical value is correct.
    assert np.all(q.value == np.float16(1000)) or np.all(q.value == 1000)

