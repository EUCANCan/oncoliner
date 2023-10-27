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


def intersect(df_truth, df_test, indel_threshold, window_radius, combine_gene_annotations=False):
    # Intersect SNVs comparing start position and alt
    snv_truth_mask = snv_mask(df_truth)
    snv_test_mask = snv_mask(df_test)
    snv_truth = df_truth[snv_truth_mask]
    snv_test = df_test[snv_test_mask]
    snv_tp, snv_tp_dup, snv_fp, snv_fp_dup, snv_fn, snv_fn_dup = \
        intersect_exact(snv_truth, snv_test, ['start_chrom', 'start', 'alt'])
    # Remove from the rest from the intersection
    df_truth = df_truth[~snv_truth_mask]
    df_test = df_test[~snv_test_mask]

    # Intersect indel ins/dup start position and alt
    indel_ins_truth_mask = indel_mask(df_truth, indel_threshold) & (df_truth['type_inferred'] != VariantType.DEL.name)
    indel_ins_test_mask = indel_mask(df_test, indel_threshold) & (df_test['type_inferred'] != VariantType.DEL.name)
    indel_ins_truth = df_truth[indel_ins_truth_mask]
    indel_ins_test = df_test[indel_ins_test_mask]
    indel_ins_tp, indel_ins_tp_dup, indel_ins_fp, indel_ins_fp_dup, indel_ins_fn, indel_ins_fn_dup = \
        intersect_exact(indel_ins_truth, indel_ins_test, ['start_chrom', 'start', 'alt'])
    # Remove from the rest from the intersection
    df_truth = df_truth[~indel_ins_truth_mask]
    df_test = df_test[~indel_ins_test_mask]

    # Intersect indel deletions comparing start position and length
    indel_del_truth_mask = indel_mask(df_truth, indel_threshold) & (df_truth['type_inferred'] == VariantType.DEL.name)
    indel_del_test_mask = indel_mask(df_test, indel_threshold) & (df_test['type_inferred'] == VariantType.DEL.name)
    indel_del_truth = df_truth[indel_del_truth_mask]
    indel_del_test = df_test[indel_del_test_mask]
    indel_del_tp, indel_del_tp_dup, indel_del_fp, indel_del_fp_dup, indel_del_fn, indel_del_fn_dup = \
        intersect_exact(indel_del_truth, indel_del_test, ['start_chrom', 'start', 'length'])
    # Remove from the rest from the intersection
    df_truth = df_truth[~indel_del_truth_mask]
    df_test = df_test[~indel_del_test_mask]

    # Intersect INS comparing start position and length with a window
    ins_truth_mask = df_truth['type_inferred'] == VariantType.INS.name
    ins_test_mask = df_test['type_inferred'] == VariantType.INS.name
    ins_truth = df_truth[ins_truth_mask]
    ins_test = df_test[ins_test_mask]
    ins_tp, ins_tp_dup,\
        ins_fp, ins_fp_dup,\
        ins_fn, ins_fn_dup = intersect_window(ins_truth, ins_test, ['start_chrom'],
                                              ['start', 'length'], window_radius)
    # Remove from the rest from the intersection
    df_truth = df_truth[~ins_truth_mask]
    df_test = df_test[~ins_test_mask]

    # Intersect rest of SVs comparing start and end positions with a window
    sv_tp, sv_tp_dup,\
        sv_fp, sv_fp_dup,\
        sv_fn, sv_fn_dup = intersect_window(df_truth, df_test, ['start_chrom', 'end_chrom', 'brackets'],
                                            ['start', 'end'], window_radius)

    # Concatenate all results
    df_tp = pd.concat([snv_tp, indel_ins_tp, indel_del_tp, ins_tp, sv_tp])
    df_tp_dup = pd.concat([snv_tp_dup, indel_ins_tp_dup, indel_del_tp_dup, ins_tp_dup, sv_tp_dup])
    df_fp = pd.concat([snv_fp, indel_ins_fp, indel_del_fp, ins_fp, sv_fp])
    df_fp_dup = pd.concat([snv_fp_dup, indel_ins_fp_dup, indel_del_fp_dup, ins_fp_dup, sv_fp_dup])
    df_fn = pd.concat([snv_fn, indel_ins_fn, indel_del_fn, ins_fn, sv_fn])
    df_fn_dup = pd.concat([snv_fn_dup, indel_ins_fn_dup, indel_del_fn_dup, ins_fn_dup, sv_fn_dup])

    if combine_gene_annotations:
        _combine_gene_annotations(df_tp)

    return df_tp, df_tp_dup, df_fp, df_fp_dup, df_fn, df_fn_dup
