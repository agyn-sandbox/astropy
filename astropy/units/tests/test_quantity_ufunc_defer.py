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
    # Multiplication with numpy scalars/arrays should continue to be handled
    # by Quantity as before.
    res_s = np.multiply(q, s)
    assert isinstance(res_s, Quantity)
    assert res_s.unit == u.m

    res_arr = np.multiply(q, arr)
    assert isinstance(res_arr, Quantity)
    assert res_arr.unit == u.m


def test_converter_condition_arg_valueerror_defers():
    # Build a duck that presents a 'value' that is non-numeric so that
    # converter(input_) will raise ValueError in the Quantity path. Quantity
    # should then return NotImplemented and the duck takes over.
    class BadValueDuck:
        def __init__(self, unit):
            self._unit = unit
            self.value = "bad"  # non-numeric to trigger ValueError

        @property
        def unit(self):
            return self._unit

        def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
            if method == "__call__" and ufunc.nin == 2:
                return DuckArray(5 * self.unit)
            return NotImplemented

    q = 1 * u.m
    duck = BadValueDuck(u.m)
    res = np.add(q, duck)
    assert isinstance(res, DuckArray)
    assert res.q == 5 * u.m



def test_converter_discovery_failure_defers():
    # Foreign duck lacks astropy-compatible unit container; getting converter
    # may raise TypeError/AttributeError. Quantity should defer.
    class ForeignNoConv:
        __array_priority__ = 1e6
        def __init__(self):
            self.unit = object()
        def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
            if method == "__call__" and ufunc.nin == 2:
                return 'handled-by-foreign'
            return NotImplemented
    q = 1 * u.m
    f = ForeignNoConv()
    assert np.add(q, f) == 'handled-by-foreign'


def test_converter_application_typeerror_defers():
    # Converter may be constructed, but applying it raises TypeError.
    class ForeignBadApply:
        def __init__(self, unit):
            self._unit = unit
            class Weird:
                # Behaves oddly under numpy array coercion
                def __array__(self):
                    raise TypeError('cannot array-coerce')
            self.value = Weird()
        @property
        def unit(self):
            return self._unit
        def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
            if method == "__call__" and ufunc.nin == 2:
                return 'handled-typeerror'
            return NotImplemented
    q = 1 * u.m
    f = ForeignBadApply(u.m)
    assert np.add(q, f) == 'handled-typeerror'


def test_reduce_accumulate_at_unchanged():
    # Ensure we did not alter behavior for ufunc methods other than __call__
    arr = np.array([1.0, 2.0, 3.0]) * u.m
    # reduce keeps unit for add
    r = np.add.reduce(arr)
    assert isinstance(r, Quantity)
    assert r.unit == u.m
    # accumulate keeps unit and shape
    acc = np.add.accumulate(arr)
    assert isinstance(acc, Quantity)
    assert acc.unit == u.m
    assert acc.shape == arr.shape
    # at modifies in place; for compatibility we only check it runs
    a = arr.copy()
    idx = np.array([0])
    np.add.at(a, idx, 1 * u.m)
    assert a[0].unit == u.m
