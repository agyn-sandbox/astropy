# Licensed under a 3-clause BSD style license
"""
:Author: Simon Gibbons (simongibbons@gmail.com)
"""


from .core import DefaultSplitter
from .fixedwidth import (
    FixedWidth,
    FixedWidthData,
    FixedWidthHeader,
    FixedWidthTwoLineDataSplitter,
)


class SimpleRSTHeader(FixedWidthHeader):
    position_line = 0
    start_line = 1
    splitter_class = DefaultSplitter
    position_char = "="

    def get_fixedwidth_params(self, line):
        vals, starts, ends = super().get_fixedwidth_params(line)
        # The right hand column can be unbounded
        ends[-1] = None
        return vals, starts, ends


class SimpleRSTData(FixedWidthData):
    start_line = 3
    end_line = -1
    splitter_class = FixedWidthTwoLineDataSplitter


class RST(FixedWidth):
    """reStructuredText simple format table.

    See: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#simple-tables

    Example::

        ==== ===== ======
        Col1  Col2  Col3
        ==== ===== ======
          1    2.3  Hello
          2    4.5  Worlds
        ==== ===== ======

    Currently there is no support for reading tables which utilize continuation lines,
    or for ones which define column spans through the use of an additional
    line of dashes in the header.

    """

    _format_name = "rst"
    _description = "reStructuredText simple table"
    data_class = SimpleRSTData
    header_class = SimpleRSTHeader

    def __init__(self, header_rows=None):
        if header_rows is not None and len(header_rows) == 0:
            raise TypeError("RST writer requires at least one header row.")
        super().__init__(delimiter_pad=None, bookend=False, header_rows=header_rows)

    def write(self, table):
        header_rows = getattr(self.header, "header_rows", ["name"])
        if not header_rows:
            raise TypeError("RST writer requires at least one header row.")

        lines = super().write(table)

        prefix_len = 0
        while prefix_len < len(lines) and (
            not lines[prefix_len].strip() or lines[prefix_len].startswith("#")
        ):
            prefix_len += 1

        prefix = lines[:prefix_len]
        body = lines[prefix_len:]

        if len(header_rows) == 1:
            if len(body) <= len(header_rows):
                return lines
            border_line = body[len(header_rows)]
            return prefix + [border_line] + body + [border_line]

        cols = self.data.cols

        header_values = []
        for attr in header_rows:
            row = []
            for col in cols:
                value = getattr(col.info, attr, None)
                row.append("" if value is None else str(value))
            header_values.append(row)

        data_rows = list(zip(*[col.str_vals for col in cols])) if cols else []

        widths = []
        for idx, col in enumerate(cols):
            width = 0
            for row in header_values:
                width = max(width, len(row[idx]))
            for row in data_rows:
                width = max(width, len(row[idx]))
            widths.append(max(1, width))

        def make_border(fill_char):
            segments = [fill_char * (width + 2) for width in widths]
            return "+" + "+".join(segments) + "+"

        def format_row(row):
            cells = [
                " " + value.rjust(width) + " "
                for value, width in zip(row, widths)
            ]
            return "|" + "|".join(cells) + "|"

        grid_lines = [make_border("-")]

        for idx, row in enumerate(header_values):
            grid_lines.append(format_row(row))
            if idx < len(header_values) - 1:
                grid_lines.append(make_border("-"))

        grid_lines.append(make_border("="))

        if data_rows:
            for row in data_rows:
                grid_lines.append(format_row(row))
                grid_lines.append(make_border("-"))
        else:
            grid_lines.append(make_border("-"))

        return prefix + grid_lines
