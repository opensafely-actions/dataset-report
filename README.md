# dataset-report

dataset-report generates a report for each dataset in an input directory.
The report is a self-contained HTML file that has the same name as the dataset, but with the extension *html*.

dataset-report's repository contains [this study](analysis/study_definition.py) that extracts a (dummy) dataset and generates [this report][3].

## Disclosure controls

dataset-report applies disclosure controls to each report that it generates,
meaning OpenSAFELY output checkers can be confident that a report is a safe output.
Specifically, dataset-report:

* rounds counts to the nearest five; then
* redacts counts that are less than or equal to five.

The OpenSAFELY documentation has more information on [disclosure controls and safe outputs][2].

## Usage

In summary:

* Use [cohort-extractor][] to extract one or more datasets.
* Use dataset-report to generate a report for each dataset.

Let's walk through an example _project.yaml_.

The following cohort-extractor action extracts a dataset:

```yaml
generate_cohort:
  run: >
    cohortextractor:latest generate_cohort
      --study-definition study_definition
  outputs:
    highly_sensitive:
      cohort: output/input.csv
```

Finally, the following dataset-report reusable action generates a report for the dataset.
Remember to replace `[version]` with [a dataset-report version][1]:

```yaml
generate_dataset_report:
  run: >
    dataset-report:[version]
      --input-files output/input.csv
      --output-dir output
  needs: [generate_cohort]
  outputs:
    moderately_sensitive:
      dataset_report: output/input.html
```

## Notes for developers

Please see [_DEVELOPERS.md_](DEVELOPERS.md).

## A note on versions

Because of a bug in the GitHub workflow that tagged versions,
some versions of dataset-report are ordered incorrectly:
a later version precedes an earlier version,
when versions are sorted by the dates their associated commits were created.
For example, v0.0.19 (later) precedes v0.0.17 (earlier).
The bug was fixed in [#111][].

[1]: https://github.com/opensafely-actions/dataset-report/tags
[2]: https://docs.opensafely.org/releasing-files/
[3]: https://opensafely-actions.github.io/dataset-report/input.html
[#111]: https://github.com/opensafely-actions/dataset-report/pull/111
[cohort-extractor]: https://docs.opensafely.org/actions-cohortextractor/
