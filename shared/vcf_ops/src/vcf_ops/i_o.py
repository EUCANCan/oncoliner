# Copyright 2023 - Barcelona Supercomputing Center
# Author: Rodrigo Martín
# BSC Dual License
from typing import List, Tuple
from collections import OrderedDict
import gzip
import pandas as pd
import pysam

from variant_extractor import VariantExtractor

from .masks import snv_mask, indel_mask  # noqa


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
            contigs[contig] = contig.length
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

def _write_raw_file(f, header: pysam.VariantHeader, variants_obj_df, same_samples: bool, same_formats: bool, remove_chr: bool):
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
    for variant_record_obj in variants_obj_df:
        # Reset samples if they are not the same in all VCFs
        if not same_formats or not same_samples:
            # Remove all format fields except GT for compatibility between VCFs
            variant_record_obj.format = ['GT']
        if not same_samples:
            variant_record_obj.samples = dummy_samples
        if remove_chr:
            # Remove chr from the first 4 fields
            variant_record_split = str(variant_record_obj).split('\t')
            variant_record_str = '\t'.join([variant_record_split[0].replace('chr', '')] + variant_record_split[1:4] +
                                           [variant_record_split[4].replace('chr', '')] + variant_record_split[5:])
        else:
            variant_record_str = str(variant_record_obj)
        f.write(variant_record_str + '\n')


def write_masked_vcfs(variants_df, output_path_prefix: str, indel_threshold: int, fasta_ref=None, command=None, gzip=True):
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


def write_vcf(variants_df: pd.DataFrame, output_vcf, fasta_ref=None, command=None):
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
    # Check if there are chr and non-chr contigs mixed
    # Get all unique contigs in variants
    variants_contigs = set(variants_df['variant_record_obj'].map(lambda x: x.contig))
    remove_chr = False
    for variants_contig in variants_contigs:
        if (variants_contig.startswith('chr') and variants_contig.replace('chr', '') in variants_contigs) or \
            (not variants_contig.startswith('chr') and 'chr' + variants_contig in variants_contigs) or \
            (variants_contig not in contigs and
             (variants_contig.replace('chr', '') in contigs or 'chr' + variants_contig in contigs)):
            remove_chr = True
            break
    # Apply contigs to header
    _set_contigs(header, contigs, remove_chr)
    # Check if all variants have the same format fields
    formats = variants_df.iloc[0]['variant_record_obj'].format
    same_formats = True
    if len(template_vcfs) > 1:
        for variant_record_obj in variants_df['variant_record_obj']:
            if variant_record_obj.format != formats:
                same_formats = False

    # Check if the VCF is gzipped
    if output_vcf.endswith('.gz'):
        f = gzip.open(output_vcf, 'wt')
    else:
        f = open(output_vcf, 'w')
    # Write the file
    _write_raw_file(f, header, variants_df['variant_record_obj'], same_samples, same_formats, remove_chr)
    f.close()


def _extract_variants(vcf_file) -> pd.DataFrame:
    extractor = VariantExtractor(vcf_file, pass_only=True)
    variants_df = extractor.to_dataframe()
    variants_df['vcf_file'] = vcf_file
    return variants_df


def read_vcfs(vcf_files):
    if len(vcf_files) == 0:
        empty_df = VariantExtractor.empty_dataframe()
        empty_df['vcf_file'] = ''
        return empty_df
    vcf_dfs = [_extract_variants(vcf_file) for vcf_file in vcf_files]
    return pd.concat(vcf_dfs, ignore_index=True)
