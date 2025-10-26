import pytest
import astropy.units as u


class Device:
    @u.quantity_input
    def __init__(self, voltage: u.V) -> None:
        self.voltage = voltage


def test_constructor_with_valid_unit():
    d = Device(5 * u.V)
    assert d.voltage == 5 * u.V


def test_constructor_with_invalid_unit():
    with pytest.raises(u.UnitsError):
        Device(5 * u.s)


@u.quantity_input
def f(x: u.m) -> None:
    pass


def test_function_return_none_valid_arg():
    # Should not raise for correct units
    f(1 * u.m)


@u.quantity_input
def g() -> u.dimensionless_unscaled:
    return 2 * u.m / (2 * u.m)


def test_dimensionless_return():
    q = g()
    assert q.unit is u.dimensionless_unscaled
    assert q.value == 1
