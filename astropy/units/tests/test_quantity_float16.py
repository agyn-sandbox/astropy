import numpy as np
import astropy.units as u


def test_quantity_construction_preserves_float16_scalar():
    q = np.float16(1) * u.km
    assert q.dtype == np.float16


def test_quantity_construction_preserves_float16_explicit():
    q = u.Quantity(np.float16(1), u.km)
    assert q.dtype == np.float16


def test_quantity_construction_preserves_float16_array():
    arr = np.array([1, 2], dtype=np.float16)
    q = u.Quantity(arr, u.m)
    assert q.dtype == np.float16


def test_same_unit_operations_preserve_float16_multiply():
    q = u.Quantity([1, 2, 3], u.m, dtype=np.float16)
    r = q * np.float16(2)
    assert r.dtype == np.float16


def test_same_unit_operations_preserve_float16_inplace():
    a = u.Quantity([1, 2, 3], u.m, dtype=np.float16)
    a *= np.float16(3)
    assert a.dtype == np.float16


def test_same_unit_operations_preserve_float16_addition():
    q = u.Quantity([1, 2, 3], u.m, dtype=np.float16)
    b = u.Quantity([1, 1, 1], u.m, dtype=np.float16)
    c = q + b
    assert c.dtype == np.float16


def test_conversion_correctness_without_dtype_assumptions():
    q = u.Quantity(np.float16(2), u.m)
    r = q.to(u.cm)
    assert r.unit == u.cm
    # Do not enforce dtype since conversion scaling may promote dtype.
    assert np.allclose(r.value, np.array(200, dtype=r.value.dtype))

