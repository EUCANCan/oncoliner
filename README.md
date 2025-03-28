# ONCOLINER<!-- omit in toc -->

![ONCOLINER logo](/docs/images/ONCOLINER_LOGO_COLOR.png)

[![DOI](https://zenodo.org/badge/656654605.svg)](https://zenodo.org/doi/10.5281/zenodo.12755026)

R. Martín et al., “ONCOLINER: A new solution for monitoring, improving, and harmonizing somatic variant calling across genomic oncology centers,” _Cell Genomics_, vol. 4, no. 9. Elsevier BV, p. 100639, Sep. 2024. [doi: 10.1016/j.xgen.2024.100639](https://doi.org/10.1016/j.xgen.2024.100639)

ONCOLINER is an integrated platform with benchmarking data and tools for the detailed assessment, improvement and quality-based harmonization of analysis pipelines across centers. It can not only improve the overall efficiency of somatic variant identification globally, but it will also enable interoperability and consistency within emerging multi-center and multi-hospital data environments, allowing the sharing and integration of cancer datasets and results.

ONCOLINER is divided into three functional modules (assessment, improvement and harmonization) and a UI module. Each module can be run **independently**. However, the results of the assessment module are required to run the improvement module and the results of the improvement module are required to run the harmonization module. The UI module generates a report for the results of each module. For more information about each module, check the corresponding README file in the [`modules`](/modules) folder:

* [Assessment README](/modules/oncoliner_assessment/README.md)
* [Improvement README](/modules/oncoliner_improvement/README.md)
* [Harmonization README](/modules/oncoliner_harmonization/README.md)
* [UI README](/modules/oncoliner_ui/README.md)

## Table of contents<!-- omit in toc -->
- [Quick start guide](#quick-start-guide)
- [Installation](#installation)
  - [Singularity](#singularity)
  - [Docker](#docker)
- [Usage](#usage)
  - [Assessment (only)](#assessment-only)
  - [Assessment and improvement (only)](#assessment-and-improvement-only)
  - [Assessment, improvement and harmonization](#assessment-improvement-and-harmonization)
  - [Normalization](#normalization)
- [Additional software](#additional-software)
  - [PipelineDesigner](#pipelinedesigner)
  - [VCF Intersect](#vcf-intersect)
  - [VCF Union](#vcf-union)
- [How to use ONCOLINER in your specific use case](#how-to-use-oncoliner-in-your-specific-use-case)
  - [Specific benchmarking datasets](#specific-benchmarking-datasets)
  - [Specific variant callers](#specific-variant-callers)

## Quick start guide

Follow these steps to run ONCOLINER with the default configuration and default datasets (tumorized and mosaic genomes). First, create a directory to store the ONCOLINER workspace:

```
mkdir oncoliner_workspace
cd oncoliner_workspace
```

Download and index the reference FASTA file. All Mosaic and Tumorized genomes are provided in CRAM format and are aligned to GRCh37 without scaffolds and supercontigs, only 1-22-X-Y-MT.

```
# Download all the contigs
wget http://www.ebi.ac.uk/ena/cram/md5/1b22b98cdeb4a9304cb5d48026a85128 -O partial_chr1.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/a0d9851da00400dec1098a9255ac712e -O partial_chr2.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/641e4338fa8d52a5b781bd2a2c08d3c3 -O partial_chr3.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/23dccd106897542ad87d2765d28a19a1 -O partial_chr4.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/0740173db9ffd264d728f32784845cd7 -O partial_chr5.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/1d3a93a248d92a729ee764823acbbc6b -O partial_chr6.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/618366e953d6aaad97dbe4777c29375e -O partial_chr7.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/96f514a9929e410c6651697bded59aec -O partial_chr8.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/3e273117f15e0a400f01055d9f393768 -O partial_chr9.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/988c28e000e84c26d552359af1ea2e1d -O partial_chr10.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/98c59049a2df285c76ffb1c6db8f8b96 -O partial_chr11.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/51851ac0e1a115847ad36449b0015864 -O partial_chr12.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/283f8d7892baa81b510a015719ca7b0b -O partial_chr13.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/98f3cae32b2a2e9524bc19813927542e -O partial_chr14.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/e5645a794a8238215b2cd77acb95a078 -O partial_chr15.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/fc9b1a7b42b97a864f56b348b06095e6 -O partial_chr16.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/351f64d4f4f9ddd45b35336ad97aa6de -O partial_chr17.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/b15d4b2d29dde9d3e4f93d1d0f2cbc9c -O partial_chr18.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/1aacd71f30db8e561810913e0b72636d -O partial_chr19.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/0dec9660ec1efaaf33281c0d5ea2560f -O partial_chr20.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/2979a6085bfe28e3ad6f552f361ed74d -O partial_chr21.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/a718acaa6135fdca8357d5bfe94211dd -O partial_chr22.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/7e0e2e580297b7764e31dbc80c2540dd -O partial_chrX.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/1fa3474750af0948bdf97d5a0ee52e51 -O partial_chrY.fa &
wget http://www.ebi.ac.uk/ena/cram/md5/c68f52674c9fb33aef52dcf399755519 -O partial_chrMT.fa &
wait

# Combine all the chromosomes into a single FASTA file
cat <(echo -e ">1") partial_chr1.fa <(echo -e "\n>2") partial_chr2.fa \
	<(echo -e "\n>3") partial_chr3.fa <(echo -e "\n>4") partial_chr4.fa \
	<(echo -e "\n>5") partial_chr5.fa <(echo -e "\n>6") partial_chr6.fa \
	<(echo -e "\n>7") partial_chr7.fa <(echo -e "\n>8") partial_chr8.fa \
	<(echo -e "\n>9") partial_chr9.fa <(echo -e "\n>10") partial_chr10.fa \
	<(echo -e "\n>11") partial_chr11.fa <(echo -e "\n>12") partial_chr12.fa \
	<(echo -e "\n>13") partial_chr13.fa <(echo -e "\n>14") partial_chr14.fa \
	<(echo -e "\n>15") partial_chr15.fa <(echo -e "\n>16") partial_chr16.fa \
	<(echo -e "\n>17") partial_chr17.fa <(echo -e "\n>18") partial_chr18.fa \
	<(echo -e "\n>19") partial_chr19.fa <(echo -e "\n>20") partial_chr20.fa \
	<(echo -e "\n>21") partial_chr21.fa <(echo -e "\n>22") partial_chr22.fa \
	<(echo -e "\n>X") partial_chrX.fa <(echo -e "\n>Y") partial_chrY.fa \
	<(echo -e "\n>MT") partial_chrMT.fa > Homo_sapiens_assembly19.fa

# Index the FASTA file with SAMtools
samtools faidx Homo_sapiens_assembly19.fa
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

Then, download the Mosaic genomes and their truth VCF files. Follow the instructions for requesting access and downloading the PCAWG Mosaic genomes and their truth files from [here](https://dcc.icgc.org/releases/PCAWG/pilot50-mosaic) and the HMF mosaic genomes and their truth files from [here](https://ega-archive.org/studies/EGAS50000000460).
```
mkdir -p benchmarking_datasets/mosaic_genomes/mosaic_genome_PCAWG_0
mkdir -p benchmarking_datasets/mosaic_genomes/mosaic_genome_PCAWG_1
mkdir -p benchmarking_datasets/mosaic_genomes/mosaic_genome_PCAWG_2
# Download data

mkdir -p benchmarking_datasets/mosaic_genomes/mosaic_genome_HMF
# Download data
```

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
singularity pull oncoliner.sif docker://ghcr.io/eucancan/oncoliner:latest
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
singularity pull oncoliner.sif docker://ghcr.io/eucancan/oncoliner:latest
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

### Assessment (only)

```bash
singularity exec oncoliner.sif python3 -O /oncoliner/oncoliner_launcher.py -c config.tsv -pf pipeline_1_folder -o output_folder --max-processes 48
```

To run ONCOLINER assessment, you must provide the following arguments (ONCOLINER will automatically enter the assessment mode):
* `-c` or `--config`: path to the configuration file.
* `-pf` or `--pipelines-folders`: path to the pipelines folders (one or more).
* `-o` or `--output`: path to the output folder.

### Assessment and improvement (only)

```bash
singularity exec oncoliner.sif python3 -O /oncoliner/oncoliner_launcher.py -c config.tsv -pf pipeline_1_folder -cf callers_folder -o output_folder --max-processes 48
```

To run ONCOLINER improvement, you need to provide the following arguments (ONCOLINER will automatically first run the assessment and then enter the improvement mode):
* `-c` or `--config`: path to the configuration file.
* `-pf` or `--pipelines-folders`: path to the pipelines folders (one or more).
* `-cf` or `--callers-folder`: path to the callers folder (it will be used to compute the improvement).
* `-o` or `--output`: path to the output folder.

### Assessment, improvement and harmonization

```bash
singularity exec oncoliner.sif python3 -O /oncoliner/oncoliner_launcher.py -c config.tsv -pf pipeline_1_folder pipelines_2_folder -cf callers_folder -o output_folder --max-processes 48
```

To run ONCOLINER harmonization, you need to provide the following arguments (ONCOLINER will automatically first run the assessment and improvement and then enter the harmonization mode):
* `-c` or `--config`: path to the configuration file.
* `-pf` or `--pipelines-folders`: path to the pipelines folders (more than one).
* `-cf` or `--callers-folder`: path to the callers folder (it will be used to compute the improvement and then the harmonization).
* `-o` or `--output`: path to the output folder.

#### Configuration file<!-- omit in toc -->

The configuration file is a TSV file with the following columns:
* `sample_name`: sample name.
* `sample_types`: sample types (recall or precision), separated by `,`.
* `reference_fasta_path`: path to the reference FASTA file.
* `truth_vcf_paths`: path(s) to the truth VCF files, separated by `,`. They can also be wildcard paths (e.g. `truths/*.vcf.gz`).
* `bed_mask_paths` (optional): path(s) to BED files, separated by `,`, describing regions where no False Positive will be computed (they will be skipped). They can also be wildcard paths (e.g. `truths/*.bed`).

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

Depending on the use case, it may be advisable to normalize indels and SNVs before running ONCOLINER. For this purpose, we recommend using pre.py from [Illumina's Haplotype Comparison Tools (hap.py)](https://github.com/Illumina/hap.py). We provide an standalone and containerized **[EUCANCan's pre.py wrapper](https://github.com/EUCANCan/prepy-wrapper)** for this purpose, specially the bulk version of the wrapper.

## Additional software

Along with ONCOLINER, in this repository we also provide additional stand-alone software solutions for multiple needs associated with the improvement, standardization and harmonization of genome analysis across centers.

### PipelineDesigner

A standalone tool that helps users to find the best strategy to combine and merge specific variant callers to maximize recall and precision over all variant types. More information about this tool can be found in the [PipelineDesigner README](/tools/pipeline_designer/README.md).

### VCF Intersect

A standalone tool that allows users to intersect two different groups of VCF files. More information about this tool can be found in the [VCF Intersect README](/tools/vcf_intersect/README.md).

### VCF Union

A standalone tool that allows users to merge two different groups of VCF files. More information about this tool can be found in the [VCF Union README](/tools/vcf_union/README.md).

## How to use ONCOLINER in your specific use case

ONCOLINER is a flexible tool that can be used in multiple use cases. In this section we will explain how to use ONCOLINER in some of the most common use cases.

### Specific benchmarking datasets

ONCOLINER can be used to evaluate pipelines using user-defined benchmarking datasets. For this purpose, you must adapt the [default_config.tsv](/default_config.tsv) file to your specific use case (see [Configuration file](#configuration-file)). Make sure that your [Pipeline folders](#pipelines-folders) contain the results of executing each pipeline on each of your samples. Note that ONCOLINER will not be able to provide you with recommendations for improvement and harmonization if you do not provide the [Callers folder](#callers-folder) with your samples (see [Specific variant callers](#specific-variant-callers)).

### Specific variant callers

ONCOLINER can be used to improve and harmonize pipelines using specific variant callers (apart from the ones provided in the [quick start guide](#quick-start-guide) for the default datasets). For this purpose, you must adapt the [Callers folder](#callers-folder) to your specific use case. To generate this folder, it is highly recommended to use ONCOLINER assessment for each variant caller. The [Callers folder](#callers-folder) must contain the results of executing each variant caller on each of your samples.

If you also want to generate combinations of your variant callers for ONCOLINER improvement and harmonization, it is highly recommended you use [PipelineDesigner](#pipelinedesigner). In the `evaluations` folder generated by the tool's output, you can find the assessment results of the combinations of your variant callers. You can use that folder as the [Callers folder](#callers-folder) for ONCOLINER improvement and harmonization directly.
