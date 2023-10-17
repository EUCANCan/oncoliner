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
