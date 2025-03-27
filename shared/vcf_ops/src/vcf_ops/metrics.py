import pandas as pd
from functools import reduce

from variant_extractor.variants import VariantType

from .genes import combine_genes_symbols, get_cancer_census_genes, GENE_SPLIT_SYMBOL

METRICS_COLUMNS = ['variant_type', 'variant_size', 'window_radius', 'recall', 'precision', 'f1_score', 'tp', 'fp', 'fn',
                   'protein_affected_genes_count', 'protein_affected_driver_genes_count', 'protein_affected_genes', 'protein_affected_driver_genes']


def infer_parameters_from_metrics(metrics: pd.DataFrame, window_radius=None):
    # Infer indel threshold
    indel_threshold = int(metrics[metrics['variant_type'] == 'INDEL']['variant_size'].iloc[0].split('-')[-1])
    # Infer window ratio from INV
    if window_radius is None:
        window_radius = metrics[metrics['variant_type'] == 'INV']['window_radius'].iloc[1]
    # Infer sv_size_bins from INV
    sv_size_bins = []
    for _, row in metrics[metrics['variant_type'] == 'INV'].iloc[2:-1].iterrows():
        _, size_2 = row['variant_size'].split('-')
        sv_size_bins.append(int(size_2))
    # Infer variant_types from metrics
    variant_types = []
    for _, row in metrics.iterrows():
        if 'SV' == row['variant_type'] or 'INDEL' == row['variant_type']:
            continue
        elif 'SNV' == row['variant_type']:
            variant_types.append(row['variant_type'])
            continue
        elif 'INV' == row['variant_type'] or 'TRA' == row['variant_type']:
            general_type = 'SV'
        elif len(row['variant_size'].split('-')) > 1 and int(row['variant_size'].split('-')[1].strip()) == indel_threshold:
            general_type = 'INDEL'
        else:
            general_type = 'SV'

        if len(row['variant_type'].split('/')) > 1:
            for specific_type in row['variant_type'].split('/'):
                variant_types.append(f'{general_type}-{specific_type.strip()}')
        else:
            variant_types.append(f'{general_type}-{row["variant_type"]}')
    # Remove duplicates but keep the order
    variant_types = list(dict.fromkeys(variant_types))
    return indel_threshold, window_radius, sv_size_bins, variant_types


def aggregate_metrics(metrics_list):
    concat_metrics = pd.concat(metrics_list, ignore_index=True)
    # Aggregate metrics
    # Convert to set (if not NaN)
    # Coding genes are splitted by GENE_SPLIT_SYMBOL, create a set of all coding genes and then join them again
    concat_metrics['protein_affected_genes_sets'] = concat_metrics['protein_affected_genes'].apply(
        lambda x: set(x.split(GENE_SPLIT_SYMBOL) if not pd.isna(x) else []))
    agg_metrics = concat_metrics.groupby(['variant_type', 'variant_size', 'window_radius'], sort=False).agg(
        tp=pd.NamedAgg(column='tp', aggfunc='sum'),
        fp=pd.NamedAgg(column='fp', aggfunc='sum'),
        fn=pd.NamedAgg(column='fn', aggfunc='sum'),
        protein_affected_genes=pd.NamedAgg(column='protein_affected_genes_sets', aggfunc=combine_genes_symbols),
    ).reset_index()
    agg_metrics['recall'] = agg_metrics['tp'] / (agg_metrics['tp'] + agg_metrics['fn'])
    agg_metrics['precision'] = agg_metrics['tp'] / (agg_metrics['tp'] + agg_metrics['fp'])
    agg_metrics['f1_score'] = 2 * agg_metrics['precision'] * \
        agg_metrics['recall'] / (agg_metrics['precision'] + agg_metrics['recall'])
    # Fill NaNs with 0
    agg_metrics['recall'] = agg_metrics['recall'].fillna(0)
    agg_metrics['precision'] = agg_metrics['precision'].fillna(0)
    agg_metrics['f1_score'] = agg_metrics['f1_score'].fillna(0)
    agg_metrics['protein_affected_genes_count'] = agg_metrics['protein_affected_genes'].apply(len)
    # Add protein_affected_driver_genes
    agg_metrics['protein_affected_driver_genes'] = agg_metrics['protein_affected_genes'].apply(lambda x: x.intersection(get_cancer_census_genes()))
    agg_metrics['protein_affected_driver_genes_count'] = agg_metrics['protein_affected_driver_genes'].apply(len)
    # Convert to string
    agg_metrics['protein_affected_genes'] = agg_metrics['protein_affected_genes'].apply(GENE_SPLIT_SYMBOL.join)
    agg_metrics['protein_affected_driver_genes'] = agg_metrics['protein_affected_driver_genes'].apply(GENE_SPLIT_SYMBOL.join)
    # Reorder columns
    agg_metrics = agg_metrics[METRICS_COLUMNS]
    return agg_metrics

