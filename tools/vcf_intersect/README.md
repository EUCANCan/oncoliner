# VCF Intersect<!-- omit in toc -->

VCF Intersect is a standalone tool that allows the user to intersect two groups of VCF/BCF/VCF.GZ files. It follows the same procedure as ONCOLINER's assessment module, see [ONCOLINER's assessment module](../../modules/oncoliner_assessment/) for more information about the process.

VCF Intersect is part of the [ONCOLINER suite](../../README.md) and is provided as a standalone command line tool. It is available as in the [Docker image](../../Dockerfile) and [Singularity image](../../singularity.def) of ONCOLINER.

## Table of contents<!-- omit in toc -->
- [Usage](#usage)
  - [Interface](#interface)


## Usage

The main executable code is in the [`src/`](/src/) folder. There is one executable file: [`intersect_main.py`](/src/intersect_main.py). It is provided as a standalone command line tool. Example of usage:

```bash
python3 src/intersect_main.py --files-1 file_1.vcf file_2.vcf --files-2 file_3.vcf file_4.vcf -o intersect_out
```

### Interface

```
usage: intersect_main.py [-h] --files-1 FILES_1 [FILES_1 ...] --files-2
                         FILES_2 [FILES_2 ...] -o OUTPUT [-it INDEL_THRESHOLD]
                         [-wr WINDOW_RADIUS] [--combine-genes-annotations]

Intersect two sets of VCF/BCF/VCF.GZ files

optional arguments:
  -h, --help            show this help message and exit
  --files-1 FILES_1 [FILES_1 ...]
                        VCF/BCF/VCF.GZ files from the first set
  --files-2 FILES_2 [FILES_2 ...]
                        VCF/BCF/VCF.GZ files from the second set
  -o OUTPUT, --output OUTPUT
                        Prefix path for the output VCF files
  -it INDEL_THRESHOLD, --indel-threshold INDEL_THRESHOLD
                        Indel threshold, inclusive (default=100)
  -wr WINDOW_RADIUS, --window-radius WINDOW_RADIUS
                        Window radius (default=100)
  --combine-genes-annotations
                        Combine genes and annotations from the input VCF files
```
