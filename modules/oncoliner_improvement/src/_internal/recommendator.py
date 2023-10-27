import os
import sys
import glob
import shutil
import multiprocessing
import logging
import pandas as pd

# Add vcf-ops to the path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', '..', '..', 'shared', 'vcf_ops', 'src'))

from vcf_ops.metrics import infer_parameters_from_metrics, aggregate_metrics  # noqa
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
    # Calculate number of processes per caller
    num_processes = [int(max_processes / len(callers_folders))] * len(callers_folders)
    for i in range(max_processes % len(callers_folders)):
        num_processes[i] += 1
    # Check improvements
    process_list = []
    for i, caller_folder in enumerate(callers_folders):
        process = multiprocessing.Process(target=execute_caller_check,
                                          args=(results_output_folder, num_processes[i], baseline_metrics,
                                                caller_folder, user_folder, recall_samples, precision_samples),
                                          kwargs=kwargs, daemon=False)
        process_list.append(process)
        process.start()
        # Avoid too many processes
        if len(process_list) >= max_processes:
            process_list.pop(0).join()
    for process in process_list:
        process.join()
    improvement_list_files = glob.glob(os.path.join(results_output_folder, '*', '*aggregated_metrics.csv'))
    improvement_list = [pd.read_csv(file) for file in improvement_list_files]
    return improvement_list


def group_improvements(improvement_list):
    # Find baseline metrics
    baseline_metrics = [x for x in improvement_list if x['operation'].iloc[0] == 'baseline'][0]
    # Create one dataframe for each of variants
    improvement_groups_dict = dict()
    for idx, row in baseline_metrics.iterrows():
        improvement_group_list = [baseline_metrics.loc[idx]]
        for possible_improvement in improvement_list:
            if possible_improvement.loc[idx]['operation'] == 'baseline':
                continue
            improvement_group_list.append(possible_improvement.loc[idx])
        improvement_group = pd.DataFrame(improvement_group_list)
        improvement_groups_dict[f'{row["variant_type"]} ({row["variant_size"]})'] = improvement_group
    return improvement_groups_dict


def main(evaluation_results, callers_folder, output, recall_samples, precision_samples, loss_margin=0.05, window_radius=None, processes=1):
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

    # callers_names = ['shimmer_', 'delly_1_1_6_']
    # Extract indel threshold, window ratio, window limit and sv_size_bins from metrics (supposing that all the samples have the same metrics)
    dummy_metrics = pd.read_csv(glob.glob(os.path.join(callers_folders[0], 'samples', '*', '*metrics.csv'))[0])
    indel_threshold, window_radius, sv_size_bins = \
        infer_parameters_from_metrics(dummy_metrics, window_radius)

    # Compute improvements
    results_output_folder = os.path.join(output, 'results')
    os.makedirs(results_output_folder, exist_ok=True)
    improvement_list = compute_improvements(callers_folders, evaluation_results, results_output_folder, recall_samples, precision_samples,
                                            processes, loss_margin=loss_margin, indel_threshold=indel_threshold, window_radius=window_radius,
                                            sv_size_bins=sv_size_bins)
    # Create improvement_group
    improvement_groups = group_improvements(improvement_list)
    # print(improvement_groups)
    # Create improvement_list folder
    improvement_list_folder = os.path.join(output, 'improvement_list')
    os.makedirs(improvement_list_folder, exist_ok=True)
    # Save results
    for variant_type, improvement_group in improvement_groups.items():
        improvement_group.to_csv(os.path.join(improvement_list_folder,
                                 f'{cleanup_text(variant_type)}.csv'), index=False)
