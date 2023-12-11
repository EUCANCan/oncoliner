# ONCOLINER: Improvement module <!-- omit in toc -->

![ONCOLINER logo](../../docs/images/ONCOLINER_LOGO_COLOR.png)

The improvement module follows the [assessment step](../oncoliner_assessment/) and provides recommendations based on the performance evaluation of the input pipelines and the selected variant callers. Specifically, the recommendations are the best combinations of variant callers to integrate into the pipeline to maximize performance metrics. It is provided as a standalone command line tool.

The first step is to perform both the union and the intersection of the pipeline calls with the callers. Then, performance metrics are calculated for these merged results, and combinations are sorted based on them. It provides a list of all possible combinations provided in a CSV file. This allows the user to sort them by any of the metrics between recall, precision, F1-score, or even by the number of affected protein-coding, cancer-driver, or actionable genes. To improve visualization of the most relevant recommendations, they are filtered by selecting the one in the top 5% for each performance metric, prioritizing those with the least number of callers. This follows the rationale that a better recommendation minimizes the cost of adding too many tools to a pipeline and the effort of going through redundant combinations.

## Table of contents<!-- omit in toc -->
- [Installation](#installation)
- [Usage](#usage)
- [Output](#output)


## Installation

We recommend using the ONCOLINER container or the provided [Dockerfile](../../Dockerfile)/[Singularity recipe](../../singularity.def) for building the whole ONCOLINER suite to avoid dependency issues.


## Usage

The main executable code is in the [`src/`](./src/) folder. The executable file is [`improvement_main.py`](./src/improvement_main.py). There is an example of usage in the [`example/`](./example/) folder.

### Interface<!-- omit in toc -->
```
usage: improvement_main.py [-h] -e EVALUATION_RESULTS -c CALLERS_FOLDER -o
                           OUTPUT -rs RECALL_SAMPLES [RECALL_SAMPLES ...] -ps
                           PRECISION_SAMPLES [PRECISION_SAMPLES ...]
                           [-lm LOSS_MARGIN] [-gm GAIN_MARGIN]
                           [-mr MAX_RECOMMENDATIONS] [-wr WINDOW_RADIUS]
                           [-p PROCESSES]

ONCOLINER Improvement

optional arguments:
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
                        Maximum performance loss in any metric to consider a
                        recommendation (default: 0.05). A value of 0.05 means
                        that a recommendation will be provided if the
                        performance loss (in any metric) is less than 5% over
                        the baseline, provided that --gain-margin is also
                        satisfied. Increasing this value will increase the
                        number of recommendations and execution time
  -gm GAIN_MARGIN, --gain-margin GAIN_MARGIN
                        Minimum performance gain in a metric to consider a
                        recommendation (default: 0.05). A value of 0.05 means
                        that a recommendation will be provided if the
                        performance gain (in any metric) is greater than 5%
                        over the baseline, provided that --loss-margin is also
                        satisfied. Increasing this value will reduce the
                        number of recommendations and execution time
  -mr MAX_RECOMMENDATIONS, --max-recommendations MAX_RECOMMENDATIONS
                        Maximun number of recommendations to provide for each
                        performance metric per variant type and size and
                        number of variant callers added (default: 1). Set to
                        -1 to provide all recommendations
  -wr WINDOW_RADIUS, --window-radius WINDOW_RADIUS
                        Window radius used for the evaluation. It will be
                        inferred automatically by default
  -p PROCESSES, --processes PROCESSES
                        Number of processes to use (default: 1)
```

## Output

The output folder will contain:
* `improvement_list`: folder containing the pipeline's improvement possibilities, grouped in different files by variant type and size.
* `results`: folder with the combinations of each variant caller with the pipeline (one subfolder per combination). Each subfolder contains an `aggregated_metrics.csv` file and a folder named `samples` with the results in a per sample basis. For example:
  * `baseline`: contains the baseline pipeline's results.
  * `baseline_and_caller_1`: contains baseline pipeline intersected with *caller_1*'s results.
  * `baseline_or_caller_2`: contains baseline pipeline joined with *caller_2*'s results.
