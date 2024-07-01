# ONCOLINER<!-- omit in toc -->

![ONCOLINER logo](/docs/images/ONCOLINER_LOGO_COLOR.png)

ONCOLINER is an integrated platform with benchmarking data and tools for the detailed assessment, improvement and quality-based harmonization of analysis pipelines across centers. It can not only improve the overall efficiency of somatic variant identification globally, but it will also enable interoperability and consistency within emerging multi-center and multi-hospital data environments, allowing the sharing and integration of cancer datasets and results.

## Table of contents<!-- omit in toc -->
- [Quick start guide](#quick-start-guide)
- [Installation](#installation)
  - [Singularity](#singularity)
  - [Docker](#docker)
- [Usage](#usage)
  - [Interface](#interface)
  - [Normalization](#normalization)
- [Additional software](#additional-software)
  - [PipelineDesigner](#pipelinedesigner)
  - [VCF Intersect](#vcf-intersect)
  - [VCF Union](#vcf-union)
- [Modules](#modules)
- [How to use ONCOLINER in your specific use case](#how-to-use-oncoliner-in-your-specific-use-case)
  - [Specific benchmarking datasets](#specific-benchmarking-datasets)
  - [Specific variant callers](#specific-variant-callers)

## Quick start guide

Follow these steps to run ONCOLINER with the default configuration and default datasets (tumorized and mosaic genomes). First, create a directory to store the ONCOLINER workspace:

```
mkdir oncoliner_workspace
cd oncoliner_workspace
```

Then, download the Tumorized genomes and their truth VCF files ([ENA project](https://www.ebi.ac.uk/ena/browser/view/PRJEB68324)):

```
wget -P benchmarking_datasets/tumorized_genomes/tumorized_precision_NA12878 -nc http://ftp.sra.ebi.ac.uk/vol1/run/ERR122/ERR12264778/tumorized_NA12878_GRCh37_GRCh37_60X_precision_T.cram
wget -P benchmarking_datasets/tumorized_genomes/tumorized_precision_NA12878 -nc http://ftp.sra.ebi.ac.uk/vol1/run/ERR122/ERR12264778/tumorized_NA12878_GRCh37_GRCh37_60X_precision_T.cram.crai
wget -P benchmarking_datasets/tumorized_genomes/tumorized_precision_NA12878 -nc http://ftp.sra.ebi.ac.uk/vol1/run/ERR122/ERR12264432/tumorized_NA12878_GRCh37_GRCh37_40X_N.cram
wget -P benchmarking_datasets/tumorized_genomes/tumorized_precision_NA12878 -nc http://ftp.sra.ebi.ac.uk/vol1/run/ERR122/ERR12264432/tumorized_NA12878_GRCh37_GRCh37_40X_N.cram.crai
wget -P benchmarking_datasets/tumorized_genomes/tumorized_precision_NA12878 -nc http://ftp.sra.ebi.ac.uk/vol1/analysis/ERZ218/ERZ21869344/tumorized_NA12878_GRCh37_GRCh37_60X_precision_T.cram.annotated.vcf

wget -P benchmarking_datasets/tumorized_genomes/tumorized_precision_HG002 -nc http://ftp.sra.ebi.ac.uk/vol1/run/ERR122/ERR12261542/tumorized_HG002_GRCh37_GRCh37_60X_precision_T.cram
wget -P benchmarking_datasets/tumorized_genomes/tumorized_precision_HG002 -nc http://ftp.sra.ebi.ac.uk/vol1/run/ERR122/ERR12261542/tumorized_HG002_GRCh37_GRCh37_60X_precision_T.cram.crai
wget -P benchmarking_datasets/tumorized_genomes/tumorized_precision_HG002 -nc http://ftp.sra.ebi.ac.uk/vol1/run/ERR122/ERR12257182/tumorized_HG002_GRCh37_GRCh37_40X_N.cram.crai
wget -P benchmarking_datasets/tumorized_genomes/tumorized_precision_HG002 -nc http://ftp.sra.ebi.ac.uk/vol1/run/ERR122/ERR12257182/tumorized_HG002_GRCh37_GRCh37_40X_N.cram
wget -P benchmarking_datasets/tumorized_genomes/tumorized_precision_HG002 -nc http://ftp.sra.ebi.ac.uk/vol1/analysis/ERZ218/ERZ21869345/tumorized_HG002_GRCh37_GRCh37_60X_precision_T.cram.annotated.vcf
```

Then, download the Mosaic genomes and their truth VCF files. Follow the instructions for requesting access and downloading the PCAWG Mosaic genomes and their truth files from [here](https://dcc.icgc.org/releases/PCAWG/pilot50-mosaic) and the HMF mosaic genomes and their truth files from [WIP]().
```
mkdir -p benchmarking_datasets/mosaic_genomes/mosaic_genome_PCAWG_0
mkdir -p benchmarking_datasets/mosaic_genomes/mosaic_genome_PCAWG_1
mkdir -p benchmarking_datasets/mosaic_genomes/mosaic_genome_PCAWG_2
# Download data

mkdir -p benchmarking_datasets/mosaic_genomes/mosaic_genome_HMF
# Download data
```

Download and index the reference FASTA file. All CRAM files are aligned to GRCh37 (https://ftp.broadinstitute.org/pub/seq/references/Homo_sapiens_assembly19.fasta without scaffolds and supercontigs, only 1-22-X-Y-MT) using BWA-0.7.17 MEM.

Download the example configuration file and edit it to match the paths of the tumorized and mosaic genomes, truth VCF files and reference FASTA file:

```
wget https://raw.githubusercontent.com/EUCANCan/oncoliner/main/default_config.tsv
# Edit the example configuration file
```

Create the pipelines folders and subfolder (as many as pipelines you want to evaluate), the following example is for one pipeline:
```
mkdir pipeline_1
mkdir pipeline_1/mosaic_genome_PCAWG_0
mkdir pipeline_1/mosaic_genome_PCAWG_1
mkdir pipeline_1/mosaic_genome_PCAWG_2
mkdir pipeline_1/mosaic_genome_HMF
mkdir pipeline_1/tumorized_precision_NA12878
mkdir pipeline_1/tumorized_recall_NA12878
```

Execute the pipelines (as many as pipelines you want to evaluate) and store the filtered VCF files in the corresponding pipelines folders previously created. The pipeline folder structure should end up looking like this:

```
pipeline_1
├── mosaic_genome_PCAWG_0
│   ├── output_file_1.vcf
│   ├── output_file_2.vcf
│   ├── ...
│   └── output_file_n.vcf
├── mosaic_genome_PCAWG_1
│   └── ...
├── mosaic_genome_PCAWG_2
│   └── ...
├── mosaic_genome_HMF
│   └── ...
├── tumorized_precision_NA12878
│   └── ...
└── tumorized_recall_NA12878
    └── ...
```

Download the ONCOLINER singularity image:
```
singularity pull oncoliner.sif oras://ghcr.io/eucancan/oncoliner:latest
```

Extract the variant callers pre-computed combinations evaluations:
```
wget -nc http://cg.bsc.es/cg/data/oncoliner_variant_callers_combinations.tar.gz
tar xzvf oncoliner_variant_callers_combinations.tar.gz
```

Execute ONCOLINER:
```
singularity exec oncoliner.sif python3 -O /oncoliner/oncoliner_launcher.py -c config.tsv -pf pipeline_1 -cf variant_callers_combinations/evaluations -o output_folder --max-processes 48
```

Check your results in the `output_folder/oncoliner_report.html` file.

## Installation

It is highly recommended to use ONCOLINER with Docker or Singularity. However, you may also install it locally following the instructions in the [Dockerfile](/Dockerfile).

### Singularity
We recommend using [`singularity-ce`](https://github.com/sylabs/singularity) with a version higher than 3.9.0. You can download the Singularity container using the following command (does not require root privileges):

```
singularity pull oncoliner.sif oras://ghcr.io/eucancan/oncoliner:latest
```

If you want to build the container yourself, you can use the [`singularity.def`](singularity.def) file (requires root privileges):
```
sudo singularity build --force oncoliner.sif singularity.def
```

### Docker
You can download the Docker image using the following command:
```
docker pull ghcr.io/eucancan/oncoliner:latest
```

You can build the Docker container with the following command (requires root privileges):

```
docker build -t oncoliner .
```

## Usage

Assuming you have a singularity image called `oncoliner.sif`, you can run ONCOLINER as follows:

```bash
singularity exec oncoliner.sif python3 -O /oncoliner/oncoliner_launcher.py -c config.tsv -pf pipeline_1_folder pipelines_2_folder -o output_folder --max-processes 48
```

### Interface
```
usage: oncoliner_launcher.py [-h] -c CONFIG -pf PIPELINES_FOLDERS
                             [PIPELINES_FOLDERS ...] -o OUTPUT
                             [-cf CALLERS_FOLDER]
                             [--max-processes MAX_PROCESSES]

ONCOLINER

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to config file
  -pf PIPELINES_FOLDERS [PIPELINES_FOLDERS ...], --pipelines-folders PIPELINES_FOLDERS [PIPELINES_FOLDERS ...]
                        Paths to pipelines folders
  -o OUTPUT, --output OUTPUT
                        Path to output folder
  -cf CALLERS_FOLDER, --callers-folder CALLERS_FOLDER
                        Path to callers folder (required for improvement and
                        harmonization)
  --max-processes MAX_PROCESSES
                        Maximum number of processes to use (defaults to 1)
```

#### Configuration file<!-- omit in toc -->

The configuration file is a TSV file with the following columns:
* `sample_name`: sample name.
* `sample_types`: sample types (recall or precision), separated by `,`.
* `reference_fasta_path`: path to the reference FASTA file.
* `truth_vcf_paths`: path(s) to the truth VCF files, separated by `,`. They can also be wildcard paths (e.g. `truths/*.vcf.gz`).

You can check an example of configuration file in [`example/example_config.tsv`](/example/example_config.tsv).

#### Pipelines folders<!-- omit in toc -->

The pipelines folders are folders containing the results of executing each pipeline. Each pipeline folder provided in the `PIPELINES_FOLDERS` argument is treated as a different pipeline. Each pipeline folder must contain one subfolder for each sample declared in the [configuration file](#configuration-file). The name of the subfolder must match the `sample_name` declared in the [configuration file](#configuration-file). Each sample subfolder must contain at least one VCF/VCF.GZ/BCF file. The pipeline folder structure should look like this:

```
pipeline_1
├── sample_1
│   ├── output_file_1.vcf
│   ├── output_file_2.vcf
│   ├── ...
│   └── output_file_n.vcf
├── sample_2
│   └── ...
└── sample_3
    └── ...
```

#### Callers folder<!-- omit in toc -->

The callers folder is a folder containing the pre-computed evaluations for each of the variant callers (and optionally their combinations). Ideally, this folder has been created using ONCOLINER assessment. This folder is only required to run ONCOLINER improvement and harmonization. The callers folder structure should look like this (automatically generated by ONCOLINER assessment):

```
callers_folder
├── variant_caller_1
│   └── samples
│       ├── sample_1
│       │   ├── variant_caller_1_fn.vcf
│       │   ├── variant_caller_1_fp.vcf
│       │   ├── variant_caller_1_tp.vcf
│       │   ├── ...
│       │   └── variant_caller_1_metrics.csv
│       ├── sample_2
│       │   └── ...
│       └── sample_3
│          └── ...
├── variant_caller_2
│   └── ...
└── variant_caller_3
    └── ...
```

You can check an example of callers folder in [`example/input/callers_folder`](/example/input/callers_folder).

### Normalization

It is recommended to normalize indels and SNVs before executing ONCOLINER. For this purpose, we recommend using pre.py from [Illumina's Haplotype Comparison Tools (hap.py)](https://github.com/Illumina/hap.py). We provide an standalone and containerized **[EUCANCan's pre.py wrapper](https://github.com/EUCANCan/prepy-wrapper)** for this purpose, specially the bulk version of the wrapper.

## Additional software

Along with ONCOLINER, in this repository we also provide additional stand-alone software solutions for multiple needs associated with the improvement, standardization and harmonization of genome analysis across centers.

### PipelineDesigner

A standalone tool that helps users to find the best strategy to combine and merge specific variant callers to maximize recall and precision over all variant types. More information about this tool can be found in the [PipelineDesigner README](/tools/pipeline_designer/README.md).

### VCF Intersect

A standalone tool that allows users to intersect two different groups of VCF files. More information about this tool can be found in the [VCF Intersect README](/tools/vcf_intersect/README.md).

### VCF Union

A standalone tool that allows users to merge two different groups of VCF files. More information about this tool can be found in the [VCF Union README](/tools/vcf_union/README.md).

## Modules

ONCOLINER is divided into three functional modules (assessment, improvement and harmonization) and a UI module. For more information about each module, check the corresponding README file in the [`modules`](/modules) folder:

* [Assessment README](/modules/oncoliner_assessment/README.md)
* [Improvement README](/modules/oncoliner_improvement/README.md)
* [Harmonization README](/modules/oncoliner_harmonization/README.md)
* [UI README](/modules/oncoliner_ui/README.md)

Each module can be run independently. However, the results of the assessment module are required to run the improvement module and the results of the improvement module are required to run the harmonization module. The UI module generates a report for the results of each module.

## How to use ONCOLINER in your specific use case

ONCOLINER is a flexible tool that can be used in multiple use cases. In this section we will explain how to use ONCOLINER in some of the most common use cases.

### Specific benchmarking datasets

ONCOLINER can be used to evaluate pipelines using user-defined benchmarking datasets. For this purpose, you must adapt the [default_config.tsv](/default_config.tsv) file to your specific use case (see [Configuration file](#configuration-file)). Make sure that your [Pipeline folders](#pipelines-folders) contain the results of executing each pipeline on each of your samples. Note that ONCOLINER will not be able to provide you with recommendations for improvement and harmonization if you do not provide the [Callers folder](#callers-folder) with your samples (see [Specific variant callers](#specific-variant-callers)).

### Specific variant callers

ONCOLINER can be used to improve and harmonize pipelines using specific variant callers (apart from the ones provided in the [quick start guide](#quick-start-guide) for the default datasets). For this purpose, you must adapt the [Callers folder](#callers-folder) to your specific use case. To generate this folder, it is highly recommended to use ONCOLINER assessment for each variant caller. The [Callers folder](#callers-folder) must contain the results of executing each variant caller on each of your samples.

If you also want to generate combinations of your variant callers for ONCOLINER improvement and harmonization, it is highly recommended you use [PipelineDesigner](#pipelinedesigner). In the `evaluations` folder generated by the tool's output, you can find the assessment results of the combinations of your variant callers. You can use that folder as the [Callers folder](#callers-folder) for ONCOLINER improvement and harmonization directly.
