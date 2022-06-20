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
    from_csv = False
    if (ext := get_extension(path)) in [".csv", ".csv.gz"]:
        from_csv = True
        dataframe = pandas.read_csv(path)
    elif ext in [".feather"]:
        dataframe = pandas.read_feather(path)
    elif ext in [".dta", ".dta.gz"]:
        dataframe = pandas.read_stata(path)
    else:
        raise ValueError(f"Cannot read '{ext}' files")
    # It's useful to know whether a dataframe was read from a csv when summarizing the
    # columns later.
    dataframe.attrs["from_csv"] = from_csv
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


def is_bool_as_int(series):
    """Does series have bool values but an int dtype?"""
    # numpy.nan will ensure an int series becomes a float series, so we need to check
    # for both int and float
    if not types.is_bool_dtype(series) and types.is_numeric_dtype(series):
        series = series.dropna()
        return ((series == 0) | (series == 1)).all()
    else:
        return False


def select(dataframe, func):
    """Returns a subset of dataframe's columns, based on func.

    func is a filter: if it returns True, then the column is included; if it returns
    False, then the column is excluded.
    """
    return dataframe.loc[:, [k for k, v in dataframe.items() if func(v)]]


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


def _count_values_from_internal_domain(series):
    return series.value_counts(dropna=False)


def _count_values_from_external_domain(series, domain):
    return pandas.Series({x: sum(series == x) for x in domain}, name=series.name)


def count_values(series, domain=None, normalize=False, *, base, threshold):
    """Counts values in series.

    By default, counts values, including missing values, in series from the internal
    domain of series. Otherwise, counts values in series from the external domain.

    Rounds counts to the nearest base; then suppresses counts less than or equal to
    threshold.
    """
    if domain is None:
        count = _count_values_from_internal_domain(series)
    else:
        count = _count_values_from_external_domain(series, domain)
    count.index.name = "Column Value"
    count = count.pipe(round_to_nearest, base).pipe(suppress, threshold)
    if normalize:
        count = count / count.sum() * 100
    count = count.sort_index(na_position="first")
    return count


def get_counts(dataframe, counter):
    counts = dataframe.apply(counter)
    counts["Statistic"] = "Count"
    counts = counts.set_index("Statistic", append=True)
    counts.index = counts.index.reorder_levels([1, 0])

    percentages = dataframe.apply(counter, normalize=True)
    percentages["Statistic"] = "Percentage"
    percentages = percentages.set_index("Statistic", append=True)
    percentages.index = percentages.index.reorder_levels([1, 0])

    summary = pandas.concat([counts, percentages])
    summary = summary.fillna(0)
    summary = summary.transpose()
    return summary


def get_dataset_report(input_file, table_summary, dtype_summaries):
    return TEMPLATE.render(
        input_file=input_file,
        table_summary=table_summary,
        dtype_summaries=dtype_summaries,
    )


def write_dataset_report(output_file, dataset_report):
    with output_file.open("w", encoding="utf-8") as f:
        f.write(dataset_report)


def main():
    args = parse_args()
    input_files = args.input_files
    output_dir = args.output_dir

    # Repeatedly passing base and threshold is error-prone, so we create a partial
    # object to pass them once.
    root_count_values = functools.partial(count_values, base=5, threshold=5)

    def summarize_bool_as_int(input_dataframe, dtype_summaries):
        if not input_dataframe.attrs["from_csv"]:
            return

        bool_as_int_dataframe = select(input_dataframe, is_bool_as_int)
        if bool_as_int_dataframe.empty:
            return

        counter = functools.partial(root_count_values, domain=[0, 1, numpy.nan])
        summary = get_counts(bool_as_int_dataframe, counter)
        dtype_summaries.append(("Bool as int", summary))

    def summarize_bool(input_dataframe, dtype_summaries):
        bool_dataframe = select(input_dataframe, types.is_bool_dtype)
        if bool_dataframe.empty:
            return

        counter = functools.partial(root_count_values, domain=[False, True, numpy.nan])
        summary = get_counts(bool_dataframe, counter)
        dtype_summaries.append(("Bool", summary))

    for input_file in input_files:
        input_dataframe = read_dataframe(input_file)
        table_summary = get_table_summary(input_dataframe)
        dtype_summaries = []
        summarize_bool_as_int(input_dataframe, dtype_summaries)
        summarize_bool(input_dataframe, dtype_summaries)
        output_file = output_dir / f"{get_name(input_file)}.html"
        dataset_report = get_dataset_report(input_file, table_summary, dtype_summaries)
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
