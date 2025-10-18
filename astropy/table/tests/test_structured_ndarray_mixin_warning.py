import numpy as np
import pytest

from astropy.table import Table, Column, NdarrayMixin
import astropy.table.table as table_module


def test_futurewarning_on_structured_ndarray_add():
    a = np.array([(1, 'a'), (2, 'b')], dtype=[('x', 'i4'), ('y', 'U1')])
    # During init via list
    with pytest.warns(FutureWarning, match="auto-converts it to astropy.table.NdarrayMixin"):
        t = Table([a], names=['a'])
    # During assignment
    t2 = Table([[1], [2]], names=['c', 'd'])
    with pytest.warns(FutureWarning):
        t2['a'] = a


def test_structured_ndarray_resulting_type_now_and_future(monkeypatch):
    a = np.array([(1, 'a'), (2, 'b')], dtype=[('x', 'i4'), ('y', 'U1')])

    # Current behavior: auto NdarrayMixin, warn
    with pytest.warns(FutureWarning):
        t = Table([a], names=['a'])
    assert isinstance(t['a'], NdarrayMixin)

    # Simulate future behavior: helper returns unchanged data (no conversion)
    def _no_convert(data):
        return data, False

    monkeypatch.setattr(table_module, '_view_structured_ndarray_as_ndarray_mixin', _no_convert)
    t2 = Table([a], names=['a'])
    assert isinstance(t2['a'], Column)
    assert not isinstance(t2['a'], NdarrayMixin)

