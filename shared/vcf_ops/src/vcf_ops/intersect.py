# Copyright 2023 - Barcelona Supercomputing Center
# Author: Rodrigo Martín
# BSC Dual License
import pandas as pd

from variant_extractor.variants import VariantType

from ._internal.internal_ops import intersect_exact, intersect_window  # noqa
from .masks import snv_mask, indel_mask  # noqa


def intersect(df_truth, df_test, indel_threshold, window_radius):
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
    sv_tp_list, sv_tp_dup_list = [], []
    sv_fp_list, sv_fp_dup_list = [], []
    sv_fn_list, sv_fn_dup_list = [], []

    for bracket in set(df_truth['brackets'].unique()).union(set(df_test['brackets'].unique())):
        bracket_truth_mask = df_truth['brackets'] == bracket
        bracket_test_mask = df_test['brackets'] == bracket

        sv_truth_bracket = df_truth[bracket_truth_mask]
        sv_test_bracket = df_test[bracket_test_mask]

        df_truth = df_truth[~bracket_truth_mask]
        df_test = df_test[~bracket_test_mask]

        sv_tp, sv_tp_dup,\
            sv_fp, sv_fp_dup,\
            sv_fn, sv_fn_dup = intersect_window(sv_truth_bracket, sv_test_bracket, ['start_chrom', 'end_chrom'],
                                                ['start', 'end'], window_radius)

        sv_tp_list.append(sv_tp)
        sv_tp_dup_list.append(sv_tp_dup)
        sv_fp_list.append(sv_fp)
        sv_fp_dup_list.append(sv_fp_dup)
        sv_fn_list.append(sv_fn)
        sv_fn_dup_list.append(sv_fn_dup)

    # Concatenate results from all bracket types
    sv_tp = pd.concat(sv_tp_list) if sv_tp_list else pd.DataFrame()
    sv_tp_dup = pd.concat(sv_tp_dup_list) if sv_tp_dup_list else pd.DataFrame()
    sv_fp = pd.concat(sv_fp_list) if sv_fp_list else pd.DataFrame()
    sv_fp_dup = pd.concat(sv_fp_dup_list) if sv_fp_dup_list else pd.DataFrame()
    sv_fn = pd.concat(sv_fn_list) if sv_fn_list else pd.DataFrame()
    sv_fn_dup = pd.concat(sv_fn_dup_list) if sv_fn_dup_list else pd.DataFrame()

    # Concatenate all results
    df_tp = pd.concat([snv_tp, indel_ins_tp, indel_del_tp, ins_tp, sv_tp])
    df_tp_dup = pd.concat([snv_tp_dup, indel_ins_tp_dup, indel_del_tp_dup, ins_tp_dup, sv_tp_dup])
    df_fp = pd.concat([snv_fp, indel_ins_fp, indel_del_fp, ins_fp, sv_fp])
    df_fp_dup = pd.concat([snv_fp_dup, indel_ins_fp_dup, indel_del_fp_dup, ins_fp_dup, sv_fp_dup])
    df_fn = pd.concat([snv_fn, indel_ins_fn, indel_del_fn, ins_fn, sv_fn])
    df_fn_dup = pd.concat([snv_fn_dup, indel_ins_fn_dup, indel_del_fn_dup, ins_fn_dup, sv_fn_dup])

    return df_tp, df_tp_dup, df_fp, df_fp_dup, df_fn, df_fn_dup
