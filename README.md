# dataset-report

dataset-report generates a report for each dataset in an input directory.
_Datasets_ are extracted by [cohort-extractor][].

## Usage

In summary:

* Use cohort-extractor to extract one or more datasets.
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
Remember to replace `[version]` with a dataset-report version:

```yaml
generate_dataset_report:
  run: >
    dataset-report:[version]
      --input-files output/input.csv
      --output-dir output
  needs: [generate_cohort]
  outputs:
    moderately_sensitive:
      dataset_report: output/input.md
```

## Notes for developers

Please see [_DEVELOPERS.md_](DEVELOPERS.md).

[cohort-extractor]: https://docs.opensafely.org/actions-cohortextractor/
