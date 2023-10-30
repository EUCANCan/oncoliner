import os
import sys
import glob
import itertools
import pandas as pd
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

# Add vcf-ops to the path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', '..', '..', 'shared', 'vcf_ops', 'src'))

from vcf_ops.union import union  # noqa
from vcf_ops.i_o import read_vcfs  # noqa
from vcf_ops.metrics import infer_parameters_from_metrics  # noqa
from vcf_ops.masks import indel_mask, snv_mask  # noqa
from .utils import cleanup_text  # noqa


def _mask_by_type_and_size(df, variant_type, variant_size_str, indel_threshold):
    # Mask based on variant type
    if variant_type == 'INDEL':
        return df[indel_mask(df, indel_threshold)]
    elif variant_type == 'SV':
        return df[~indel_mask(df, indel_threshold) & ~snv_mask(df)]
    elif '/' in variant_type:
        variant_type_1, variant_type_2 = variant_type.split('/')
        mask = (df['type_inferred'] == variant_type_1) | (df['type_inferred'] == variant_type_2)
    else:
        mask = df['type_inferred'] == variant_type
    # Mask based on variant size
    if '>' in variant_size_str:
        variant_size = int(variant_size_str.replace('>', '').strip())
        mask &= df['length'] > variant_size
    elif '-' in variant_size_str:
        variant_size_1, variant_size_2 = variant_size_str.split('-')
        variant_size_1 = int(variant_size_1.strip())
        variant_size_2 = int(variant_size_2.strip())
        mask &= (df['length'] >= variant_size_1) & (df['length'] <= variant_size_2)
    return df[mask]


def _compute_overlapping_metrics(total_variants, overlapping_variants, evaluation_metrics_example, indel_threshold):
    metrics_rows = []
    columns = ['variant_type', 'variant_size', 'total_variants', 'overlapping_variants',
               'overlapping_variants_ratio', 'total_genes', 'overlapping_genes', 'overlapping_genes_ratio']
    # Iterate over each row in the evaluation metrics example
    for _, row in evaluation_metrics_example.iterrows():
        variant_type = row['variant_type']
        variant_size = row['variant_size']
        total_variants_masked = _mask_by_type_and_size(total_variants, variant_type, variant_size, indel_threshold)
        overlapping_variants_masked = _mask_by_type_and_size(
            overlapping_variants, variant_type, variant_size, indel_threshold)
        # Compute metrics
        total_variants_count = len(total_variants_masked)
        overlapping_variants_count = len(overlapping_variants_masked)
        overlapping_variants_ratio = overlapping_variants_count / total_variants_count if total_variants_count > 0 else 0
        total_genes = 0
        overlapping_genes = 0
        overlapping_genes_ratio = overlapping_genes / total_genes if total_genes > 0 else 0
        metrics_rows.append([variant_type, variant_size, total_variants_count, overlapping_variants_count,
                             overlapping_variants_ratio, total_genes, overlapping_genes, overlapping_genes_ratio])
    return pd.DataFrame(metrics_rows, columns=columns)


def _aggregate_overlapping_metrics(overlapping_metrics_list):
    overlapping_metrics = pd.concat(overlapping_metrics_list, ignore_index=True)
    overlapping_metrics = overlapping_metrics.groupby(['variant_type', 'variant_size'], sort=False).sum().reset_index()
    overlapping_metrics['overlapping_variants_ratio'] = overlapping_metrics['overlapping_variants'] / \
        overlapping_metrics['total_variants']
    overlapping_metrics['overlapping_genes_ratio'] = overlapping_metrics['overlapping_genes'] / \
        overlapping_metrics['total_genes']
    # Fill NaNs with 0
    overlapping_metrics['overlapping_variants_ratio'].fillna(0, inplace=True)
    overlapping_metrics['overlapping_genes_ratio'].fillna(0, inplace=True)
    return overlapping_metrics


def _compute_sample_overlap(pipeline_1_sample_folder, pipeline_2_sample_folder, indel_threshold, window_radius):
    # Read VCFs
    pipeline_1_vcfs_paths = glob.glob(os.path.join(pipeline_1_sample_folder, '*tp.*')) + \
        glob.glob(os.path.join(pipeline_1_sample_folder, '*fp.*'))
    pipeline_2_vcfs_paths = glob.glob(os.path.join(pipeline_2_sample_folder, '*tp.*')) + \
        glob.glob(os.path.join(pipeline_2_sample_folder, '*fp.*'))
    pipeline_1_vcfs = read_vcfs(pipeline_1_vcfs_paths)
    pipeline_2_vcfs = read_vcfs(pipeline_2_vcfs_paths)
    # Create a fake truth set
    fake_truth = pd.DataFrame(columns=pipeline_1_vcfs.columns)
    df = pd.concat([pipeline_1_vcfs, pipeline_2_vcfs], ignore_index=True)
    # Compute overlap
    total_variants, overlapping_variants = union(fake_truth, df, indel_threshold, window_radius)
    # Metrics
    evaluation_metrics_example = pd.read_csv(glob.glob(os.path.join(pipeline_1_sample_folder, '*metrics.csv'))[0])
    return _compute_overlapping_metrics(total_variants, overlapping_variants, evaluation_metrics_example, indel_threshold)


