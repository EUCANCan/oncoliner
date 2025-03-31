# Copyright 2023 - Barcelona Supercomputing Center
# Author: Rodrigo Martín
# BSC Dual License
from typing import List, Tuple, Sequence, Iterator
from collections import OrderedDict
import gzip
import pandas as pd
import pysam

from variant_extractor import VariantExtractor
from variant_extractor.variants import VariantRecord

from .masks import snv_mask, indel_mask  # noqa
from .constants import ONCOLINER_INFO_GENES_NAME  # noqa


def _extract_header(vcf_files: List[str]) -> Tuple[pysam.VariantHeader, bool]:
    headers = [pysam.VariantFile(open(vcf_file)).header for vcf_file in vcf_files]
    main_header = headers[0]
    # Check if samples are the same in all VCFs
    same_samples = True
    for header in headers[1:]:
        if header.samples.header != main_header.samples.header:
            same_samples = False
        main_header.merge(header)
    return main_header, same_samples


def _get_contigs(header: pysam.VariantHeader, fasta_ref=None):
    contigs = OrderedDict()
    if fasta_ref:
        with open(fasta_ref + '.fai') as f:
            for i, line in enumerate(f):
                chrom, length = line.split()[:2]
                contigs[chrom] = length
    else:
        for contig in header.contigs:
            contigs[contig] = None
    return contigs


def _get_contig_order(contigs: OrderedDict):
    # Set contigs from fasta_ref
    contig_order = dict()
    for i, contig in enumerate(contigs):
        contig_order[contig] = i
    return contig_order


def _set_contigs(header: pysam.VariantHeader, contigs: OrderedDict, remove_chr: bool):
    if remove_chr:
        contigs = OrderedDict((contig.replace('chr', ''), length) for contig, length in contigs.items())
    for contig, length in contigs.items():
        if contig not in header.contigs:
            header.contigs.add(contig, length)
    for contig in header.contigs:
        if contig not in contigs:
            header.contigs.remove_header(contig)


def _write_raw_file(f, header: pysam.VariantHeader, variant_record_list: Sequence[VariantRecord], same_samples: bool, same_formats: bool, remove_chr: bool):
    # Remove all format fields except GT for compatibility between VCFs
    if not same_formats or not same_samples:
        for format_ in header.formats:
            if format_ != 'GT':
                header.formats.remove_header(format_)
    if 'GT' not in header.formats:
        header.formats.add('GT', 1, 'String', 'Genotype')
    header_str = str(header)
    # Reset samples if they are not the same in all VCFs
    if not same_samples:
        header_pos = header_str.find('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO')
        custom_header_header = '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tDUMMY_NORMAL\tDUMMY_TUMOR\n'
        header_str = header_str[:header_pos] + custom_header_header
    f.write(header_str)
    # Dummy samples (in case samples are not the same in all VCFs)
    dummy_samples = {'DUMMY_NORMAL': {'GT': (0, 0)}, 'DUMMY_TUMOR': {'GT': (0, 1)}}
    # Write variants
    for variant_record in variant_record_list:
        # Reset samples if they are not the same in all VCFs
        if not same_formats or not same_samples:
            # Remove all format fields except GT for compatibility between VCFs
            variant_record.format = ['GT']
        if not same_samples:
            variant_record.samples = dummy_samples
        if remove_chr:
            # Remove chr from the first 4 fields
            variant_record_split = str(variant_record).split('\t')
            variant_record_str = '\t'.join([variant_record_split[0].replace('chr', '')] + variant_record_split[1:4] +
                                           [variant_record_split[4].replace('chr', '')] + variant_record_split[5:])
        else:
            variant_record_str = str(variant_record)
        f.write(variant_record_str + '\n')


def extract_variants(vcf_file: str, idx_list: List[int], pass_only: bool = True) -> Iterator[VariantRecord]:
    extractor = VariantExtractor(vcf_file, pass_only=pass_only)
    idx_list = set(idx_list)
    for i, variant_record in enumerate(extractor):
        if i in idx_list:
            yield variant_record
    extractor.close()


