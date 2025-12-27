import textwrap

import numpy as np
import pytest

from astropy.io import ascii
from astropy.io.ascii.qdp import _get_lines_from_file, _read_table_qdp, _write_table_qdp
from astropy.table import Column, MaskedColumn, Table
from astropy.utils.exceptions import AstropyUserWarning


@pytest.mark.parametrize(
    "command_line",
    ["read serr 1 2", "ReAd SeRr 1 2"],
    ids=["lower", "mixed"],
)
def test_qdp_read_serr_case_insensitive(command_line):
    qdp_text = textwrap.dedent(
        f"""
        {command_line}
        10 0.1 20 0.2
        30 0.3 40 0.4
        """
    ).strip()

    table = _read_table_qdp(qdp_text, names=["c1", "c2"], table_id=0)

    assert table.colnames == ["c1", "c1_err", "c2", "c2_err"]
    assert np.allclose(table["c1"], [10, 30])
    assert np.allclose(table["c1_err"], [0.1, 0.3])
    assert np.allclose(table["c2"], [20, 40])
    assert np.allclose(table["c2_err"], [0.2, 0.4])


@pytest.mark.parametrize(
    (
        "command_lines",
        "names",
        "expected_colnames",
        "expected_checks",
        "data_lines",
    ),
    [
        (
            ["read    terr    1     3"],
            ["col1", "col2", "col3"],
            [
                "col1",
                "col1_perr",
                "col1_nerr",
                "col2",
                "col3",
                "col3_perr",
                "col3_nerr",
            ],
            {
                "col1_perr": [0.1, 0.6],
                "col1_nerr": [0.2, 0.7],
                "col3": [3, 6],
                "col3_perr": [0.4, 0.8],
                "col3_nerr": [0.5, 0.9],
            },
            [
                "1 0.1 0.2 2 3 0.4 0.5",
                "4 0.6 0.7 5 6 0.8 0.9",
            ],
        ),
        (
            ["read serr 2", "read terr 1 ! trailing comment"],
            ["x", "y"],
            ["x", "x_perr", "x_nerr", "y", "y_err"],
            {
                "x_perr": [0.1, 0.4],
                "x_nerr": [0.2, 0.5],
                "y_err": [0.3, 0.6],
            },
            [
                "10 0.1 0.2 20 0.3",
                "30 0.4 0.5 40 0.6",
            ],
        ),
    ],
    ids=["terr_spacing", "inline_comment"],
)
def test_qdp_read_terr_variants(
    command_lines, names, expected_colnames, expected_checks, data_lines
):
    qdp_text = textwrap.dedent(
        "\n".join(command_lines + data_lines)
    ).strip()

    table = _read_table_qdp(qdp_text, names=names, table_id=0)

    assert table.colnames == expected_colnames
    for column, values in expected_checks.items():
        assert np.allclose(table[column], values)


def test_qdp_data_lines_without_commands_are_parsed():
    qdp_text = textwrap.dedent(
        """
        ! pure data follows
        1 2
        3 4
        """
    ).strip()

    table = _read_table_qdp(qdp_text, names=["c1", "c2"], table_id=0)

    assert table.colnames == ["c1", "c2"]
    assert np.allclose(table["c1"], [1, 3])
    assert np.allclose(table["c2"], [2, 4])


def test_qdp_unknown_command_raises():
    qdp_text = textwrap.dedent(
        """
        read xerr 1 2
        1 2 3 4
        """
    ).strip()

    with pytest.raises(ValueError, match="Unrecognized QDP"):
        _read_table_qdp(qdp_text, names=["a", "b"], table_id=0)


