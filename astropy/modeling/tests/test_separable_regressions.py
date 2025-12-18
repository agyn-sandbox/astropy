# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Regression tests for separability matrix combinations."""

from __future__ import annotations

import numpy as np

from astropy.modeling import models
from astropy.modeling.separable import separability_matrix


def test_separability_plain_and():
    compound = models.Linear1D(10) & models.Linear1D(5)
    expected = np.array([[True, False], [False, True]])
    assert np.array_equal(separability_matrix(compound), expected)


def test_separability_mixed_compound():
    compound = models.Identity(2) & models.Linear1D(10) & models.Linear1D(5)
    expected = np.eye(4, dtype=bool)
    assert np.array_equal(separability_matrix(compound), expected)


def test_separability_nested_compound():
    inner = models.Identity(2)
    compound = models.Identity(2) & inner
    expected = np.eye(4, dtype=bool)
    assert np.array_equal(separability_matrix(compound), expected)


def test_separability_deep_nesting_equivalence():
    a = models.Linear1D(1)
    b = models.Linear1D(2)
    c = models.Linear1D(3)
    d = models.Linear1D(4)
    nested = (a & (b & c)) & d
    flat = a & b & c & d
    assert np.array_equal(separability_matrix(nested), separability_matrix(flat))
