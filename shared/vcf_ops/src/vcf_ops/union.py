# Copyright 2023 - Barcelona Supercomputing Center
# Author: Rodrigo Martín
# BSC Dual License
import pandas as pd

from .intersect import intersect


def union(df_truth, df_test, indel_threshold, window_radius):
    # Intersect
    df_tp, df_tp_dup, df_fp, df_fp_dup, df_fn, df_fn_dup = intersect(
        df_truth, df_test, indel_threshold, window_radius, False)

    # Union
    df_union = pd.concat([df_tp, df_fp, df_fn])
    df_union_dup = pd.concat([df_tp_dup, df_fp_dup, df_fn_dup])

    return df_union, df_union_dup