def _compute_overlap(pipelines_combination_path, sample_names, indel_threshold, window_radius, threads):
    thread_pool = ThreadPoolExecutor(max_workers=threads)
    results = thread_pool.map(lambda x:
                              _compute_sample_overlap(os.path.join(pipelines_combination_path[0], 'samples', x),
                                                      os.path.join(pipelines_combination_path[1], 'samples', x),
                                                      indel_threshold, window_radius), sample_names)
    overlapping_metrics = list(results)
    agg_overlapping_metrics = _aggregate_overlapping_metrics(overlapping_metrics)
    # Mask if they come from the baseline pipeline
    pipeline_1_agg_metrics_path = os.path.join(pipelines_combination_path[0], 'aggregated_metrics.csv')
    pipeline_2_agg_metrics_path = os.path.join(pipelines_combination_path[1], 'aggregated_metrics.csv')
    pipeline_1_agg_metrics = pd.read_csv(pipeline_1_agg_metrics_path)
    pipeline_2_agg_metrics = pd.read_csv(pipeline_2_agg_metrics_path)
    pipeline_1_mask = pipeline_1_agg_metrics['operation'] != 'baseline'
    pipeline_2_mask = pipeline_2_agg_metrics['operation'] != 'baseline'
    # If the mask is all false, it means that the pipeline is the baseline pipeline, we keep everything
    if not any(pipeline_1_mask):
        pipeline_1_mask = pd.Series([True] * len(agg_overlapping_metrics))
    if not any(pipeline_2_mask):
        pipeline_2_mask = pd.Series([True] * len(agg_overlapping_metrics))
    agg_overlapping_metrics = agg_overlapping_metrics[pipeline_1_mask & pipeline_2_mask]
    return agg_overlapping_metrics


def _check_pipelines_combinations(pipelines_folders, window_radius=None, processes=1):
    # Each folder contains a set of improvements in the form of subfolders
    # Create a list of the possible improvements for each pipeline
    improvements = dict()
    for folder in pipelines_folders:
        subfolders = [f for f in glob.glob(os.path.join(folder, '*')) if os.path.isdir(f)]
        if len(subfolders) == 0:
            raise ValueError(f'No subfolders found in {folder}')
        improvements[folder] = subfolders
    # Create a list of all possible combinations with an improvement from each pipeline
    improvements_combinations = list(itertools.product(*improvements.values()))
    # Get sample names from the first pipeline
    sample_names = [os.path.basename(f)
                    for f in glob.glob(os.path.join(improvements_combinations[0][0], 'samples', '*'))
                    if os.path.isdir(f)]
    # Get indel_threshold, window_radius from the first pipeline metrics
    metrics = pd.read_csv(glob.glob(os.path.join(improvements_combinations[0][0], 'samples', '*', '*metrics.csv'))[0])
    indel_threshold, window_radius, _, _ = infer_parameters_from_metrics(metrics, window_radius=window_radius)
    # Compute overlap for each combination
    pool = multiprocessing.Pool(processes=processes)
    # Calculate number of processes per combination
    num_processes = [int(processes / len(improvements_combinations))] * len(improvements_combinations)
    for i in range(processes % len(improvements_combinations)):
        num_processes[i] += 1
    num_processes = [max(x, 1) for x in num_processes]
    results = pool.starmap(_compute_overlap, [(x, sample_names, indel_threshold, window_radius,
                           num_processes[i]) for i, x in enumerate(improvements_combinations)])
    overlapping_metrics = list(results)
    combination_names = [[os.path.basename(x) for x in y] for y in improvements_combinations]
    return list(zip(combination_names, overlapping_metrics))


def _group_combinations(improvements_combinations_metrics):
    # Find baseline metrics
    baseline_metrics = next(x for x in improvements_combinations_metrics
                            if all(y == 'baseline' for y in x[0]))[1]
    num_pipelines = len(improvements_combinations_metrics[0][0])
    pipelines_columns = [f'pipeline_{i+1}' for i in range(num_pipelines)]
    # Create one dataframe for each of variants
    combinations_groups_dict = dict()
    for idx, row in baseline_metrics.iterrows():
        # Add baseline row
        baseline_row = baseline_metrics.loc[idx].copy()
        for pipeline in pipelines_columns:
            baseline_row[pipeline] = 'baseline'
        combinations_group_list = [baseline_row]
        for combination_names, combination_metrics in improvements_combinations_metrics:
            # Skip if the combination_metrics don't contain the current variant
            if idx not in combination_metrics.index:
                continue
            baseline_row = baseline_metrics.loc[idx]
            combination_row = combination_metrics.loc[idx]
            # If the combination_metrics are worse or the same as the baseline, skip
            if combination_row['overlapping_variants_ratio'] <= baseline_row['overlapping_variants_ratio'] and \
                    combination_row['overlapping_genes_ratio'] <= baseline_row['overlapping_genes_ratio']:
                continue
            new_row = combination_row.copy()
            for i, name in enumerate(combination_names):
                new_row[pipelines_columns[i]] = name
            combinations_group_list.append(new_row)
        combination_group = pd.DataFrame(combinations_group_list,
                                         columns=pipelines_columns + baseline_metrics.columns.tolist())
        combinations_groups_dict[f'{row["variant_type"]} ({row["variant_size"]})'] = combination_group
    return combinations_groups_dict


def main(input_pipelines_improvements, output, window_radius=None, processes=1):
    # Create output folder
    os.makedirs(output, exist_ok=True)

    # Compute combinations
    improvements_combinations_metrics = _check_pipelines_combinations(input_pipelines_improvements, window_radius, processes)
    combinations_groups_dict = _group_combinations(improvements_combinations_metrics)
    # Save results
    for variant_type, combinations_group in combinations_groups_dict.items():
        combinations_group.to_csv(os.path.join(output, f'{cleanup_text(variant_type)}.csv'), index=False)
