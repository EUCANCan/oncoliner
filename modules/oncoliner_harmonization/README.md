# ONCOLINER: Harmonization module<!-- omit in toc -->

![ONCOLINER logo](../../docs/images/ONCOLINER_LOGO_COLOR.png)

WIP

## Dependencies
ONCOLINER's harmonization module makes use of the following Python modules:
* [`pandas`](https://pandas.pydata.org/)
* [`pysam`](https://github.com/pysam-developers/pysam)
* [`variant-extractor`](https://github.com/EUCANCan/variant-extractor)

You may install them using pip:
```
pip3 install pandas pysam variant-extractor
```

However, we recommend using the provided [Dockerfile](../../Dockerfile)/[Singularity recipe](../../singularity.def) for building the whole ONCOLINER suite to avoid dependency issues.
