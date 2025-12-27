# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest

from astropy import units as u
from astropy.io.ascii.rst import RST
from astropy.table import QTable, Table


def _split_lines(text):
    return text.splitlines()


def test_header_rows_empty_error():
    with pytest.raises(TypeError, match="RST writer requires at least one header row."):
        RST(header_rows=[])

    writer = RST()
    writer.header.header_rows = []
    table = Table({"a": [1]})

    with pytest.raises(TypeError, match="RST writer requires at least one header row."):
        writer.write(table)


def test_single_header_row_default_names():
    table = Table(
        {
            "Col1": [1.2, 2.4],
            "Col2": ['"hello"', "'s worlds"],
            "Col3": [1, 2],
            "Col4": ["a", "2"],
        }
    )

    lines = RST().write(table)

    expected = _split_lines(
        """\
==== ========= ==== ====
Col1      Col2 Col3 Col4
==== ========= ==== ====
 1.2   "hello"    1    a
 2.4 's worlds    2    2
==== ========= ==== ====
"""
    )

    assert lines == expected


def test_single_header_row_units_only():
    table = QTable({"a": [1, 2] * u.m, "bbb": [3, 4] * u.s})

    lines = RST(header_rows=["unit"]).write(table)

    expected = _split_lines(
        """\
=== ===
  m   s
=== ===
1.0 3.0
2.0 4.0
=== ===
"""
    )

    assert lines == expected


def test_two_header_rows_grid_table():
    table = QTable({"a": [1, 2] * u.m, "bbb": [3, 4] * u.s})

    lines = RST(header_rows=["name", "unit"]).write(table)

    expected = _split_lines(
        """\
+-----+-----+
|   a | bbb |
+-----+-----+
|   m |   s |
+=====+=====+
| 1.0 | 3.0 |
+-----+-----+
| 2.0 | 4.0 |
+-----+-----+
"""
    )

    assert lines == expected


def test_three_header_rows_alignment():
    table = QTable({"a": [1, 2] * u.m, "bbb": [3, 4] * u.s})

    lines = RST(header_rows=["dtype", "name", "unit"]).write(table)

    expected = _split_lines(
        """\
+---------+---------+
| float64 | float64 |
+---------+---------+
|       a |     bbb |
+---------+---------+
|       m |       s |
+=========+=========+
|     1.0 |     3.0 |
+---------+---------+
|     2.0 |     4.0 |
+---------+---------+
"""
    )

    assert lines == expected
