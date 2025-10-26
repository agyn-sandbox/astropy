import pytest

import astropy.units as u
from astropy.units import UnrecognizedUnit


def test_unrecognized_compare_with_none():
    x = u.Unit('asdf', parse_strict='silent')
    # Ensure compare to None does not raise and is False
    assert not (x == None)  # noqa: E711
    assert x != None  # noqa: E711


def test_unrecognized_equality_same_name():
    a = u.Unit('mystery', parse_strict='silent')
    b = u.Unit('mystery', parse_strict='silent')
    assert isinstance(a, UnrecognizedUnit)
    assert isinstance(b, UnrecognizedUnit)
    assert a == b


def test_unrecognized_inequality_different_name():
    a = u.Unit('mystery', parse_strict='silent')
    b = u.Unit('other', parse_strict='silent')
    assert a != b


def test_unrecognized_vs_recognized():
    x = u.Unit('asdf', parse_strict='silent')
    assert x != u.m
    assert not (x == u.m)


def test_unrecognized_vs_quantity():
    x = u.Unit('asdf', parse_strict='silent')
    q = 5 * u.m
    assert x != q
    assert not (x == q)


def test_unrecognized_vs_non_unit_like():
    x = u.Unit('asdf', parse_strict='silent')
    assert not (x == 1)
    assert x != 1
    class Foo:
        pass
    obj = Foo()
    assert not (x == obj)
    assert x != obj