def test_get_tables_from_qdp_file(tmp_path):
    example_qdp = """
    ! Swift/XRT hardness ratio of trigger: XXXX, name: BUBU X-2
    ! Columns are as labelled
    READ TERR 1
    READ SERR 2
    ! WT -- hard data
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   -0.212439       0.212439
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   0.000000        0.000000
    NO NO NO NO NO
    ! WT -- soft data
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   0.726155        0.583890
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   2.410935        1.393592
    NO NO NO NO NO
    ! WT -- hardness ratio
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   -0.292553       -0.374935
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   0.000000        -nan
    """

    path = tmp_path / "test.qdp"

    with open(path, "w") as fp:
        print(example_qdp, file=fp)

    table0 = _read_table_qdp(fp.name, names=["MJD", "Rate"], table_id=0)
    assert table0.meta["initial_comments"][0].startswith("Swift")
    assert table0.meta["comments"][0].startswith("WT -- hard data")
    table2 = _read_table_qdp(fp.name, names=["MJD", "Rate"], table_id=2)
    assert table2.meta["initial_comments"][0].startswith("Swift")
    assert table2.meta["comments"][0].startswith("WT -- hardness")
    assert np.isclose(table2["MJD_nerr"][0], -2.37847222222222e-05)


def test_roundtrip(tmp_path):
    example_qdp = """
    ! Swift/XRT hardness ratio of trigger: XXXX, name: BUBU X-2
    ! Columns are as labelled
    READ TERR 1
    READ SERR 2
    ! WT -- hard data
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   NO       0.212439
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   0.000000        0.000000
    NO NO NO NO NO
    ! WT -- soft data
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   0.726155        0.583890
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   2.410935        1.393592
    NO NO NO NO NO
    ! WT -- hardness ratio
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   -0.292553       -0.374935
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   0.000000        NO
    ! Add command, just to raise the warning.
    READ TERR 1
    ! WT -- whatever
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   -0.292553       -0.374935
    NO 1.14467592592593e-05    -1.14467592592593e-05   0.000000        NO
    """

    path = str(tmp_path / "test.qdp")
    path2 = str(tmp_path / "test2.qdp")

    with open(path, "w") as fp:
        print(example_qdp, file=fp)
    with pytest.warns(AstropyUserWarning) as record:
        table = _read_table_qdp(path, names=["MJD", "Rate"], table_id=0)
    assert np.any(
        [
            "This file contains multiple command blocks" in r.message.args[0]
            for r in record
        ]
    )

    _write_table_qdp(table, path2)

    new_table = _read_table_qdp(path2, names=["MJD", "Rate"], table_id=0)

    for col in new_table.colnames:
        is_masked = np.array([np.ma.is_masked(val) for val in new_table[col]])
        if np.any(is_masked):
            # All NaN values are read as such.
            assert np.ma.is_masked(table[col][is_masked])

        is_nan = np.array(
            [(not np.ma.is_masked(val) and np.isnan(val)) for val in new_table[col]]
        )
        # All non-NaN values are the same
        assert np.allclose(new_table[col][~is_nan], table[col][~is_nan])
        if np.any(is_nan):
            # All NaN values are read as such.
            assert np.isnan(table[col][is_nan])
    assert np.allclose(new_table["MJD_perr"], [2.378472e-05, 1.1446759e-05])

    for meta_name in ["initial_comments", "comments"]:
        assert meta_name in new_table.meta


def test_read_example():
    example_qdp = """
        ! Initial comment line 1
        ! Initial comment line 2
        READ TERR 1
        READ SERR 3
        ! Table 0 comment
        !a a(pos) a(neg) b c ce d
        53000.5   0.25  -0.5   1  1.5  3.5 2
        54000.5   1.25  -1.5   2  2.5  4.5 3
        NO NO NO NO NO
        ! Table 1 comment
        !a a(pos) a(neg) b c ce d
        54000.5   2.25  -2.5   NO  3.5  5.5 5
        55000.5   3.25  -3.5   4  4.5  6.5 nan
        """
    dat = ascii.read(example_qdp, format="qdp", table_id=1, names=["a", "b", "c", "d"])
    t = Table.read(
        example_qdp, format="ascii.qdp", table_id=1, names=["a", "b", "c", "d"]
    )

    assert np.allclose(t["a"], [54000, 55000])
    assert t["c_err"][0] == 5.5
    assert np.ma.is_masked(t["b"][0])
    assert np.isnan(t["d"][1])

    for col1, col2 in zip(t.itercols(), dat.itercols()):
        assert np.allclose(col1, col2, equal_nan=True)


