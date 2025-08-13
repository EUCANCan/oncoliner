# Copyright 2023 - Barcelona Supercomputing Center
# Author: Rodrigo Martín
# BSC Dual License
import pandas as pd


def intersect_exact(df_truth, df_test, matching_fields):
    # Find exact matches
    df_all_tp = pd.merge(df_test[matching_fields].reset_index(), df_truth[matching_fields].reset_index(), how='inner', on=matching_fields,
                         copy=False, suffixes=(None, '_truth')).set_index('index')
    # Drop columns from truth
    df_all_tp.drop([col for col in df_all_tp.columns if col.endswith('_truth') and not col == 'index_truth'], axis=1, inplace=True)
    df_all_tp.rename(columns={'index_truth': 'idx_truth'}, inplace=True)
    # Find duplicates
    df_test_tp_mask = df_test.index.isin(df_all_tp.index)
    df_tp = df_test[df_test_tp_mask]
    df_tp_dup_mask = df_tp.duplicated(subset=matching_fields, keep='first')
    df_tp_dup = df_tp[df_tp_dup_mask]
    df_tp = df_tp[~df_tp_dup_mask]
    # Add idx_truth to df_tp
    # Handle duplicate indices in df_all_tp by taking the first occurrence
    df_tp.loc[df_tp.index, 'idx_truth'] = df_all_tp.loc[df_tp.index, 'idx_truth'].groupby(level=0).first()
    # Find false positives
    df_fp = df_test[~df_test_tp_mask]
    # Find duplicates
    df_fp_dup_mask = df_fp.duplicated(subset=matching_fields, keep='first')
    df_fp_dup = df_fp[df_fp_dup_mask]
    df_fp = df_fp[~df_fp_dup_mask]
    # Find false negatives
    # Find duplicates
    df_all_fn = df_truth[~df_truth.index.isin(df_all_tp['idx_truth'])]
    df_fn_dup_mask = df_all_fn.duplicated(subset=matching_fields, keep='first')
    df_fn_dup = df_all_fn[df_fn_dup_mask]
    df_fn = df_all_fn[~df_fn_dup_mask]
    return df_tp, df_tp_dup, df_fp, df_fp_dup, df_fn, df_fn_dup


def _entries_in_window(df_truth, df_test, matching_fields, window_fields, window_radius):
    # Necessary columns
    necessary_cols = matching_fields + window_fields
    # Drop unnecessary columns
    curr_df_test = df_test[necessary_cols]
    curr_df_truth = df_truth[necessary_cols]
    # Merge on matching fields
    cross_merge = pd.merge(curr_df_truth.reset_index(), curr_df_test.reset_index(), suffixes=('_truth', '_test'),
                           how='inner', on=matching_fields, copy=False)
    # Drop entries that are not in the window
    for window_field in window_fields:
        window_field_test = window_field + '_test'
        window_field_truth = window_field + '_truth'
        diff = (cross_merge[window_field_truth].astype(int) - cross_merge[window_field_test].astype(int)).abs()
        cross_merge = cross_merge[diff <= window_radius]
    return cross_merge.drop(matching_fields, axis=1)


def _matching_window_entries(df_truth, df_test, matching_fields, window_fields, window_radius):
    # Get matching window entries
    cross_merge = _entries_in_window(df_truth, df_test, matching_fields, window_fields, window_radius)
    # Calculate window_fields_sum_diff
    cross_merge['window_fields_sum_test'] = cross_merge[[w + '_test' for w in window_fields]].sum(axis=1)
    cross_merge['window_fields_sum_truth'] = cross_merge[[w + '_truth' for w in window_fields]].sum(axis=1)
    cross_merge['window_fields_sum_diff'] = (
        cross_merge['window_fields_sum_test'] - cross_merge['window_fields_sum_truth']).abs()
    # Sort by window_fields_sum_diff
    cross_merge.sort_values(by='window_fields_sum_diff', inplace=True)
    # Right now, a test entry can match multiple truth entries
    # We want to match a test entry to only one truth entry
    # A truth entry can still be matched to multiple test entries
    # We want to leave the least amount of truth entries unmatched
    # In the case of a tie, we want to select the test entry to the truth entry with the least window_fields_sum_diff
    entries_to_keep = pd.Series(False, index=cross_merge.index)
    curr_cross_merge = cross_merge
    while True:
        duplicated_truth_mask = curr_cross_merge.duplicated(subset=['index_truth'], keep=False)
        unique_truth_df = curr_cross_merge[~duplicated_truth_mask]
        duplicated_truth_df = curr_cross_merge[duplicated_truth_mask]
        new_duplicated_truth_df = duplicated_truth_df[~duplicated_truth_df['index_test'].isin(
            unique_truth_df['index_test'])]
        entries_to_keep.loc[unique_truth_df.index.union(new_duplicated_truth_df.index)] = True
        curr_cross_merge = curr_cross_merge.loc[unique_truth_df.index.union(new_duplicated_truth_df.index)]
        if len(new_duplicated_truth_df) == len(duplicated_truth_df):
            break
    cross_merge = cross_merge[entries_to_keep]
    # Remove test entries duplicates keeping the one with the least window_fields_sum_diff
    selected_entries = pd.Series(False, index=cross_merge.index)
    # Those test entries that are matched to an already matched truth entry are marked as duplicates
    possible_duplications = dict()
    already_selected_test_entries = set()
    already_selected_truth_entries = set()
    for idx, row in cross_merge.iterrows():
        if row['index_test'] in already_selected_test_entries:
            continue
        if row['index_truth'] in already_selected_truth_entries:
            possible_duplications.setdefault(row['index_test'], []).append(idx)
            continue
        already_selected_test_entries.add(row['index_test'])
        already_selected_truth_entries.add(row['index_truth'])
        selected_entries.loc[idx] = True  # type: ignore
    duplicated_entries = pd.Series(False, index=cross_merge.index)
    for index_test, duplicated_idxs in possible_duplications.items():
        if index_test in already_selected_test_entries:
            continue
        duplicated_entries.loc[duplicated_idxs[0]] = True
    selected_cross_merge = cross_merge[selected_entries]
    duplicated_cross_merge = cross_merge[duplicated_entries]
    df_tp_test = df_test.loc[selected_cross_merge['index_test']]
    df_tp_dup_test = df_test.loc[duplicated_cross_merge['index_test']]
    df_tp_truth = df_truth.loc[selected_cross_merge['index_truth'].unique()]
    df_tp_test['idx_truth'] = df_truth.loc[selected_cross_merge['index_truth']].index
    return df_tp_test, df_tp_dup_test, df_tp_truth


