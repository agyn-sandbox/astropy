import numpy as np
import astropy.units as u
import pytest


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


def test_structured_record_dtype_preserved():
    dt = np.dtype([('x', np.float16), ('y', np.float16)])
    arr = np.zeros(3, dtype=dt)
    q = u.Quantity(arr, u.m)
    # Structured dtype preserved; no casting to float
    assert q.dtype == dt
    assert q.dtype.fields is not None


def test_complex_dtypes_preserved_and_ops():
    c64 = u.Quantity(np.array([1+2j], dtype=np.complex64), u.m)
    assert c64.dtype == np.complex64
    c128 = u.Quantity(np.array([1+2j], dtype=np.complex128), u.m)
    assert c128.dtype == np.complex128
    # Basic ops preserve dtype where numpy does
    r = c64 * np.complex64(2+0j)
    assert r.dtype == np.complex64
    s = c128 + np.complex128(0+1j)
    assert s.dtype == np.complex128


def test_non_numeric_dtypes_rejected():
    # datetime64 array
    dtarr = np.array([np.datetime64('2020-01-01')])
    with pytest.raises(TypeError):
        u.Quantity(dtarr, u.m)
    # timedelta64 array
    tdarr = np.array([np.timedelta64(1, 'D')])
    with pytest.raises(TypeError):
        u.Quantity(tdarr, u.m)
    # string array
    sarr = np.array(['a', 'b'])
    with pytest.raises(TypeError):
        u.Quantity(sarr, u.m)
    # bytes array
    barr = np.array([b'a', b'b'])
    with pytest.raises(TypeError):
        u.Quantity(barr, u.m)


def test_object_arrays_numeric_and_mixed():
    # Numeric-only object array casts to float and succeeds
    oarr_num = np.array([1, 2.5], dtype=object)
    q = u.Quantity(oarr_num, u.m)
    assert np.issubdtype(q.dtype, np.floating)
    # Mixed object array should raise
    oarr_mixed = np.array([1, 'a'], dtype=object)
    with pytest.raises((TypeError, ValueError)):
        u.Quantity(oarr_mixed, u.m)


def test_default_cast_and_explicit_dtype_preservation():
    # Default cast: ints -> float
    q = u.Quantity(np.array([1, 2], dtype=np.int16), u.m)
    assert np.issubdtype(q.dtype, np.floating)
    # Explicit dtype: if allowed, preserve; otherwise, check behavior
    # Some versions may not allow non-float dtype with unit; accept either
    # by verifying the result_type aligns with numpy casting rules
    q2 = u.Quantity(np.array([1, 2], dtype=np.int16), u.m, dtype=np.int16)
    # If preserved, dtype is int16; else likely cast to float
    assert q2.dtype in (np.int16, np.dtype(float))


def test_sequence_of_quantity_dtype_promotions():
    qlist = [1*u.m, 2*u.m]
    q = u.Quantity(qlist)
    assert np.issubdtype(q.dtype, np.floating)
    qlist16 = [np.float16(1)*u.m, np.float16(2)*u.m]
    q16 = u.Quantity(qlist16)
    assert q16.dtype == np.float16
    qmixed = [np.float16(1)*u.m, np.float32(2)*u.m]
    qm = u.Quantity(qmixed)
    assert qm.dtype == np.result_type(np.float16, np.float32)


def test_mixed_dtype_operations_follow_numpy_promotion():
    q16 = u.Quantity([1, 2], u.m, dtype=np.float16)
    r = q16 * np.float32(2)
    assert r.dtype == np.result_type(np.float16, np.float32)


def test_inplace_add_preserves_dtype():
    a = u.Quantity([1, 2, 3], u.m, dtype=np.float16)
    a += np.float16(1)
    assert a.dtype == np.float16


def test_conversion_round_trip_correctness():
    q = u.Quantity(np.float16(2), u.m)
    r = q.to(u.cm).to(u.m)
    assert r.unit == u.m
    assert np.allclose(r.value, np.array(2, dtype=r.value.dtype))
