import os
import sys
import argparse
import glob
import pandas as pd

# Add vcf-ops to the path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'shared', 'vcf_ops', 'src'))

from vcf_ops import VariantType  # noqa
from vcf_ops.i_o import read_vcfs, write_masked_vcfs  # noqa
from vcf_ops.masks import snv_mask, indel_mask  # noqa
from vcf_ops.intersect import intersect  # noqa
from vcf_ops.metrics import compute_metrics  # noqa
from vcf_ops.constants import DEFAULT_CONTIGS, DEFAULT_INDEL_THRESHOLD, DEFAULT_WINDOW_RADIUS, DEFAULT_SV_BINS  # noqa
from indel_sv_converter import convert_indels, convert_svs  # noqa

def _ingest(truth_vcfs, test_vcfs, fasta_ref, indel_threshold, output_prefix, contigs, keep_intermediates=False):
    # Load truth and test VCFs
    df_truth = read_vcfs(truth_vcfs)
    df_test = read_vcfs(test_vcfs)

    contigs = set(contigs)
    # Skip SGL, 0-length variants and variants without contig in contigs list
    contigs_truth_mask = df_truth['start_chrom'].isin(contigs) & df_truth['end_chrom'].isin(contigs)
    contigs_test_mask = df_test['start_chrom'].isin(contigs) & df_test['end_chrom'].isin(contigs)
    sgl_truth_mask = df_truth['type_inferred'] == VariantType.SGL.name
    sgl_test_mask = df_test['type_inferred'] == VariantType.SGL.name
    length_truth_mask = (df_truth['length'] == 0) & \
        (df_truth['type_inferred'] != VariantType.SNV.name) & (df_truth['type_inferred'] != VariantType.TRA.name)
    length_test_mask = (df_test['length'] == 0) & \
        (df_test['type_inferred'] != VariantType.SNV.name) & (df_test['type_inferred'] != VariantType.TRA.name)
    df_skipped_truth = df_truth[sgl_truth_mask | length_truth_mask | ~contigs_truth_mask]
    df_skipped_test = df_test[sgl_test_mask | length_test_mask | ~contigs_test_mask]
    df_truth = df_truth[~sgl_truth_mask & ~length_truth_mask & contigs_truth_mask]
    df_test = df_test[~sgl_test_mask & ~length_test_mask & contigs_test_mask]

    # Separate indels and SNVs from SVs
    indel_snv_truth_mask = snv_mask(df_truth) | indel_mask(df_truth, indel_threshold)
    indel_snv_test_mask = snv_mask(df_test) | indel_mask(df_test, indel_threshold)
    df_truth_indel = df_truth[indel_snv_truth_mask]
    df_test_indel = df_test[indel_snv_test_mask]
    df_truth_sv = df_truth[~indel_snv_truth_mask]
    df_test_sv = df_test[~indel_snv_test_mask]

    # Convert everything to indel or sv representation
    df_truth_indel = convert_indels(df_truth_indel, fasta_ref)
    df_test_indel = convert_indels(df_test_indel, fasta_ref)
    df_truth_sv = convert_svs(df_truth_sv, fasta_ref)
    df_test_sv = convert_svs(df_test_sv, fasta_ref)

    # Write CSVs if necessary
    if keep_intermediates:
        df_truth_sv.to_csv(output_prefix + 'truth_sv.csv', index=False)
        df_test_sv.to_csv(output_prefix + 'test_sv.csv', index=False)
        df_truth_indel.to_csv(output_prefix + 'truth_indel_snv.csv', index=False)
        df_test_indel.to_csv(output_prefix + 'test_indel_snv.csv', index=False)

    # Concat SVs and indels
    df_truth = pd.concat([df_truth_indel, df_truth_sv], ignore_index=True)
    df_test = pd.concat([df_test_indel, df_test_sv], ignore_index=True)

    return df_truth, df_test, df_skipped_truth, df_skipped_test


