import argparse
import functools
import glob
import pathlib

import jinja2
import pandas


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
        return pandas.read_csv(path)
    elif ext == ".feather":
        return pandas.read_feather(path)
    elif ext == ".dta" or ext == ".dta.gz":
        return pandas.read_stata(path)
    else:
        raise ValueError(f"Cannot read '{ext}' files")


def get_memory_usage(dataframe):
    memory_usage = dataframe.memory_usage(index=False)
    memory_usage = memory_usage / 1_000**2
    memory_usage.name = "Size (MB)"
    # At this point, `dataframe.columns` is the same instance as `memory_usage.index`.
    # Consequently, if we change the name of the latter, then we will also change the
    # name of the former. This is undesirable, so we copy `memory_usage.index`.
    memory_usage.index = memory_usage.index.copy()
    memory_usage.index.name = "Column Name"
    return memory_usage


def get_data_types(dataframe):
    dtypes = dataframe.dtypes
    dtypes.name = "Data Type"
    dtypes.index = dtypes.index.copy()
    dtypes.index.name = "Column Name"
    return dtypes


def get_summary(dataframe):
    memory_usage = get_memory_usage(dataframe)
    data_types = get_data_types(dataframe)
    summary = memory_usage.to_frame().join(data_types)
    return summary


def is_boolean(series):
    """Does series contain boolean values?

    Because series may have been read from an untyped file, such as a csv file, it may
    contain boolean values but may not have a boolean data type.
    """
    series = series.dropna()
    return ((series == 0) | (series == 1)).all()


def get_dataset_report(input_file, summary):
    return TEMPLATE.render(input_file=input_file, summary=summary)


def write_dataset_report(output_file, dataset_report):
    with output_file.open("w", encoding="utf-8") as f:
        f.write(dataset_report)


def main():
    args = parse_args()
    input_files = args.input_files
    output_dir = args.output_dir

    for input_file in input_files:
        input_dataframe = read_dataframe(input_file)
        summary = get_summary(input_dataframe)

        output_file = output_dir / f"{get_name(input_file)}.html"
        dataset_report = get_dataset_report(input_file, summary)
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