def test_roundtrip_example(tmp_path):
    example_qdp = """
        ! Initial comment line 1
        ! Initial comment line 2
        READ TERR 1
        READ SERR 3
        ! Table 0 comment
        !a a(pos) a(neg) b c ce d
        53000.5   0.25  -0.5   1  1.5  3.5 2
        54000.5   1.25  -1.5   2  2.5  4.5 3
        NO NO NO NO NO
        ! Table 1 comment
        !a a(pos) a(neg) b c ce d
        54000.5   2.25  -2.5   NO  3.5  5.5 5
        55000.5   3.25  -3.5   4  4.5  6.5 nan
        """
    test_file = tmp_path / "test.qdp"

    t = Table.read(
        example_qdp, format="ascii.qdp", table_id=1, names=["a", "b", "c", "d"]
    )
    t.write(test_file, err_specs={"terr": [1], "serr": [3]})
    t2 = Table.read(test_file, names=["a", "b", "c", "d"], table_id=0)

    for col1, col2 in zip(t.itercols(), t2.itercols()):
        assert np.allclose(col1, col2, equal_nan=True)


def test_roundtrip_example_comma(tmp_path):
    example_qdp = """
        ! Initial comment line 1
        ! Initial comment line 2
        READ TERR 1
        READ SERR 3
        ! Table 0 comment
        !a,a(pos),a(neg),b,c,ce,d
        53000.5,0.25,-0.5,1,1.5,3.5,2
        54000.5,1.25,-1.5,2,2.5,4.5,3
        NO,NO,NO,NO,NO
        ! Table 1 comment
        !a,a(pos),a(neg),b,c,ce,d
        54000.5,2.25,-2.5,NO,3.5,5.5,5
        55000.5,3.25,-3.5,4,4.5,6.5,nan
        """
    test_file = tmp_path / "test.qdp"

    t = Table.read(
        example_qdp, format="ascii.qdp", table_id=1, names=["a", "b", "c", "d"], sep=","
    )
    t.write(test_file, err_specs={"terr": [1], "serr": [3]})
    t2 = Table.read(test_file, names=["a", "b", "c", "d"], table_id=0)

    # t.values_equal(t2)
    for col1, col2 in zip(t.itercols(), t2.itercols()):
        assert np.allclose(col1, col2, equal_nan=True)


def test_read_write_simple(tmp_path):
    test_file = tmp_path / "test.qdp"
    t1 = Table()
    t1.add_column(Column(name="a", data=[1, 2, 3, 4]))
    t1.add_column(
        MaskedColumn(
            data=[4.0, np.nan, 3.0, 1.0], name="b", mask=[False, False, False, True]
        )
    )
    t1.write(test_file, format="ascii.qdp")
    with pytest.warns(UserWarning) as record:
        t2 = Table.read(test_file, format="ascii.qdp")
    assert np.any(
        [
            "table_id not specified. Reading the first available table"
            in r.message.args[0]
            for r in record
        ]
    )

    assert np.allclose(t2["col1"], t1["a"])
    assert np.all(t2["col1"] == t1["a"])

    good = ~np.isnan(t1["b"])
    assert np.allclose(t2["col2"][good], t1["b"][good])


def test_read_write_simple_specify_name(tmp_path):
    test_file = tmp_path / "test.qdp"
    t1 = Table()
    t1.add_column(Column(name="a", data=[1, 2, 3]))
    # Give a non-None err_specs
    t1.write(test_file, format="ascii.qdp")
    t2 = Table.read(test_file, table_id=0, format="ascii.qdp", names=["a"])
    assert np.all(t2["a"] == t1["a"])


def test_get_lines_from_qdp(tmp_path):
    test_file = str(tmp_path / "test.qdp")
    text_string = "A\nB"
    text_output = _get_lines_from_file(text_string)
    with open(test_file, "w") as fobj:
        print(text_string, file=fobj)
    file_output = _get_lines_from_file(test_file)
    list_output = _get_lines_from_file(["A", "B"])
    for i, line in enumerate(["A", "B"]):
        assert file_output[i] == line
        assert list_output[i] == line
        assert text_output[i] == line
