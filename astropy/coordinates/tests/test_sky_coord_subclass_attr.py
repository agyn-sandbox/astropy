# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
import astropy.units as u
from astropy.coordinates import SkyCoord

class CustomCoord(SkyCoord):
    @property
    def prop(self):
        # Access a non-existent attribute to trigger AttributeError from the descriptor
        return self.random_attr


def test_subclass_property_inner_attributeerror_message():
    c = CustomCoord('00h42m30s', '+41d12m00s', frame='icrs')
    with pytest.raises(AttributeError) as excinfo:
        _ = c.prop
    # Ensure the error message mentions the missing inner attribute, not the property name
    assert "random_attr" in str(excinfo.value)
    assert "prop" not in str(excinfo.value)
