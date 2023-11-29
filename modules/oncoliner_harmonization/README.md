# ONCOLINER: Harmonization module<!-- omit in toc -->

![ONCOLINER logo](../../docs/images/ONCOLINER_LOGO_COLOR.png)

The harmonizer module follows the [improvement step](../oncoliner_improvement/) generating recommendations to bring the performance of all input pipelines closer while maintaining the best possible performance. To achieve this, the degree of heterogeneity between pipelines is evaluated based on two values: $H_{score}$ and Gene Discordance Ratio (GDR). It is provided as a standalone command line tool.

To quantitatively scale the heterogeneity in performance metrics we created the heterogeneity score ($H_{score}$). By plotting precision-recall ranges in a Euclidean space, pipelines are represented by their respective performance coordinates. Considering $p_{i}$ (recall, precision) as a pipeline from the set of $n$ pipelines, a centroid $c$ is the point that minimizes the distance $d_{i}$ from all $p_{i}$. Then, the $H_{score}$ is computed as the mean of all $d_{i}$. In other words, the $H_{score}$ is the average Euclidean distance from the position of each pipeline to the centroid or the theoretical maximum homogeneity point.

$H_{score} = \frac{1}{n}\sum_{i=1 }^n{d_i},{ where }\; d_i = \sqrt{(p_i^{recall}-c^{recall})^2+(p_i^{precision}-c^{precision})^2}$

To measure functional impact heterogeneity in variant discovery we created the Gene Discordance Ratio (GDR). The GDR is calculated as the complement of the proportion between the variant-affected genes found by every pipeline (intersection) over the total number of variant-affected genes even if only detected by one of the pipelines (union). Hence, a GDR value closer to 1 would imply a high level of heterogeneity in functional impact between the pipelines. This metric follows \Cref{eq:gdr} where $G_{i}$ represents the number of genes affected by the discovered variants from the i-th pipeline.

$GDR = 1 - \frac{|G_1 \cap G_2 \cap G_3\dots \cap G_n|}{|G_1 \cup G_2 \cup G_3\dots \cup G_n|}$

## Table of contents<!-- omit in toc -->
- [Installation](#installation)
- [Usage](#usage)
- [Output](#output)


## Installation

We recommend using the ONCOLINER container or the provided [Dockerfile](../../Dockerfile)/[Singularity recipe](../../singularity.def) for building the whole ONCOLINER suite to avoid dependency issues.

## Usage

The main executable code is in the [`src/`](./src/) folder. The executable file is [`harmonization_main.py`](./src/harmonization_main.py).

### Interface<!-- omit in toc -->

```
usage: harmonization_main.py [-h] -i INPUT_PIPELINES_IMPROVEMENTS
                             [INPUT_PIPELINES_IMPROVEMENTS ...] -o OUTPUT
                             [-lm LOSS_MARGIN] [-mr MAX_RECOMMENDATIONS]
                             [-t THREADS]

ONCOLINER Harmonization

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_PIPELINES_IMPROVEMENTS [INPUT_PIPELINES_IMPROVEMENTS ...], --input-pipelines-improvements INPUT_PIPELINES_IMPROVEMENTS [INPUT_PIPELINES_IMPROVEMENTS ...]
                        Paths to each pipeline improvement folder
  -o OUTPUT, --output OUTPUT
                        Output folder
  -lm LOSS_MARGIN, --loss-margin LOSS_MARGIN
                        Maximum performance loss from the maximum in a metric
                        to consider a recommendation (default: 0.05). A value
                        of 0.05 means that a recommendation will be provided
                        if the performance loss (in any metric) is less than
                        5% over the maximum of all recommendations. Decreasing
                        this value will decrease the number of recommendations
                        after --max-recommendations is applied
  -mr MAX_RECOMMENDATIONS, --max-recommendations MAX_RECOMMENDATIONS
                        Maximun number of recommendations to provide for each
                        performance metric per variant type and size and
                        number of variant callers added (default: 1). Set to
                        -1 to provide all recommendations
  -t THREADS, --threads THREADS
                        Number of CPU threads
```

## Output

The output folder will contain all the pipeline's harmonization possibilities, grouped in different files by variant type and size.
