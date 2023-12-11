# VCF Union<!-- omit in toc -->

VCF Union is a standalone tool that allows the user to union two groups of VCF/BCF/VCF.GZ files. It follows the same procedure as ONCOLINER's assessment module, see [ONCOLINER's assessment module](../../modules/oncoliner_assessment/) for more information about the process.

VCF Union is part of the [ONCOLINER suite](../../README.md) and is provided as a standalone command line tool. It is available as in the [Docker image](../../Dockerfile) and [Singularity image](../../singularity.def) of ONCOLINER.

## Table of contents<!-- omit in toc -->
- [Usage](#usage)
  - [Interface](#interface)


## Usage

The main executable code is in the [`src/`](/src/) folder. There is one executable file: [`union_main.py`](/src/union_main.py). It is provided as a standalone command line tool. Example of usage:

```bash
python3 src/union_main.py --files-1 file_1.vcf file_2.vcf --files-2 file_3.vcf file_4.vcf -o union_out
```

### Interface

```
usage: union_main.py [-h] --files-1 FILES_1 [FILES_1 ...] --files-2
                         FILES_2 [FILES_2 ...] -o OUTPUT [-it INDEL_THRESHOLD]
                         [-wr WINDOW_RADIUS] [--combine-genes-annotations]

Union two sets of VCF/BCF/VCF.GZ files

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
```
