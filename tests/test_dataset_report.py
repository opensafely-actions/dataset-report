import pathlib
from datetime import datetime

import numpy
import pandas
import pytest
from pandas import testing

from analysis import dataset_report


@pytest.fixture
def dataframe_writer(tmp_path):
    """Returns a function that, when called, writes a dataframe to a temporary directory
    and returns the path to the dataframe."""
    # We use a function to return a function (a factory) to create a closure around
    # tmp_path, and to keep the logic that decides which DataFrame.to_* method to call
    # as simple as possible.
    csv_exts = {".csv", ".csv.gz"}
    feather_exts = {".feather"}
    dta_exts = {".dta", ".dta.gz"}

    def writer(ext):
        assert ext in csv_exts | feather_exts | dta_exts
        f_path = tmp_path / f"input{ext}"
        dataframe = pandas.DataFrame({"patient_id": pandas.Series(range(5), dtype=int)})
        if ext in [".csv", ".csv.gz"]:
            dataframe.to_csv(f_path)
        elif ext in [".feather"]:
            dataframe.to_feather(f_path)
        else:
            dataframe.to_stata(f_path)
        return f_path

    return writer


@pytest.mark.parametrize(
    "path,name",
    [
        (pathlib.Path("output/input.csv"), "input"),
        (pathlib.Path("output/input.csv.gz"), "input"),
        (pathlib.Path("output/input.feather"), "input"),
        (pathlib.Path("output/input.dta"), "input"),
        (pathlib.Path("output/input.dta.gz"), "input"),
    ],
)
def test_get_name(path, name):
    assert dataset_report.get_name(path) == name


class TestReadDataframe:
    @pytest.mark.parametrize(
        "ext,from_csv",
        [
            (".csv", True),
            (".csv.gz", True),
            (".feather", False),
            (".dta", False),
            (".dta.gz", False),
        ],
    )
    def test_read_supported_file_type(self, dataframe_writer, ext, from_csv):
        f_path = dataframe_writer(ext)
        dataframe = dataset_report.read_dataframe(f_path)
        assert dataframe.attrs["from_csv"] is from_csv
        assert dataframe.columns.name == "Column Name"

    def test_read_unsupported_file_type(self):
        with pytest.raises(ValueError):
            dataset_report.read_dataframe(pathlib.Path("input.xlsx"))


class TestIsEmpty:
    def test_with_empty_series(self):
        series = pandas.Series([numpy.nan, numpy.nan, numpy.nan], dtype=float)
        assert dataset_report.is_empty(series)

    @pytest.mark.parametrize(
        "series",
        [
            pandas.Series([0, 1, 1], dtype=int),
            pandas.Series([0, 1, numpy.nan], dtype=float),
        ],
    )
    def test_with_non_empty_series(self, series):
        assert not dataset_report.is_empty(series)


def test_count_values():
    # arrange
    # value of 0:   there are 5, not rounded, suppressed
    # value of 1:   there are 6, rounded down to 5, suppressed
    # value of nan: there are 8, rounded up to 10, not suppressed
    series = pandas.Series([0] * 5 + [1] * 6 + [numpy.nan] * 8, dtype=float)
    # act
    obs_count = dataset_report.count_values(series, base=5, threshold=5)
    # assert
    exp_count = pandas.Series(
        [10, numpy.nan, numpy.nan],
        # value of nan should be sorted first
        index=pandas.Index([numpy.nan, 0, 1], name="Column Value"),
        dtype=float,
    )
    testing.assert_series_equal(obs_count, exp_count)


class TestIsBoolAsInt:
    @pytest.mark.parametrize(
        "data,dtype",
        [
            ([0, 1], int),
            ([0, 1], float),
            ([numpy.nan, 1], float),
            # We have no way of knowing whether the following series should contain
            # boolean values when it only contains missing values. However, the
            # distinction doesn't matter in practice.
            ([numpy.nan, numpy.nan], float),
        ],
    )
    def test_with_boolean_values(self, data, dtype):
        assert dataset_report.is_bool_as_int(pandas.Series(data, dtype=dtype))

    @pytest.mark.parametrize(
        "data,dtype",
        [
            ([False, True], bool),
            ([0, 2], int),
            ([0.1, 0.2], float),
            ([numpy.nan, 2], float),
            (["0", "1"], str),
            ([datetime(2022, 1, 1), datetime(2022, 1, 2)], "datetime64[ns]"),
            (["0", "1"], "category"),
            # We know the following series won't contain boolean values when they only
            # contain missing values: their types tell us.
            ([numpy.nan, numpy.nan], str),
            ([numpy.nan, numpy.nan], "datetime64[ns]"),
            ([numpy.nan, numpy.nan], "category"),
        ],
    )
    def test_with_non_boolean_values(self, data, dtype):
        assert not dataset_report.is_bool_as_int(pandas.Series(data, dtype=dtype))
