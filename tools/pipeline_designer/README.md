# PipelineDesigner<!-- omit in toc -->

PipelineDesigner is a standalone tool that allows the user to combine the results of different variant callers to improve the results of a variant calling pipeline. PipelineDesigner outputs the list of the best combinations of variant callers for each variant type and size, including SNVs, indels and SVs. PipelineDesigner also displays the F1-score, precision, recall and the number and names of genes discovered (if provided) of each combination (see [ONCOLINER's assessment module](../../modules/oncoliner_assessment/) for more information about the evaluation process).

The user just needs to provide the VCF files of the variant callers they want to combine as well as the truth files of the samples. The user must also specify which samples should be used to compute recall related metrics and which samples should be used to compute precision related metrics. PipelineDesigner will automatically combine the variant callers and evaluate the results. Check the [Use case example](#use-case-example) section for more information.

PipelineDesigner is part of the [ONCOLINER suite](../../README.md) and is provided as a standalone command line tool. It is available as in the [Docker image](../../Dockerfile) and [Singularity image](../../singularity.def) of ONCOLINER.

## Table of contents<!-- omit in toc -->
- [Usage](#usage)
  - [Interface](#interface)
  - [Output](#output)
- [Use case example](#use-case-example)

## Usage

The main executable code is in the [`src/`](/src/) folder. There is one executable file: [`main.py`](/src/main.py). It is provided as a standalone command line tool. Example of usage:

```bash
python3 src/main.py -t ./input/truth -v ./input/test -o ./output
    -f  ./fake_ref.fa \
    -rs sample_1 \
    -ps sample_2 \
    -p 32 \
    --max-combinations 5
```

Check the example of usage in the [example](./example/) folder for more information.

_Note_: it is recommended to normalize indels and SNVs for each variant caller before executing the PipelineDesigner. For this purpose, we recommend using pre.py from [Illumina's Haplotype Comparison Tools (hap.py)](https://github.com/Illumina/hap.py). We provide an standalone and containerized **[EUCANCan's pre.py wrapper](https://github.com/EUCANCan/prepy-wrapper)** for this purpose.

### Interface
```
usage: main.py [-h] -t TRUTH -v TEST -o OUTPUT -f FASTA_REF -rs RECALL_SAMPLES [RECALL_SAMPLES ...] -ps PRECISION_SAMPLES [PRECISION_SAMPLES ...] [-it INDEL_THRESHOLD] [-wr WINDOW_RADIUS]
               [--sv-size-bins SV_SIZE_BINS [SV_SIZE_BINS ...]] [--contigs CONTIGS [CONTIGS ...]] [-p PROCESSES] [--max-combinations MAX_COMBINATIONS]

PipelineDesigner

options:
  -h, --help            show this help message and exit
  -t TRUTH, --truth TRUTH
                        Path to the VCF truth folder
  -v TEST, --test TEST  Path to the VCF test folder
  -o OUTPUT, --output OUTPUT
                        Path to the output folder
  -f FASTA_REF, --fasta-ref FASTA_REF
                        Path to reference FASTA file
  -rs RECALL_SAMPLES [RECALL_SAMPLES ...], --recall-samples RECALL_SAMPLES [RECALL_SAMPLES ...]
                        Recall samples names
  -ps PRECISION_SAMPLES [PRECISION_SAMPLES ...], --precision-samples PRECISION_SAMPLES [PRECISION_SAMPLES ...]
                        Precision samples names
  -it INDEL_THRESHOLD, --indel-threshold INDEL_THRESHOLD
                        Indel threshold, inclusive (default=100)
  -wr WINDOW_RADIUS, --window-radius WINDOW_RADIUS
                        Window ratio (default=100)
  --sv-size-bins SV_SIZE_BINS [SV_SIZE_BINS ...]
                        SV size bins for the output_prefix metrics (default=[500])
  --contigs CONTIGS [CONTIGS ...]
                        Contigs to process (default=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', 'X', 'Y'])
  -p PROCESSES, --processes PROCESSES
                        Number of processes to use
  --max-combinations MAX_COMBINATIONS
                        Maximum number of combinations to perform (-1) for all
```

### Output

PipelineDesigner generates a series of files in the output folder. Most of them are intermediate files that are used by PipelineDesigner to generate the final output files and recover in case of failure. The most important ones are the `.csv` files in `$OUTPUT_FOLDER/improvement_list`.

Each output `.csv` file is named after the variant type and the variant size (e.g `SNV_1.csv` contains the callers combinations results for SNVs of size 1). Each file contains the following columns:

* `operation`: The combination performed (e.g. `variant_caller_1$or$variant_caller_2`, which means that the combination is the union of the results of `variant_caller_1` and `variant_caller_2`).
* `variant_type`: variant type, as outputted by [VariantExtractor](https://github.com/EUCANCan/variant-extractor).
* `variant_size`: range of variant sizes analyzed for that particular file.
* `window_radius`: window radius used for the assessment.
* `recall`: Recall. TP / (TP + FN). Calculated **only** from the recall samples.
* `precision`: Precision. TP / (TP + FP). Calculated **only** from the precision samples.
* `f1_score`: F1 score. 2 * (precision * recall) / (precision + recall).
* `tp`: Number of true positives. Calculated **only** from the recall samples.
* `fp`: Number of false positives. Calculated **only** from the precision samples.
* `fn`: Number of false negatives. Calculated **only** from the recall samples.
* `protein_affected_genes_count`: Number of genes affected by the variants.
* `protein_affected_driver_genes_count`: Number of cancer driver genes affected by the variants.
* `protein_affected_genes`: List of genes affected by the variants (separated by `;`).
* `protein_affected_driver_genes`: List of cancer driver genes affected by the variants (separated by `;`).

## Use case example

Assume that we have the following input variant callers: `variant_caller_1` and `variant_caller_2`. Both are SV callers. We want to combine them to improve the results of our pipeline. We have the following samples: `sample_1` and `sample_2`. We will use `sample_1` as a recall sample and `sample_2` as a precision sample.

First of all, we need to run the variant callers and obtain the VCF files for each sample. Assume we obtain the following VCF files: `variant_caller_1_sample_N.vcf` and `variant_caller_2_sample_N.vcf` for each sample. **Make sure the names of the samples subfolders are the same across all the variant callers**.

**Optional**. We recommend normalizing the VCF files before running the PipelineDesigner (see [Usage](#usage) for more information). However, in this case it is not necessary because we are only working with SVs.

Now, we can run the PipelineDesigner. We will use the following command:

```bash
python3 src/main.py -t ./input/truth -v ./input/test -o ./output
    -f  ./genome.fa \
    -rs sample_1 \
    -ps sample_2 \
    -p 32 \
    --max-combinations 5
```

The `input` folder has the following structure:
```
input
├── truth
│   ├── sample_1
│   │   └── truth_sample_1.vcf
│   └── sample_2
│       └── truth_sample_2.vcf
└── test
    ├── variant_caller_1
    │   ├── sample_1
    │   │   └── variant_caller_1_sample_1.vcf
    │   └── sample_2
    │       └── variant_caller_1_sample_2.vcf
    └── variant_caller_2
        ├── sample_1
        │   └── variant_caller_2_sample_1.vcf
        └── sample_2
            └── variant_caller_2_sample_2.vcf
```

After running the PipelineDesigner, we will obtain the following output folder structure:
```
output
├── ...
└── improvement_list
    ├── SNV_1.csv
    ├── INDEL_1__100.csv
    ├── ...
    └── SV_ALL.csv
```

We are looking for the `SV_ALL.csv` file. This file contains the results of the combinations of all the SVs. The file may look like this:

| operation                               | variant_type | variant_size | recall | precision | f1_score | ... | num_callers |
| --------------------------------------- | ------------ | ------------ | ------ | --------- | -------- | --- | ----------- |
| `variant_caller_1$or$variant_caller_2`  | SV           | ALL          | 1.00   | 0.50      | 0.67     | ... | 2           |
| `variant_caller_2`                      | SV           | ALL          | 0.67   | 0.50      | 0.57     | ... | 1           |
| `variant_caller_1$and$variant_caller_2` | SV           | ALL          | 0.33   | 1.00      | 0.5      | ... | 2           |
| `variant_caller_1`                      | SV           | ALL          | 0.67   | 1.00      | 0.8      | ... | 1           |


In our case, the best option for maximizing the F1 score is to use `variant_caller_1` alone. However, we can see that the union of `variant_caller_1` and `variant_caller_2` has a higher recall and that `variant_caller_1` alone has a higher precision. Selecting one option or another will depend on the use case.
