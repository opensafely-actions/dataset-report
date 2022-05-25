import argparse
import functools
import glob
import pathlib

import jinja2
import numpy
import pandas
from pandas.api import types


# Template
# --------


@functools.singledispatch
def finalize(value):
    """Processes the value of a template variable before it is rendered."""
    # This is the default "do nothing" path.
    return value


@finalize.register
def _(value: pandas.DataFrame):
    return value.to_html()


ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader("analysis/templates"),
    finalize=finalize,
)
TEMPLATE = ENVIRONMENT.get_template("dataset_report.html")


# Application
# -----------


def get_extension(path):
    return "".join(path.suffixes)


def get_name(path):
    return path.name.split(".")[0]


def read_dataframe(path):
    ext = get_extension(path)
    if ext == ".csv" or ext == ".csv.gz":
        dataframe = pandas.read_csv(path)
    elif ext == ".feather":
        dataframe = pandas.read_feather(path)
    elif ext == ".dta" or ext == ".dta.gz":
        dataframe = pandas.read_stata(path)
    else:
        raise ValueError(f"Cannot read '{ext}' files")
    # We give the column index a name now, because it's preserved when summaries are
    # computed later.
    dataframe.columns.name = "Column Name"
    return dataframe


def is_empty(series):
    """Does series contain only missing values?"""
    return series.isna().all()


def get_table_summary(dataframe):
    memory_usage = dataframe.memory_usage(index=False)
    memory_usage = memory_usage / 1_000**2
    return pandas.DataFrame(
        {
            "Size (MB)": memory_usage,
            "Data Type": dataframe.dtypes,
            "Empty": dataframe.apply(is_empty),
        },
    )


def is_boolean(series):
    """Does series contain boolean values?

    Because series may have been read from an untyped file, such as a csv file, it may
    contain boolean values but may not have a boolean data type.
    """
    if not (types.is_bool_dtype(series) or types.is_numeric_dtype(series)):
        return False
    series = series.dropna()
    return ((series == 0) | (series == 1)).all()


def round_to_nearest(series, base):
    """Rounds values in series to the nearest base."""
    # ndigits=0 ensures the return value is a whole number, but with the same type as x
    series_copy = series.apply(lambda x: base * round(x / base, ndigits=0))
    try:
        return series_copy.astype(int)
    except ValueError:
        # series contained nan
        return series_copy


def suppress(series, threshold):
    """Replaces values in series less than or equal to threshold with missing values."""
    series_copy = series.copy()
    series_copy[series_copy <= threshold] = numpy.nan  # in place
    return series_copy


def count_values(series, *, base, threshold):
    """Counts values, including missing values, in series.

    Rounds counts to the nearest base; then suppresses counts less than or equal to
    threshold.
    """
    count = series.value_counts(dropna=False)
    count = count.pipe(round_to_nearest, base).pipe(suppress, threshold)
    count = count.sort_index(na_position="first")
    return count


def get_column_summaries(dataframe):
    for name, series in dataframe.items():
        if name == "patient_id":
            continue

        if is_boolean(series):
            count = count_values(series, threshold=5, base=5)
            percentage = count / count.sum() * 100
            summary = pandas.DataFrame({"Count": count, "Percentage": percentage})
            summary.index.name = "Column Value"
            yield name, summary


def get_dataset_report(input_file, table_summary, column_summaries):
    return TEMPLATE.render(
        input_file=input_file,
        table_summary=table_summary,
        column_summaries=column_summaries,
    )


def write_dataset_report(output_file, dataset_report):
    with output_file.open("w", encoding="utf-8") as f:
        f.write(dataset_report)


def main():
    args = parse_args()
    input_files = args.input_files
    output_dir = args.output_dir

    for input_file in input_files:
        input_dataframe = read_dataframe(input_file)
        table_summary = get_table_summary(input_dataframe)
        column_summaries = get_column_summaries(input_dataframe)

        output_file = output_dir / f"{get_name(input_file)}.html"
        dataset_report = get_dataset_report(input_file, table_summary, column_summaries)
        write_dataset_report(output_file, dataset_report)


# Argument parsing
# ----------------


def get_path(*args):
    return pathlib.Path(*args)


def match_paths(pattern):
    yield from (get_path(x) for x in glob.iglob(pattern))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-files",
        required=True,
        type=match_paths,
        help="Glob pattern for matching one or more input files",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=get_path,
        help="Path to the output directory",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
