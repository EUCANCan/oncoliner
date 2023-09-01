# Copyright 2023 - Barcelona Supercomputing Center
# Author: Rodrigo Martín
# BSC Dual License
import pandas as pd

from variant_extractor.variants import VariantType

from ._internal.internal_ops import intersect_exact, intersect_window  # noqa
from .masks import snv_mask, indel_mask  # noqa
from .genes import is_gene_annotated, extract_protein_affected_genes, add_gene_annotation_to_variant_record


def _combine_gene_annotations(df_tp: pd.DataFrame):
    # Add gene annotations from the truth files if not present
    # Check if the variant_record_obj is gene annotated in the test file
    is_test_annotated = df_tp['variant_record_obj'].apply(is_gene_annotated)
    if is_test_annotated.any():
        return
    # Check if the variant_record_obj is gene annotated in the truth file
    is_truth_annotated = df_tp['variant_record_obj_truth'].apply(is_gene_annotated)
    if not is_truth_annotated.any():
        return
    # Extract protein affected genes from the truth file
    truth_protein_affected_genes = df_tp['variant_record_obj_truth'].apply(extract_protein_affected_genes)

    # Add gene annotations to the test file
    for idx, row in df_tp[is_truth_annotated].iterrows():
        add_gene_annotation_to_variant_record(row['variant_record_obj'], truth_protein_affected_genes[idx])


def intersect(df_truth, df_test, indel_threshold, window_radius, combine_gene_annotations=True):
    # Intersect for SNV and indels comparing position, alt, length and type
    snv_indel_truth_mask = snv_mask(df_truth) | indel_mask(df_truth, indel_threshold)
    snv_indel_test_mask = snv_mask(df_test) | indel_mask(df_test, indel_threshold)
    snv_indel_truth = df_truth[snv_indel_truth_mask]
    snv_indel_test = df_test[snv_indel_test_mask]
    snv_indel_tp, snv_indel_tp_dup, snv_indel_fp, snv_indel_fp_dup, snv_indel_fn, snv_indel_fn_dup = \
        intersect_exact(snv_indel_truth, snv_indel_test, ['start_chrom', 'start', 'alt', 'length', 'type_inferred'])
    # Remove from the rest of the benchmark
    df_truth = df_truth[~snv_indel_truth_mask]
    df_test = df_test[~snv_indel_test_mask]

    # Benchmark INS comparing start position and length
    ins_truth_mask = df_truth['type_inferred'] == VariantType.INS.name
    ins_test_mask = df_test['type_inferred'] == VariantType.INS.name
    ins_truth = df_truth[ins_truth_mask]
    ins_test = df_test[ins_test_mask]
    ins_tp, ins_tp_dup,\
        ins_fp, ins_fp_dup,\
        ins_fn, ins_fn_dup = intersect_window(ins_truth, ins_test, ['start_chrom'],
                                              ['start', 'length'], window_radius)
    # Remove from the rest of the benchmark
    df_truth = df_truth[~ins_truth_mask]
    df_test = df_test[~ins_test_mask]

    # Benchmark rest of SVs comparing start and end positions
    sv_tp, sv_tp_dup,\
        sv_fp, sv_fp_dup,\
        sv_fn, sv_fn_dup = intersect_window(df_truth, df_test, ['start_chrom', 'end_chrom', 'brackets'],
                                            ['start', 'end'], window_radius)

    # Concatenate all results
    df_tp = pd.concat([snv_indel_tp, ins_tp, sv_tp])
    df_tp_dup = pd.concat([snv_indel_tp_dup, ins_tp_dup, sv_tp_dup])
    df_fp = pd.concat([snv_indel_fp, ins_fp, sv_fp])
    df_fp_dup = pd.concat([snv_indel_fp_dup, ins_fp_dup, sv_fp_dup])
    df_fn = pd.concat([snv_indel_fn, ins_fn, sv_fn])
    df_fn_dup = pd.concat([snv_indel_fn_dup, ins_fn_dup, sv_fn_dup])

    if combine_gene_annotations:
        _combine_gene_annotations(df_tp)

    return df_tp, df_tp_dup, df_fp, df_fp_dup, df_fn, df_fn_dup


if __name__ == '__main__':
    import argparse
    from .i_o import read_vcfs, write_masked_vcfs
    from .constants import DEFAULT_INDEL_THRESHOLD, DEFAULT_WINDOW_RADIUS

    parser = argparse.ArgumentParser(description='Intersect two sets of VCF/BCF/VCF.GZ files')
    parser.add_argument('--files-1', nargs='+', required=True, help='VCF/BCF/VCF.GZ files from the first set')
    parser.add_argument('--files-2', nargs='+', required=True, help='VCF/BCF/VCF.GZ files from the second set')
    parser.add_argument('-o', '--output', help='Prefix path for the output VCF files', required=True, type=str)
    parser.add_argument('-it', '--indel-threshold',
                        help=f'Indel threshold, inclusive (default={DEFAULT_INDEL_THRESHOLD})', default=DEFAULT_INDEL_THRESHOLD, type=int)
    parser.add_argument('-wr', '--window-radius',
                        help=f'Window radius (default={DEFAULT_WINDOW_RADIUS})', default=DEFAULT_WINDOW_RADIUS, type=float)
    args = parser.parse_args()

    # Read the input files
    df_truth = read_vcfs(args.files_1)
    df_test = read_vcfs(args.files_2)

    # Intersect
    df_tp, df_tp_dup, df_fp, df_fp_dup, df_fn, df_fn_dup = intersect(df_truth, df_test, args.indel_threshold, args.window_radius)

    # Write VCF files
    if len(df_tp) > 0:
        write_masked_vcfs(df_tp, args.output + 'intersect_in.', args.test_files, args.indel_threshold)
        print(f'True positives can be found in {args.output}intersect_in.*')
    if len(df_tp_dup) > 0:
        write_masked_vcfs(df_tp_dup, args.output + 'intersect_in_dup.', args.test_files, args.indel_threshold)
        print(f'True positives with duplicates can be found in {args.output}intersect_in_dup.*')
    if len(df_fp) > 0:
        write_masked_vcfs(df_fp, args.output + 'intersect_out_2.', args.test_files, args.indel_threshold)
        print(f'False positives can be found in {args.output}intersect_out_2.*')
    if len(df_fp_dup) > 0:
        write_masked_vcfs(df_fp_dup, args.output + 'intersect_out_2_dup.', args.test_files, args.indel_threshold)
        print(f'False positives with duplicates can be found in {args.output}intersect_out_2_dup.*')
    if len(df_fn) > 0:
        write_masked_vcfs(df_fn, args.output + 'intersect_out_1.', args.truth_files, args.indel_threshold)
        print(f'False negatives can be found in {args.output}intersect_out_1.*')
    if len(df_fn_dup) > 0:
        write_masked_vcfs(df_fn_dup, args.output + 'intersect_out_1_dup.', args.truth_files, args.indel_threshold)
        print(f'False negatives with duplicates can be found in {args.output}intersect_out_1_dup.*')
