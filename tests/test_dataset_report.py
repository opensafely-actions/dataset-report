import pathlib
from datetime import datetime

import numpy
import pandas
import pytest
from pandas import testing

from analysis import dataset_report


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
        index=[numpy.nan, 0, 1],  # value of nan should be sorted first
        dtype=float,
    )
    testing.assert_series_equal(obs_count, exp_count)


@pytest.mark.parametrize("dtype,num_column_summaries", [(int, 1), (bool, 1)])
def test_get_column_summaries(dtype, num_column_summaries):
    # arrange
    dataframe = pandas.DataFrame(
        {
            # won't be suppressed
            "patient_id": pandas.Series(range(8), dtype=int),
            "is_registered": pandas.Series([1] * 8, dtype=dtype),
        },
    )
    # act
    obs_column_summaries = list(dataset_report.get_column_summaries(dataframe))
    # assert
    assert len(obs_column_summaries) == num_column_summaries


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
