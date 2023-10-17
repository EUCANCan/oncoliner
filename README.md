# ONCOLINER<!-- omit in toc -->

![ONCOLINER logo](/docs/images/ONCOLINER_LOGO_COLOR.png)

WIP

## Table of contents<!-- omit in toc -->
- [Installation](#installation)
  - [Docker / Singularity](#docker--singularity)
  - [Local installation](#local-installation)
- [Usage](#usage)
  - [Interface](#interface)
  - [Normalization](#normalization)
- [Tools](#tools)
  - [Pipeline designer](#pipeline-designer)
  - [`vcf-ops`](#vcf-ops)
- [Modularity](#modularity)

## Installation

It is highly recommended to use ONCOLINER with Docker or Singularity (we recommend using [`singularity-ce`](https://github.com/sylabs/singularity) with a version higher than 3.9.0). However, you may also install it locally.

### Docker / Singularity

You may use the [Dockerfile](/Dockerfile) to build a Docker image or the [singularity.def](/singularity.def) file to build a Singularity image.

```bash
# Build Docker image
docker build -t oncoliner .

# Build Singularity image
singularity build oncoliner.sif singularity.def
```

### Local installation

You may also install ONCOLINER locally using the same instructions as provided in the [Dockerfile](/Dockerfile).

## Usage

Assuming you have a singularity image called `oncoliner.sif`, you can run ONCOLINER as follows:

```bash
singularity exec oncoliner.sif oncoliner/main.py -c config.tsv -pf pipelines_1_folder pipelines_2_folder -o output_folder --max-processes 48
```

### Interface
```
usage: main.py [-h] -c CONFIG -pf PIPELINES_FOLDERS [PIPELINES_FOLDERS ...] -o OUTPUT [-cf CALLERS_FOLDER] [--max-processes MAX_PROCESSES]

ONCOLINER

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to config file
  -pf PIPELINES_FOLDERS [PIPELINES_FOLDERS ...], --pipelines-folders PIPELINES_FOLDERS [PIPELINES_FOLDERS ...]
                        Paths to pipelines folders
  -o OUTPUT, --output OUTPUT
                        Path to output folder
  -cf CALLERS_FOLDER, --callers-folder CALLERS_FOLDER
                        Path to callers folder
  --max-processes MAX_PROCESSES
                        Maximum number of processes to use (defaults to 1)
```

#### Pipelines folders<!-- omit in toc -->

The pipelines folders are folders containing the results of executing each pipeline. Each pipeline folder provided in the `PIPELINES_FOLDERS` argument is treated as a different pipeline. Each pipeline folder must contain one subfolder for each sample declared in the [configuration file](#configuration-file). The name of the subfolder must match the `sample_name` declared in the [configuration file](#configuration-file). Each sample subfolder must contain at least one VCF/VCF.GZ/BCF file.

#### Configuration file<!-- omit in toc -->

The configuration file is a TSV file with the following columns:
* `sample_name`: sample name.
* `sample_types`: sample types (recall or precision), separated by `,`.
* `reference_fasta_path`: path to the reference FASTA file.
* `truth_vcf_paths`: path(s) to the truth VCF files, separated by `,`. They can also be wildcard paths (e.g. `truths/*.vcf.gz`).

You can check an example of configuration file in [`example/example_config.tsv`](/example/example_config.tsv).

### Normalization

It is recommended to normalize indels and SNVs before executing ONCOLINER. For this purpose, we recommend using pre.py from [Illumina's Haplotype Comparison Tools (hap.py)](https://github.com/Illumina/hap.py). We provide an standalone and containerized **[EUCANCan's pre.py wrapper](https://github.com/EUCANCan/prepy-wrapper)** for this purpose, specially the bulk version of the wrapper. You can check an example of usage in [`example/example_prepy.sh`](/example/example_prepy.sh).

## Tools

Along with ONCOLINER, in this repository you can find some tools that may be useful.

### Pipeline designer

WIP

### `vcf-ops`

WIP

## Modularity

ONCOLINER is divided into three functional modules (assesment, improvement and harmonization) and a UI module. For more information about each module, check the corresponding README file in the [`modules`](/modules) folder:

* [Assesment README](/modules/oncoliner_assesment/README.md)
* [Improvement README](/modules/oncoliner_improvement/README.md)
* [Harmonization README](/modules/oncoliner_harmonization/README.md)
* [UI README](/modules/oncoliner_ui/README.md)

Each module can be run independently. However, the results of the assesment module are required to run the improvement module and the results of the improvement module are required to run the harmonization module. The UI module generates a report for the results of each module.
