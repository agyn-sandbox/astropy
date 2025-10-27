import numpy as np
import pytest

from astropy import units as u


class TestQuantityFloat16Preserve:
    def test_scalar_float16_preserved(self):
        x = np.float16(1.5)
        q = u.Quantity(x, u.m)
        assert q.dtype == np.float16

    def test_0d_array_float16_preserved(self):
        x = np.array(2.5, dtype=np.float16)
        q = u.Quantity(x, u.s)
        assert q.dtype == np.float16

    def test_1d_array_float16_preserved(self):
        x = np.array([1.0, 2.0], dtype=np.float16)
        q = u.Quantity(x, u.m)
        assert q.dtype == np.float16

    def test_unit_multiply_divide_preserves_dtype(self):
        x = np.array([1.0, 2.0], dtype=np.float16)
        q = x * u.m
        assert isinstance(q, u.Quantity)
        assert q.dtype == np.float16
        q2 = q / u.s
        assert q2.dtype == np.float16

    def test_round_trip_to_value_preserves_dtype(self):
        x = np.array([1.0, 2.0], dtype=np.float16)
        q = u.Quantity(x, u.m)
        v = q.to_value(u.m)
        assert isinstance(v, np.ndarray)
        assert v.dtype == np.float16

    def test_float32_64_unchanged(self):
        for dt in (np.float32, np.float64):
            x = np.array([1.0, 2.0], dtype=dt)
            q = u.Quantity(x, u.m)
            assert q.dtype == dt

    def test_integers_default_to_float64(self):
        x = np.array([1, 2, 3], dtype=np.int32)
        q = u.Quantity(x, u.m)
        assert q.dtype == np.float64

    def test_mixed_list_numpy_resolution(self):
        # numpy decides the dtype; float takes precedence
        x = [1, 2.0, 3]
        q = u.Quantity(x, u.m)
        assert q.dtype == np.float64

    def test_object_numeric_list_defaults_float64(self):
        x = np.array([1, 2.0, 3], dtype=object)
        q = u.Quantity(x, u.m)
        assert q.dtype == np.float64

