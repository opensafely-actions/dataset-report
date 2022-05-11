import pathlib

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


@pytest.mark.xfail(
    reason="The argument and the return value share an index instance",
    strict=True,
)
def test_get_memory_usage(dataframe):
    memory_usage = dataset_report.get_memory_usage(dataframe)
    assert dataframe.columns is not memory_usage.index
