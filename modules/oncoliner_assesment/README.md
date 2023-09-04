# Oncoliner: Assesment module<!-- omit in toc -->

![Oncoliner logo](../../docs/images/ONCOLINER_LOGO_COLOR.png)

Evaluator of variants (SNVs, indels and SVs) from test VCFs against truth VCFs. It is provided as a standalone command line tool to allow for the comparison of a series of (VCF/BCF/VCF.GZ) files generated by any variant callers against a series of (VCF/BCF/VCF.GZ) truth files. If provided in the truth files the module will also provide information about the genes affected by the variants. Check the [Functional analysis](#functional-analysis) section for more information.

It uses [VariantExtractor](https://github.com/EUCANCan/variant-extractor) under-the-hood for extracting SNVs, indels and structural variants (SVs) from VCF files in a deterministic and standard way. Different variant callers may provice slightly different formatted VCF files, that is why VariantExtractor adds a preprocessing layer to homogenize the variants extracted from the file. For more information about the preprocessing process check [VariantExtractor's repository](https://github.com/EUCANCan/variant-extractor#table-of-contents).

It is written in Python 3 (**requires Python version 3.6 or higher**).

## Table of contents<!-- omit in toc -->
- [Dependencies](#dependencies)
- [Functional analysis](#functional-analysis)
- [Usage](#usage)
  - [`assesment_main.py`](#assesment_mainpy)
  - [`assesment_bulk.py`](#assesment_bulkpy)
    - [Configuration file](#configuration-file)

## Dependencies
Oncoliner's assesment module makes use of the following Python modules:
* [`pandas`](https://pandas.pydata.org/)
* [`pysam`](https://github.com/pysam-developers/pysam)

You may install them using pip:
```
pip3 install pandas pysam
```

## Functional analysis

The module will try to obtain the genes affected by the variants from the `INFO` field in the truth files. **WARNING: Oncoliner does not compute genes linked to false positives.** Oncoliner's assesment module is compatible with the following functional analysis tools annotations:
* Oncoliner.
* [**VEP**](https://www.ensembl.org/info/docs/tools/vep/index.html): Variant Effect Predictor from Ensembl.


## Usage

**WARNING**: It is recommended to normalize indels and SNVs before executing the assesment. For this purpose, we recommend using pre.py from [Illumina's Haplotype Comparison Tools (hap.py)](https://github.com/Illumina/hap.py). We provide an standalone and containerized **[EUCANCan's pre.py wrapper](https://github.com/EUCANCan/prepy-wrapper)** for this purpose.

The main executable code is in the [`src/`](/src/) folder. There are two executable files: [`assesment_main.py`](#assesment_mainpy) and [`assesment_bulk.py`](/src/assesment_bulk.py). The first one is the main executable file and the second one is a wrapper for the first one that allows to execute the assesment in a bulk way.

There is an example of usage in the [`examples/`](/examples/) folder for each executable file: [`examples/test_main.sh`](/examples/test_main.sh) and [`examples/test_bulk.sh`](/examples/test_bulk.sh).


### `assesment_main.py`

Main executable file. It allows to compare a series of (VCF/BCF/VCF.GZ) files generated by any variant callers against a series of (VCF/BCF/VCF.GZ) truth files for **only one sample**. It is provided as a standalone command line tool. Example of usage:

```
python3 -O src/assesment_main.py -t truth.vcf -v test.vcf -o output_
```

Check the example of usage in [`examples/test_main.sh`](/examples/test_main.sh) for more information.

#### Interface<!-- omit in toc -->
```
usage: assesment_main.py [-h] -t TRUTHS [TRUTHS ...] -v TESTS [TESTS ...] -o OUTPUT_PREFIX -f FASTA_REF [-it INDEL_THRESHOLD] [-wr WINDOW_RADIUS] [--sv-size-bins SV_SIZE_BINS [SV_SIZE_BINS ...]]
                         [--contigs CONTIGS [CONTIGS ...]] [--keep-intermediates] [--no-gzip]

Oncoliner Assesment

options:
  -h, --help            show this help message and exit
  -t TRUTHS [TRUTHS ...], --truths TRUTHS [TRUTHS ...]
                        Path to the VCF truth files
  -v TESTS [TESTS ...], --tests TESTS [TESTS ...]
                        Path to the VCF test files
  -o OUTPUT_PREFIX, --output_prefix OUTPUT_PREFIX
                        Prefix path for the output_prefix VCF files
  -f FASTA_REF, --fasta-ref FASTA_REF
                        Path to reference FASTA file
  -it INDEL_THRESHOLD, --indel-threshold INDEL_THRESHOLD
                        Indel threshold, inclusive (default=100)
  -wr WINDOW_RADIUS, --window-radius WINDOW_RADIUS
                        Window ratio (default=100)
  --sv-size-bins SV_SIZE_BINS [SV_SIZE_BINS ...]
                        SV size bins for the output_prefix metrics (default=[500])
  --contigs CONTIGS [CONTIGS ...]
                        Contigs to process (default=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', 'X', 'Y'])
  --keep-intermediates  Keep intermediate CSV/VCF files from input VCF files
  --no-gzip             Do not gzip output_prefix VCF files
```

#### Output<!-- omit in toc -->

`assesment_main.py` outputs a series of files:
 * `{OUTPUT_PREFIX}tp.[snv|indel|sv].vcf.gz`: VCF files with the true positives (TP) variants. One file per variant type (SNV, indel and SV).
 * `{OUTPUT_PREFIX}fp.[snv|indel|sv].vcf.gz`: VCF files with the false positives (FP) variants. One file per variant type (SNV, indel and SV).
 * `{OUTPUT_PREFIX}fn.[snv|indel|sv].vcf.gz`: VCF files with the false negatives (FN) variants. One file per variant type (SNV, indel and SV).
 * `{OUTPUT_PREFIX}metrics.csv`: CSV file containing the metrics for the comparison of the test and truth VCF files. It contains the following columns:
   * `variant_type`: variant type (SNV, indel or SV), as outputted by [VariantExtractor](https://github.com/EUCANCan/variant-extractor).
   * `variant_size`: range of variant sizes for that particular row.
   * `window_radius`: window radius used for the assessment.
   * `recall`: Recall. TP / (TP + FN).
   * `precision`: Precision. TP / (TP + FP).
   * `f1_score`: F1 score. 2 * (precision * recall) / (precision + recall).
   * `tp`: Number of true positives.
   * `fp`: Number of false positives.
   * `fn`: Number of false negatives.
   * `protein_affected_genes_count`: Number of genes affected by the variants.
   * `protein_affected_driver_genes_count`: Number of cancer driver genes affected by the variants.
   * `protein_affected_genes`: List of genes affected by the variants (separated by `;`).
   * `protein_affected_driver_genes`: List of cancer driver genes affected by the variants (separated by `;`).

### `assesment_bulk.py`

Wrapper for `assesment_main.py`. It allows to compare a series of (VCF/BCF/VCF.GZ) files generated by any variant callers against a series of (VCF/BCF/VCF.GZ) truth files for **multiple samples**. It takes advantage of multiple processors. It is provided as a standalone command line tool. Example of usage:

```
python3 -O src/assesment_main.py -c config.tsv -o output_
```

Check the example of usage in [`examples/test_bulk.sh`](/examples/test_bulk.sh) for more information.

#### Configuration file

The configuration file is a TSV file with the following columns:
* `sample_name`: sample name.
* `sample_type`: sample types (recall or precision), separated by `,`.
* `reference_fasta_path`: path to the reference FASTA file.
* `truth_vcf_paths`: path(s) to the truth VCF files, separated by `,`. They can also be wildcard paths (e.g. `truths/*.vcf.gz`).
* `test_vcf_paths`: path(s) to the test VCF files, separated by `,`. They can also be wildcard paths (e.g. `tests/*.vcf.gz`).

#### Interface<!-- omit in toc -->
```
usage: assesment_bulk.py [-h] -c CONFIG_FILE -o OUTPUT_FOLDER [-it INDEL_THRESHOLD] [-wr WINDOW_RADIUS] [--sv-size-bins SV_SIZE_BINS [SV_SIZE_BINS ...]] [--contigs CONTIGS [CONTIGS ...]] [--keep-intermediates]
                         [--no-gzip] [-p MAX_PROCESSES]

Oncoliner Assesment Bulk

options:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        Path to the config TSV file
  -o OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                        Path to the output folder
  -it INDEL_THRESHOLD, --indel-threshold INDEL_THRESHOLD
                        Indel threshold, inclusive (default=100)
  -wr WINDOW_RADIUS, --window-radius WINDOW_RADIUS
                        Window radius (default=100)
  --sv-size-bins SV_SIZE_BINS [SV_SIZE_BINS ...]
                        SV size bins for the output_prefix metrics (default=[500])
  --contigs CONTIGS [CONTIGS ...]
                        Contigs to process (default=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', 'X', 'Y'])
  --keep-intermediates  Keep intermediate CSV/VCF files from input VCF files
  --no-gzip             Do not gzip output_prefix VCF files
  -p MAX_PROCESSES, --max-processes MAX_PROCESSES
                        Maximum number of processes to use (defaults to 1)
```

#### Output<!-- omit in toc -->

`assesment_bulk.py` outputs the same files as `assesment_main.py` for each sample. The output files for each sample are stored in the `OUTPUT_FOLDER/samples` folder in a subfolder named after the sample name.

`assesment_bulk.py` also outputs a `aggregated_metrics.csv` file, which aggregates the metrics for all the samples. It contains the same columns as `assesment_main.py`'s `metrics.csv` file. Recall related metrics are calculated using the recall samples and precision related metrics are calculated using the precision samples (as described in the configuration file).