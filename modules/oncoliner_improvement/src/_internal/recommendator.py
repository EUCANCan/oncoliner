import os
import sys
import glob
import shutil
import logging
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor

# Add vcf-ops to the path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', '..', '..', 'shared', 'vcf_ops', 'src'))

from vcf_ops.metrics import infer_parameters_from_metrics, aggregate_metrics, filter_metrics_recommendations  # noqa
from .caller_check import execute_caller_check  # noqa
from .common import build_result_dataframe, cleanup_text  # noqa


def compute_baseline(user_folder, samples):
    baseline_metrics_list = []
    for sample in samples:
        metrics_file = glob.glob(os.path.join(user_folder, 'samples', sample, '*metrics.csv'))[0]
        baseline_metrics_list.append(pd.read_csv(metrics_file))
    return aggregate_metrics(baseline_metrics_list)


def compute_improvements(callers_folders, user_folder, results_output_folder, recall_samples, precision_samples, max_processes, **kwargs):
    # Compute baseline metrics
    baseline_precision_metrics = compute_baseline(user_folder, precision_samples)
    baseline_recall_metrics = compute_baseline(user_folder, recall_samples)
    # Add baseline metrics to the improvement list
    baseline_metrics = build_result_dataframe(
        'baseline', baseline_recall_metrics['recall'] > -1, baseline_precision_metrics, baseline_recall_metrics)
    # Save to results output folder
    baseline_output_folder = os.path.join(results_output_folder, 'baseline')
    os.makedirs(baseline_output_folder, exist_ok=True)
    baseline_metrics.to_csv(os.path.join(baseline_output_folder, 'aggregated_metrics.csv'), index=False)
    # Add samples to baseline folder
    os.makedirs(os.path.join(baseline_output_folder, 'samples'), exist_ok=True)
    for sample in recall_samples + precision_samples:
        user_sample_folder = os.path.abspath(os.path.join(user_folder, 'samples', sample))
        baseline_sample_folder = os.path.abspath(os.path.join(baseline_output_folder, 'samples', sample))
        # Remove sample folder if it exists
        shutil.rmtree(baseline_sample_folder, ignore_errors=True)
        shutil.copytree(user_sample_folder, baseline_sample_folder)
    # Check improvements
    pool = ProcessPoolExecutor(max_workers=max_processes)
    futures = []
    for caller_folder in callers_folders:
        future = pool.submit(execute_caller_check, results_output_folder, baseline_metrics,
                             caller_folder, user_folder, recall_samples, precision_samples, **kwargs)
        futures.append(future)
    for future in as_completed(futures):
        future.result()
    pool.shutdown()

def filter_operations(df: pd.DataFrame, loss_margin: float, max_recommendations: int):
    filtered_df = filter_metrics_recommendations(df, loss_margin, max_recommendations, 'added_callers')
    result = set(filtered_df['operation'].unique())
    return result

def group_improvements(results_output_folder: str, max_processes: int, loss_margin: float, max_recommendations: int):
    improvement_list_files = glob.glob(os.path.join(results_output_folder, '*', '*aggregated_metrics.csv'))
    pool = ThreadPoolExecutor(max_workers=max_processes)
    improvement_list = pool.map(pd.read_csv, improvement_list_files)
    improvement_list = list(improvement_list)
    pool.shutdown()
    # Find baseline metrics, if all operations are baseline
    baseline_metrics = [x for x in improvement_list if set(x['operation']) == {'baseline'}][0]
    selected_operations = set()
    # Get all the operations that improve the baseline
    for idx, row in baseline_metrics.iterrows():
        improvement_group_list = [baseline_metrics.loc[idx]]
        for possible_improvement in improvement_list:
            if possible_improvement.loc[idx]['operation'] == 'baseline':
                continue
            improvement_group_list.append(possible_improvement.loc[idx])
        improvement_group = pd.DataFrame(improvement_group_list)
        selected_operations.update(filter_operations(improvement_group, loss_margin, max_recommendations))
    # Create one dataframe for each of variant type and size
    improvement_groups_dict = dict()
    selected_operations.remove('baseline')
    concat_df = pd.concat([x for x in improvement_list if x['operation'].isin(selected_operations).any()])
    del selected_operations
    for idx, row in baseline_metrics.iterrows():
        improvement_group = concat_df[(concat_df['variant_type'] == row['variant_type']) & (concat_df['variant_size'] == row['variant_size'])]
        # Add baseline metrics
        improvement_group = pd.concat([improvement_group, baseline_metrics.loc[idx:idx]])
        # Drop duplicated operations
        improvement_group = improvement_group.drop_duplicates(subset=['operation'])
        improvement_groups_dict[f'{row["variant_type"]} ({row["variant_size"]})'] = improvement_group
    return improvement_groups_dict


def main(evaluation_results, callers_folder, output, recall_samples, precision_samples, loss_margin, gain_margin, max_recommendations, window_radius, processes):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    # Get callers names
    callers_names = os.listdir(callers_folder)
    callers_folders = [os.path.join(callers_folder, caller) for caller in callers_names]

    # Check that all samples in callers_folders are present for each caller
    for sample in recall_samples + precision_samples:
        for caller_folder in callers_folders:
            if not glob.glob(os.path.join(caller_folder, 'samples', sample, '*metrics.csv')):
                raise Exception(f'Sample {sample} not found in {caller_folder}')

    # Create output folder if it does not exist
    os.makedirs(output, exist_ok=True)

    # Extract indel threshold, window ratio, window limit and sv_size_bins from metrics (supposing that all the samples have the same metrics)
    dummy_metrics = pd.read_csv(glob.glob(os.path.join(callers_folders[0], 'samples', '*', '*metrics.csv'))[0])
    indel_threshold, window_radius, sv_size_bins, variant_types = \
        infer_parameters_from_metrics(dummy_metrics, window_radius)

    # Compute improvements
    results_output_folder = os.path.join(output, 'results')
    os.makedirs(results_output_folder, exist_ok=True)
    compute_improvements(callers_folders, evaluation_results, results_output_folder, recall_samples, precision_samples,
                         processes, loss_margin=loss_margin, gain_margin=gain_margin, indel_threshold=indel_threshold,
                         window_radius=window_radius, sv_size_bins=sv_size_bins, variant_types=variant_types)
    # Create improvement_group
    improvement_groups = group_improvements(results_output_folder, processes, loss_margin, max_recommendations)
    # Create improvement_list folder
    improvement_list_folder = os.path.join(output, 'improvement_list')
    os.makedirs(improvement_list_folder, exist_ok=True)
    # Save results
    for variant_type, improvement_group in improvement_groups.items():
        improvement_group.to_csv(os.path.join(improvement_list_folder,
                                 f'{cleanup_text(variant_type)}.csv'), index=False)