def main(truth_vcfs, test_vcfs, output_prefix, fasta_ref, indel_threshold=DEFAULT_INDEL_THRESHOLD, window_radius=DEFAULT_WINDOW_RADIUS,
         sv_size_bins=DEFAULT_SV_BINS, contigs=DEFAULT_CONTIGS, keep_intermediates=False, no_gzip=False):
    # Get files from the truth and test vcfs
    truth_vcfs = [file for file_pattern in truth_vcfs for file in glob.glob(file_pattern)]
    test_vcfs = [file for file_pattern in test_vcfs for file in glob.glob(file_pattern)]

    # Sort bins
    sv_size_bins.sort()
    if sv_size_bins[0] < indel_threshold:
        raise ValueError(f'SV size bins must be greater than {indel_threshold}')

    # Read the input files
    df_truth, df_test, df_skipped_truth, df_skipped_test = _ingest(
        truth_vcfs, test_vcfs, fasta_ref, indel_threshold, output_prefix, contigs, keep_intermediates)

    # Run benchmark
    df_tp, df_tp_dup, \
        df_fp, df_fp_dup, \
        df_fn, df_fn_dup = intersect(df_truth, df_test, indel_threshold, window_radius)

    # Write VCF files
    command = ' '.join(sys.argv)
    if len(df_tp) > 0:
        write_masked_vcfs(df_tp, f'{output_prefix}tp.', indel_threshold, fasta_ref, command, not no_gzip)
        print(f'True positives can be found in {output_prefix}tp.*')
    if len(df_tp_dup) > 0:
        write_masked_vcfs(df_tp_dup, f'{output_prefix}tp_dup.', indel_threshold, fasta_ref, command, not no_gzip)
        print(f'True positives (duplicates) can be found in {output_prefix}tp_dup.*')
    if len(df_fp) > 0:
        write_masked_vcfs(df_fp, f'{output_prefix}fp.', indel_threshold, fasta_ref, command, not no_gzip)
        print(f'False positives can be found in {output_prefix}fp.*')
    if len(df_fp_dup) > 0:
        write_masked_vcfs(df_fp_dup, f'{output_prefix}fp_dup.', indel_threshold, fasta_ref, command, not no_gzip)
        print(f'False positives (duplicates) can be found in {output_prefix}fp_dup.*')
    if len(df_skipped_test) > 0:
        write_masked_vcfs(df_skipped_test, f'{output_prefix}skipped_test.',
                          indel_threshold, fasta_ref, command, not no_gzip)
        print(f'Skipped test variants can be found in {output_prefix}skipped_test.*')
    if len(df_fn) > 0:
        write_masked_vcfs(df_fn, f'{output_prefix}fn.', indel_threshold, fasta_ref, command, not no_gzip)
        print(f'False negatives can be found in {output_prefix}fn.*')
    if len(df_fn_dup) > 0:
        write_masked_vcfs(df_fn_dup, f'{output_prefix}fn_dup.',
                          indel_threshold, fasta_ref, command, not no_gzip)
        print(f'False negatives (duplicates) can be found in {output_prefix}fn_dup.*')
    if len(df_skipped_truth) > 0:
        write_masked_vcfs(df_skipped_truth, f'{output_prefix}skipped_truth.',
                          indel_threshold, fasta_ref, command, not no_gzip)
        print(f'Skipped truth variants can be found in {output_prefix}skipped_truth.*')

    # Compute metrics
    metrics_df = compute_metrics(df_tp, df_fp, df_fn, indel_threshold, window_radius, sv_size_bins)
    # Write CSV with metrics
    metrics_df.to_csv(f'{output_prefix}metrics.csv', index=False)

    # Print info about metrics
    print(f'True positives: {len(df_tp)} + {len(df_tp_dup)} duplicates')
    print(f'False positives: {len(df_fp)} + {len(df_fp_dup)} duplicates')
    print(f'False negatives: {len(df_fn)} + {len(df_fn_dup)} duplicates')
    print(f'Total truth variants analyzed: {len(df_truth)} + {len(df_skipped_truth)} skipped')
    print(f'Total test variants analyzed: {len(df_test)} + {len(df_skipped_test)} skipped')
    print('Benchmark metrics:')
    print(metrics_df.to_string(index=False))
    print(f'Benchmark metrics can be found in {output_prefix}metrics.csv')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Oncoliner Assesment')
    parser.add_argument('-t', '--truths', help='Path to the VCF truth files', nargs='+', required=True, type=str)
    parser.add_argument('-v', '--tests', help='Path to the VCF test files', nargs='+', required=True, type=str)
    parser.add_argument('-o', '--output_prefix',
                        help='Prefix path for the output_prefix VCF files', required=True, type=str)
    parser.add_argument('-f', '--fasta-ref', help='Path to reference FASTA file', required=True, type=str)
    parser.add_argument('-it', '--indel-threshold',
                        help=f'Indel threshold, inclusive (default={DEFAULT_INDEL_THRESHOLD})', default=DEFAULT_INDEL_THRESHOLD, type=int)
    parser.add_argument('-wr', '--window-radius',
                        help=f'Window ratio (default={DEFAULT_WINDOW_RADIUS})', default=DEFAULT_WINDOW_RADIUS, type=int)
    parser.add_argument(
        '--sv-size-bins', help=f'SV size bins for the output_prefix metrics (default={DEFAULT_SV_BINS})', nargs='+', default=DEFAULT_SV_BINS, type=int)
    parser.add_argument(
        '--contigs', help=f'Contigs to process (default={DEFAULT_CONTIGS})', nargs='+', default=DEFAULT_CONTIGS, type=str)
    parser.add_argument('--keep-intermediates',
                        help='Keep intermediate CSV/VCF files from input VCF files', action='store_true', default=False)
    parser.add_argument('--no-gzip', help='Do not gzip output_prefix VCF files', action='store_true', default=False)
    args = parser.parse_args()

    # Convert everything to absolute paths
    args.truths = [os.path.abspath(x) for x in args.truths]
    args.tests = [os.path.abspath(x) for x in args.tests]
    args.fasta_ref = os.path.abspath(args.fasta_ref)
    args.output_prefix = os.path.abspath(args.output_prefix)

    main(args.truths, args.tests, args.output_prefix, args.fasta_ref, args.indel_threshold,
         args.window_radius, args.sv_size_bins, args.contigs, args.keep_intermediates, args.no_gzip)
