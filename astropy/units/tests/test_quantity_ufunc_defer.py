import numpy as np
import pytest

import astropy.units as u
from astropy.units import Quantity
from astropy.units.core import UnitTypeError


class DuckArray:
    """Simple duck-type that carries a Quantity internally and handles ufuncs.

    The purpose is to verify that astropy Quantity returns NotImplemented for
    mixed operations it cannot interpret, allowing this duck to handle them.
    """

    def __init__(self, q):
        assert isinstance(q, Quantity)
        self.q = q

    @property
    def unit(self):
        # Expose a unit attribute to appear quantity-like
        return self.q.unit

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        # Convert any Quantity inputs to their values in our unit, then apply.
        if method != "__call__" or ufunc.nin != 2:
            return NotImplemented
        a, b = inputs
        if isinstance(a, Quantity):
            a = a.to(self.unit).value
        if isinstance(b, Quantity):
            b = b.to(self.unit).value
        # Extract DuckArray payloads
        if isinstance(a, DuckArray):
            a = a.q.to(self.unit).value
        if isinstance(b, DuckArray):
            b = b.q.to(self.unit).value
        res = getattr(ufunc, method)(a, b, **kwargs)
        return DuckArray(res * self.unit)

    # enable comparisons in assertions
    def __eq__(self, other):
        if isinstance(other, DuckArray):
            return np.allclose(other.q.value, self.q.value) and other.q.unit == self.q.unit
        return NotImplemented


def test_mixed_duck_add_defers_to_duck():
    q = 1 * u.m
    duck = DuckArray(1 * u.mm)
    # Quantity should return NotImplemented and let duck handle
    res = np.add(q, duck)
    assert isinstance(res, DuckArray)
    assert res.q.unit == u.m
    assert np.allclose(res.q.value, 1.001)

    # Also for operator
    res2 = q + duck
    assert isinstance(res2, DuckArray)
    assert res2 == res


def test_incompatible_quantities_still_raise():
    a = 1 * u.m
    b = 1 * u.s
    with pytest.raises(UnitTypeError):
        np.add(a, b)


def test_numpy_scalar_and_array_unchanged():
    q = 3 * u.m
    s = 2.0
    arr = np.array([1.0, 2.0])
    res_s = np.add(q, s)
    assert isinstance(res_s, Quantity)
    assert res_s.unit == u.m

    res_arr = np.add(q, arr)
    assert isinstance(res_arr, Quantity)
    assert res_arr.unit == u.m


def test_converter_condition_arg_valueerror_defers():
    # Build a duck that will cause astropy conversion attempt to fail when
    # applying converter(input_) due to non-numeric payload but should defer.
    class BadValueDuck(DuckArray):
        def __init__(self, unit):
            # Intentionally store a string; converter(input_) will raise
            self._unit = unit
            self.q = ("bad",) * u.Quantity(1, unit).unit  # fake to satisfy type

        @property
        def unit(self):
            return self._unit

        def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
            # On deferral, just return a known value to prove it reached here
            if method == "__call__" and ufunc.nin == 2:
                return DuckArray(5 * self.unit)
            return NotImplemented

    q = 1 * u.m
    duck = BadValueDuck(u.m)
    res = np.add(q, duck)
    assert isinstance(res, DuckArray)
    assert res.q == 5 * u.m

