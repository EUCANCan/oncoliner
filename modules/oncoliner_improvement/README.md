# ONCOLINER: Improvement module <!-- omit in toc -->

![ONCOLINER logo](../../docs/images/ONCOLINER_LOGO_COLOR.png)

WIP

## Table of contents<!-- omit in toc -->
- [Dependencies](#dependencies)
- [Usage](#usage)
- [Output](#output)


## Dependencies
ONCOLINER's improvement module makes use of the following Python modules:
* [`pandas`](https://pandas.pydata.org/)
* [`pysam`](https://github.com/pysam-developers/pysam)
* [`variant-extractor`](https://github.com/EUCANCan/variant-extractor)

You may install them using pip:
```
pip3 install pandas pysam variant-extractor
```

However, we recommend using the provided [Dockerfile](../../Dockerfile)/[Singularity recipe](../../singularity.def) for building the whole ONCOLINER suite to avoid dependency issues.


## Usage
```
usage: main.py [-h] -e EVALUATION_RESULTS -c CALLERS_FOLDER -o OUTPUT -rs RECALL_SAMPLES [RECALL_SAMPLES ...] -ps PRECISION_SAMPLES [PRECISION_SAMPLES ...] [-lm LOSS_MARGIN] [-wr WINDOW_RADIUS] [-p PROCESSES]

ONCOLINER Improvement

options:
  -h, --help            show this help message and exit
  -e EVALUATION_RESULTS, --evaluation-results EVALUATION_RESULTS
                        Pipeline evaluation results folder path
  -c CALLERS_FOLDER, --callers-folder CALLERS_FOLDER
                        Callers folder path
  -o OUTPUT, --output OUTPUT
                        Output folder path
  -rs RECALL_SAMPLES [RECALL_SAMPLES ...], --recall-samples RECALL_SAMPLES [RECALL_SAMPLES ...]
                        Recall samples names
  -ps PRECISION_SAMPLES [PRECISION_SAMPLES ...], --precision-samples PRECISION_SAMPLES [PRECISION_SAMPLES ...]
                        Precision samples names
  -lm LOSS_MARGIN, --loss-margin LOSS_MARGIN
                        Loss margin for the improvement
  -wr WINDOW_RADIUS, --window-radius WINDOW_RADIUS
                        Window radius used for the evaluation. It will be inferred automatically by default
  -p PROCESSES, --processes PROCESSES
                        Number of processes to use
```

## Output

The output folder will contain:
* `callers_aggregated`: folder containing the aggregated results for each caller.
* `improvement_list`: folder containing the pipeline's improvement possibilities, grouped in different files by variant type and size.
* `results`: folder with the combinations of each variant caller with the pipeline (one subfolder per combination). Each subfolder contains an `aggregated_metrics.csv` file and a folder named `samples` with the results in a per sample basis. For example:
  * `baseline`: contains the baseline pipeline's results.
  * `baseline$and$caller_1`: contains baseline pipeline intersected with *caller_1*'s results.
  * `baseline$or$caller_2`: contains baseline pipeline joined with *caller_2*'s results.