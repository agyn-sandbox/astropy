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
        """Initialize the RST writer.

        Parameters
        ----------
        header_rows : list of str or None
            Optional list of column attributes to include as header rows.
            Examples: ["name"], ["name", "unit"]. When None, defaults to
            ["name"].
        """
        # Pass through header_rows to FixedWidth to allow multi-row headers.
        super().__init__(delimiter_pad=None, bookend=False, header_rows=header_rows)

    def write(self, lines):
        # Collect the core lines from FixedWidth writer which include:
        #   [ header rows..., header/body separator, data rows... ]
        lines = super().write(lines)

        # The simple RST table format requires a top rule and a bottom rule
        # identical to the header/body separator. When multiple header rows
        # are present, the separator appears after the last header row. Use
        # the number of header rows to select that rule line.
        header_rows = getattr(self.header, "header_rows", None) or ["name"]
        sep_index = len(header_rows)
        sep_line = lines[sep_index]
        lines = [sep_line] + lines + [sep_line]
        return lines
