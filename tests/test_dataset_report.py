import pathlib
from datetime import datetime

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
            # We know the following series won't contain boolean values when they only
            # contain missing values: their types tell us.
            ([numpy.nan, numpy.nan], str),
            ([numpy.nan, numpy.nan], "datetime64[ns]"),
        ],
    )
    def test_with_non_boolean_values(self, data, dtype):
        assert not dataset_report.is_boolean(pandas.Series(data, dtype=dtype))