def filter_metrics_recommendations(df: pd.DataFrame, loss_margin: float, max_recommendations: int, num_callers_column='num_callers', ranking_columns=['f1_score', 'recall', 'precision'], priority_columns=['f1_score', 'recall', 'precision']):
    if len(df) == 0:
        return df
    selected_dfs = []
    for i, ranking_column in enumerate(ranking_columns):
        sort_columns = [ranking_column] + priority_columns
        # Filter all rows with the max element for each column - loss_margin
        df_temp = df
        for column in sort_columns:
            df_temp = df_temp[df_temp[column] >= df_temp[column].max() - loss_margin]
        # Get the minimum number of callers within the loss margin
        min_num_callers = df_temp[num_callers_column].min()
        # Start filtering
        for i in range(min_num_callers, -1, -1):
            df_filtered = df[df[num_callers_column] == i]
            for column in sort_columns:
                df_filtered = df_filtered[df_filtered[column] >= df_filtered[column].max() - loss_margin]
            # Get the top max_recommendations rows
            if max_recommendations > 0 and len(df_filtered) > max_recommendations:
                # Sort by the ranking column
                df_filtered = df_filtered.sort_values(by=sort_columns, ascending=False)
                df_filtered = df_filtered.head(max_recommendations)
            selected_dfs.append(df_filtered)

    return pd.concat(selected_dfs, ignore_index=True)


def combine_precision_recall_metrics(recall_df, precision_df):
    df = pd.DataFrame()
    df[precision_df.columns] = precision_df[precision_df.columns]
    df['recall'] = recall_df['recall']
    df['tp'] = recall_df['tp']
    df['fn'] = recall_df['fn']
    df['precision'] = precision_df['precision']
    df['fp'] = precision_df['fp']
    # Calculate F1 score
    df['f1_score'] = 2 * df['precision'] * df['recall'] / (df['precision'] + df['recall'])
    # Fill NaNs in f1_score with 0
    df['f1_score'] = df['f1_score'].fillna(0)
    df['protein_affected_genes_count'] = recall_df['protein_affected_genes_count']
    df['protein_affected_driver_genes_count'] = recall_df['protein_affected_driver_genes_count']
    df['protein_affected_genes'] = recall_df['protein_affected_genes']
    df['protein_affected_driver_genes'] = recall_df['protein_affected_driver_genes']
    return df


