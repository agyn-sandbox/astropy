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
        """RST writer/reader.

        Parameters
        ----------
        header_rows : list of str, optional
            List of column attributes to include as header rows prior to the
            separator line. Typical values include "name", "unit",
            "dtype", "format", or "description". If not provided the
            default is ["name"].
        """
        # For RST simple tables we don't use delimiter padding and there are
        # no bookend characters. Allow passing header_rows through to the
        # FixedWidth base class so that multiple header rows (e.g. name + unit)
        # are supported consistently with other fixed-width writers.
        super().__init__(delimiter_pad=None, bookend=False, header_rows=header_rows)

    def write(self, lines):
        # Delegate to FixedWidth for composing header rows (including any
        # requested extra header rows) and the single separator line that
        # precedes data rows. Then wrap with the RST-required top and bottom
        # border lines (copies of the separator line).
        lines = super().write(lines)
        # The separator line is appended by FixedWidthData.write() after all
        # header rows. Compute its index robustly even when there are multiple
        # header rows.
        header_rows = getattr(self.header, "header_rows", ["name"]) or []
        sep_index = len(header_rows)
        sep_line = lines[sep_index]
        lines = [sep_line] + lines + [sep_line]
        return lines
