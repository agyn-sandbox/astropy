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


# Additional inexact dtype coverage (float32/float128, complex64/complex128)

def test_float32_and_float128_preserve_dtype_on_construction_and_mul():
    q32 = u.Quantity(np.float32(3), u.m)
    assert q32.dtype == np.float32
    q32m = np.float32(4) * u.s
    assert q32m.dtype == np.float32

    # float128 may not exist on all platforms; guard accordingly
    if hasattr(np, 'float128'):
        q128 = u.Quantity(np.float128(5), u.m)
        assert q128.dtype == np.float128
        q128m = np.float128(6) * u.s
        assert q128m.dtype == np.float128


def test_complex64_and_complex128_preserve_dtype_on_construction_and_mul():
    c64 = u.Quantity(np.complex64(1+2j), u.m)
    assert c64.dtype == np.complex64
    c64m = np.complex64(2+3j) * u.s
    assert c64m.dtype == np.complex64

    c128 = u.Quantity(np.complex128(1+2j), u.m)
    assert c128.dtype == np.complex128
    c128m = np.complex128(2+3j) * u.s
    assert c128m.dtype == np.complex128