def compute_metrics(df_tp, df_fp, df_fn, indel_threshold, window_radius, sv_size_bins, variant_types):
    # Add temporal benchmark column
    df_tp = df_tp.assign(benchmark='TP')
    df_fp = df_fp.assign(benchmark='FP')
    df_fn = df_fn.assign(benchmark='FN')

    df = pd.concat([df_tp, df_fp, df_fn], ignore_index=True)

    # Setup repeated bin sizes
    repeated_bin_sizes = []
    for i in range(len(sv_size_bins) + 1):
        if i == 0:
            size_text = f'{indel_threshold+1} - {sv_size_bins[i]}'
        elif i == len(sv_size_bins):
            size_text = f'> {sv_size_bins[i-1]}'
        else:
            size_text = f'{sv_size_bins[i-1]+1} - {sv_size_bins[i]}'
        repeated_bin_sizes.append(size_text)
    # Setup bin names
    bin_names = []
    bin_sizes_names = []
    # Setup bin sizes names
    for variant_type in variant_types:
        variant_type_split = variant_type.split('-')
        if len(variant_type_split) == 1:
            general_variant_type = variant_type_split[0]
            specific_variant_type = variant_type_split[0]
        elif len(variant_type_split) == 2:
            general_variant_type, specific_variant_type = variant_type_split
        else:
            raise ValueError(f'Invalid variant type: {variant_type}')
        if general_variant_type == VariantType.SNV.name:
            bin_names.append(VariantType.SNV.name)
            bin_sizes_names.append('1')
        elif general_variant_type == 'INDEL':
            if 'INDEL' not in bin_names:
                bin_names.append('INDEL')
                bin_sizes_names.append(f'1 - {indel_threshold}')
            # Put INDEL INS and DUP in the same bin
            if specific_variant_type == VariantType.INS.name or specific_variant_type == VariantType.DUP.name:
                specific_variant_type = 'INS/DUP'
            if specific_variant_type in bin_names:
                continue
            bin_names.append(specific_variant_type)
            bin_sizes_names.append(f'1 - {indel_threshold}')
        elif general_variant_type == 'SV':
            if 'SV' not in bin_names:
                bin_names.append('SV')
                bin_sizes_names.append('ALL')
            if specific_variant_type == VariantType.TRA.name:
                bin_names.append(VariantType.TRA.name)
                bin_sizes_names.append(VariantType.TRA.name)
            elif specific_variant_type == VariantType.INV.name:
                bin_names.extend([VariantType.INV.name] * (len(sv_size_bins) + 3))
                bin_sizes_names.extend(['> 0', f'1 - {indel_threshold}'] + repeated_bin_sizes)
            else:
                bin_names.extend([specific_variant_type] * (len(sv_size_bins) + 2))
                bin_sizes_names.extend([f'> {indel_threshold}'] + repeated_bin_sizes)

    # Setup window sizes names
    window_radius_names = []
    for i, bin_sizes_name in enumerate(bin_sizes_names):
        if bin_names[i] == 'SNV' or bin_names[i] == 'INDEL':
            window_radius_names.append('0')
        elif bin_sizes_name.split('-')[0].strip() == '1' and ('INS' in bin_names[i] or 'DEL' in bin_names[i]):
            window_radius_names.append('0')
        else:
            window_radius_names.append(str(window_radius))

    # Setup masks
    masks = []
    for i, bin_sizes_name in enumerate(bin_sizes_names):
        if bin_names[i] == 'INDEL' or bin_names[i] == 'SV':
            masks.append(None)  # Skip indels and SVs, fill in later
            continue
        curr_names = bin_names[i].split('/')
        curr_mask = df['type_inferred'] == curr_names[0].strip()
        for name in curr_names[1:]:
            curr_mask = curr_mask | (df['type_inferred'] == name.strip())

        curr_sizes = bin_sizes_name.split('-')
        if '>' in curr_sizes[0]:
            curr_mask = curr_mask & (df['length'] > int(curr_sizes[0].replace('>', '').strip()))
        elif len(curr_sizes) == 2:
            curr_mask = curr_mask & (df['length'] >= int(curr_sizes[0].strip())) & \
                (df['length'] <= int(curr_sizes[1].strip()))
        masks.append(curr_mask)
    # Fill INDEL mask with the existing masks
    masks[1] = masks[2] | masks[3]
    # Fill SV mask with the existing masks
    masks[4] = reduce(lambda x, y: x | y, masks[6:], masks[5])

    rows = []
    for i, bin_name in enumerate(bin_names):
        df_bin = df[masks[i]]
        row = []
        row.append(bin_name)
        row.append(bin_sizes_names[i])
        row.append(window_radius_names[i])
        tp_df = df_bin[df_bin['benchmark'] == 'TP']
        fp_df = df_bin[df_bin['benchmark'] == 'FP']
        fn_df = df_bin[df_bin['benchmark'] == 'FN']
        tp = len(tp_df)
        fp = len(fp_df)
        fn = len(fn_df)
        recall = tp / (tp + fn) if tp + fn > 0 else 0
        precision = tp / (tp + fp) if tp + fp > 0 else 0
        f1 = 2 * recall * precision / (recall + precision) if recall + precision > 0 else 0
        row.append(recall)
        row.append(precision)
        row.append(f1)
        row.append(tp)
        row.append(fp)
        row.append(fn)
        protein_affected_genes = set()
        protein_affected_driver_genes = set()
        # Check if there are any genes in the GENES column
        if 'GENES' in tp_df.columns and tp_df['GENES'].apply(len).sum() > 0:
            protein_affected_genes = combine_genes_symbols(tp_df['GENES'])
            protein_affected_driver_genes = protein_affected_genes & get_cancer_census_genes()
        row.append(len(protein_affected_genes))
        row.append(len(protein_affected_driver_genes))
        row.append(GENE_SPLIT_SYMBOL.join(protein_affected_genes))
        row.append(GENE_SPLIT_SYMBOL.join(protein_affected_driver_genes))
        rows.append(row)

    return pd.DataFrame(rows, columns=METRICS_COLUMNS)

