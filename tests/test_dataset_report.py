import datetime
import pathlib

import numpy
import pandas
import pytest

from analysis import dataset_report


@pytest.fixture
def dataframe():
    return pandas.DataFrame(
        {
            "patient_id": [1],
            "is_registered": [True],
            "is_dead": [False],
            "stp_code": ["STP0"],
            "has_sbp_event": [True],
        }
    )


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


@pytest.mark.parametrize(
    "summary_function",
    [
        dataset_report.get_memory_usage,
        dataset_report.get_data_types,
    ],
)
def test_summary_function(summary_function, dataframe):
    # Test that the argument and the return value do not share an index instance.
    summary = summary_function(dataframe)
    assert dataframe.columns is not summary.index


class TestIsBool:
    def test_with_boolean(self):
        assert dataset_report.is_boolean(pandas.Series([0, 1], dtype=int))
        assert dataset_report.is_boolean(pandas.Series([0, 1], dtype=float))
        assert dataset_report.is_boolean(pandas.Series([numpy.nan, 1], dtype=float))
        assert dataset_report.is_boolean(pandas.Series([False, True], dtype=bool))

    def test_with_non_boolean(self):
        assert not dataset_report.is_boolean(pandas.Series([0, 2], dtype=int))
        assert not dataset_report.is_boolean(pandas.Series([0.1, 0.2], dtype=float))
        assert not dataset_report.is_boolean(pandas.Series([numpy.nan, 2], dtype=float))
        assert not dataset_report.is_boolean(pandas.Series(["0", "1"], dtype=str))
        assert not dataset_report.is_boolean(
            pandas.Series(
                [
                    datetime.datetime(2022, 1, 1),
                    datetime.datetime(2022, 1, 2),
                ],
                dtype="datetime64[ns]",
            )
        )