def _build_record_list(variants_df: pd.DataFrame, template_vcfs: List[str]) -> List[VariantRecord]:
    variant_record_list = []
    # For each template_vcf create a VariantExtractor
    for vcf_file in template_vcfs:
        vcf_variants = variants_df[variants_df['vcf_file'] == vcf_file]
        for i, variant_record in enumerate(extract_variants(vcf_file, vcf_variants['idx_in_file'], vcf_variants['pass_only'].iloc[0])):
            variant_info = vcf_variants.iloc[i]
            if 'GENES' in variant_info:
                genes_symbols = variant_info['GENES']
                if genes_symbols is not None and len(genes_symbols) > 0:
                    variant_record.info[ONCOLINER_INFO_GENES_NAME] = list(genes_symbols)
            variant_record_list.append(variant_record)
    return variant_record_list


def write_masked_vcfs(variants_df: pd.DataFrame, output_path_prefix: str, indel_threshold: int, fasta_ref=None, command=None, gzip=True):
    df_snv_mask = snv_mask(variants_df)
    df_indel_mask = indel_mask(variants_df, indel_threshold)
    df_snv = variants_df[df_snv_mask]
    df_indel = variants_df[df_indel_mask]
    df_sv = variants_df[~df_snv_mask & ~df_indel_mask]
    for df_split, var_type in zip([df_snv, df_indel, df_sv], ['snv', 'indel', 'sv']):
        if len(df_split) == 0:
            continue
        output_file_path = f'{output_path_prefix}{var_type}.vcf'
        if gzip:
            output_file_path += '.gz'
        write_vcf(df_split, output_file_path, fasta_ref, command)


def write_vcf(variants_df: pd.DataFrame, output_vcf: str, fasta_ref=None, command=None, remove_chr=False):
    template_vcfs = list(variants_df['vcf_file'].unique())
    header, same_samples = _extract_header(template_vcfs)
    # Add meta field with the command used to generate the VCF
    if command:
        header.add_meta('vcf_ops', command)
    # Get contigs
    contigs = _get_contigs(header, fasta_ref)
    # Get contig order
    contig_order = _get_contig_order(contigs)
    # Add contig_order column
    variants_df = variants_df.assign(contig_order=variants_df['start_chrom'].map(contig_order))
    # Sort by chromosome and position
    variants_df.sort_values(by=['contig_order', 'start'], inplace=True)
    # Apply contigs to header
    _set_contigs(header, contigs, remove_chr)
    # Build variant_record_list
    variant_record_list = _build_record_list(variants_df, template_vcfs)
    # Check if all variants have the same format fields
    same_formats = True
    if len(variant_record_list) > 0 and len(template_vcfs) > 1:
        formats = variant_record_list[0].format
        for variant_record in variant_record_list[1:]:
            if variant_record.format != formats:
                same_formats = False
                break

    # Check if the VCF is gzipped
    if output_vcf.endswith('.gz'):
        f = gzip.open(output_vcf, 'wt')
    else:
        f = open(output_vcf, 'w', encoding='utf-8')
    # Write the file
    _write_raw_file(f, header, variant_record_list, same_samples, same_formats, remove_chr)
    f.close()


def _extract_variants(vcf_file, pass_only=True) -> pd.DataFrame:
    try:
        extractor = VariantExtractor(vcf_file, pass_only=pass_only)
        variants_df = extractor.to_dataframe()
        extractor.close()
    except Exception as e:
        raise IOError(f'Error reading VCF file {vcf_file}') from e
    variants_df['vcf_file'] = vcf_file
    variants_df['vcf_file'] = variants_df['vcf_file'].astype('category')
    variants_df['pass_only'] = pass_only
    variants_df['pass_only'] = variants_df['pass_only'].astype('bool')
    variants_df['idx_in_file'] = variants_df.index
    return variants_df


def read_vcfs(vcf_files, pass_only=True) -> pd.DataFrame:
    if len(vcf_files) == 0:
        empty_df = VariantExtractor.empty_dataframe()
        empty_df.columns += ['vcf_file', 'pass_only', 'idx_in_file']
        empty_df['vcf_file'] = empty_df['vcf_file'].astype('category')
        empty_df['pass_only'] = empty_df['pass_only'].astype('bool')
        return empty_df
    vcf_dfs = [_extract_variants(vcf_file, pass_only=pass_only) for vcf_file in vcf_files]
    return pd.concat(vcf_dfs, ignore_index=True)
