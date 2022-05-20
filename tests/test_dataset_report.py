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


def test_get_table_summary():
    # arrange
    dataframe = pandas.DataFrame(
        {
            "patient_id": pandas.Series([1, 2, 3, 4], dtype=int),
            "is_registered": pandas.Series([1, 0, numpy.nan, numpy.nan], dtype=float),
        },
    )
    # act
    obs_table_summary = dataset_report.get_table_summary(dataframe)
    # assert
    del obs_table_summary["Size (MB)"]  # don't test
    del obs_table_summary["Data Type"]  # don't test
    exp_table_summary = pandas.DataFrame(
        {
            "Count of missing values": pandas.Series(
                [0, 2],
                index=dataframe.columns,
                dtype=int,
            ),
            "Percentage of missing values": pandas.Series(
                [0, 50],
                index=dataframe.columns,
                dtype=float,
            ),
        }
    )
    testing.assert_frame_equal(obs_table_summary, exp_table_summary)


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


def test_get_column_summaries():
    # arrange
    dataframe = pandas.DataFrame(
        {
            # won't be suppressed
            "patient_id": pandas.Series(range(8), dtype=int),
            "is_registered": pandas.Series([1] * 8, dtype=int),
        },
    )
    # act
    obs_column_summaries = list(dataset_report.get_column_summaries(dataframe))
    # assert
    assert len(obs_column_summaries) == 1
    obs_name, obs_summary = obs_column_summaries[0]
    assert obs_name == "is_registered"
    exp_index = pandas.Index([1], dtype=int, name="Column Value")
    exp_summary = pandas.DataFrame(
        {
            # will be rounded
            "Count": pandas.Series([10], index=exp_index, dtype=int),
            "Percentage": pandas.Series([100], index=exp_index, dtype=float),
        }
    )
    testing.assert_frame_equal(obs_summary, exp_summary)


class TestIsBoolean:
    @pytest.mark.parametrize(
        "data,dtype",
        [
            ([0, 1], int),
            ([0, 1], float),
            ([numpy.nan, 1], float),
            ([False, True], bool),
            # We have no way of knowing whether the following series should contain
            # boolean values when it only contains missing values. However, the
            # distinction doesn't matter in practice.
            ([numpy.nan, numpy.nan], float),
        ],
    )
    def test_with_boolean_values(self, data, dtype):
        assert dataset_report.is_boolean(pandas.Series(data, dtype=dtype))

    @pytest.mark.parametrize(
        "data,dtype",
        [
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
        assert not dataset_report.is_boolean(pandas.Series(data, dtype=dtype))