def _matching_window_duplicate_entries(df, matching_fields, window_fields, window_radius):
    # Get matching window entries
    cross_merge = _entries_in_window(df, df, matching_fields, window_fields, window_radius)
    # Avoid returning the same entry
    cross_merge = cross_merge[cross_merge['index_truth'] != cross_merge['index_test']]
    # Calculate window_fields_sum_diff
    cross_merge['window_fields_sum_test'] = cross_merge[[w + '_test' for w in window_fields]].sum(axis=1)
    cross_merge['window_fields_sum_truth'] = cross_merge[[w + '_truth' for w in window_fields]].sum(axis=1)
    cross_merge['window_fields_sum_diff'] = (
        cross_merge['window_fields_sum_test'] - cross_merge['window_fields_sum_truth']).abs()
    # Group by index_truth and get the count of index_test and sum of window_fields_sum_diff
    grouped = cross_merge.groupby('index_truth', sort=False).agg(
        {'index_test': 'count', 'window_fields_sum_diff': 'sum'})
    grouped.rename(columns={'index_test': 'mate_count'}, inplace=True)
    # Sort by mate_count and window_fields_sum_diff
    grouped.sort_values(by=['mate_count', 'window_fields_sum_diff'], ascending=[False, True], inplace=True)
    # The entries with the most mates are the non-duplicated ones
    duplicated_entries = set()
    while len(grouped) > 0:
        mates_to_remove = cross_merge.loc[cross_merge['index_truth'] == grouped.index[0], 'index_test']
        # Remove the selected entry and its mates
        grouped.drop(index=grouped.index[0], inplace=True)
        grouped.drop(index=mates_to_remove, inplace=True, errors='ignore')  # type: ignore
        duplicated_entries.update(mates_to_remove.values)

    # Get the original entries from the selected_truth_entries and the same_entry_mask
    duplicated_entries = df.loc[list(duplicated_entries)]
    original_entries = df.loc[df.index.difference(duplicated_entries.index)]
    return original_entries, duplicated_entries


def intersect_window(df_truth, df_test, matching_fields, window_fields, window_radius):
    # Compute TP
    df_tp, df_tp_dup_test, df_all_truth_tp = _matching_window_entries(
        df_truth, df_test, matching_fields, window_fields, window_radius)
    df_all_test_tp = df_test.loc[df_tp.index.union(df_tp_dup_test.index)]
    # Find FP
    df_all_fp = df_test.loc[~df_test.index.isin(df_all_test_tp.index)]
    # Find duplicates in FP
    df_fp, df_fp_dup = _matching_window_duplicate_entries(
        df_all_fp, matching_fields, window_fields, window_radius)
    # Find FN
    df_all_fn = df_truth.drop(df_all_truth_tp.index)
    # Find duplicates in TP from truth
    df_1, df_2, df_tp_dup_truth = _matching_window_entries(
        df_all_truth_tp, df_all_fn, matching_fields, window_fields, window_radius)
    # Concat truth TP and truth TP duplicates
    df_tp_dup = pd.concat([df_tp_dup_test, df_tp_dup_truth], ignore_index=True)
    # Find duplicates in FN
    df_all_fn = df_all_fn.drop(df_1.index.union(df_2.index))
    df_fn, df_fn_dup = _matching_window_duplicate_entries(
        df_all_fn, matching_fields, window_fields, window_radius)
    return df_tp, df_tp_dup, df_fp, df_fp_dup, df_fn, df_fn_dup
