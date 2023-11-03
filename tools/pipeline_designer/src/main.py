from typing import List, Tuple
import os
import subprocess
import sys
import argparse
import glob
import shutil
import re
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
import pandas as pd

# Add vcf-ops to the path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', '..', 'shared', 'vcf_ops', 'src'))

from vcf_ops.constants import DEFAULT_INDEL_THRESHOLD, DEFAULT_WINDOW_RADIUS, DEFAULT_SV_BINS, DEFAULT_CONTIGS, DEFAULT_VARIANT_TYPES  # noqa
from vcf_ops.intersect import intersect  # noqa
from vcf_ops.union import union  # noqa
from vcf_ops.i_o import read_vcfs, write_masked_vcfs  # noqa
from vcf_ops.constants import UNION_SYMBOL, INTERSECTION_SYMBOL  # noqa
from combinator import generate_combinations, split_operation  # noqa


MIN_RECALL = 0.05


def cleanup_text(text: str) -> str:
    # Keep [a-zA-Z0-9_], the rest is replaced by _
    return re.sub(r'[^a-zA-Z0-9_]', '_', text)


def get_vcf_files(path_prefix: str) -> List[str]:
    return glob.glob(path_prefix + '*.vcf.gz') + \
        glob.glob(path_prefix + '*.bcf') + \
        glob.glob(path_prefix + '*.vcf')


def extract_vcfs(path_prefix: str) -> pd.DataFrame:
    files = get_vcf_files(path_prefix)
    return read_vcfs(files)


def check_improvement(combination_evaluation_folder: str, evaluation_element_1_folder: str, evaluation_element_2_folder: str, operation_symbol: str, loss_margin: float) -> bool:
    # Get the aggregated metrics for all the folders
    combination_metrics = pd.read_csv(glob.glob(os.path.join(combination_evaluation_folder, '*aggregated_metrics.csv'))[0])
    element_1_metrics = pd.read_csv(glob.glob(os.path.join(evaluation_element_1_folder, '*aggregated_metrics.csv'))[0])
    element_2_metrics = pd.read_csv(glob.glob(os.path.join(evaluation_element_2_folder, '*aggregated_metrics.csv'))[0])
    # Check depending on the operation
    if operation_symbol == UNION_SYMBOL:
        metric_loss = 'precision'
        metric_improve = 'recall'
    elif operation_symbol == INTERSECTION_SYMBOL:
        metric_loss = 'recall'
        metric_improve = 'precision'
    # Get all the rows where the combination has not lost more than the loss margin
    loss_mask_1 = element_1_metrics[metric_loss] - combination_metrics[metric_loss] <= loss_margin
    loss_mask_2 = element_2_metrics[metric_loss] - combination_metrics[metric_loss] <= loss_margin
    loss_mask = loss_mask_1 | loss_mask_2
    combination_metrics = combination_metrics[loss_mask]
    element_1_metrics = element_1_metrics[loss_mask]
    element_2_metrics = element_2_metrics[loss_mask]
    # Get all the rows where the combination has improved
    improve_mask_1 = combination_metrics[metric_improve] - element_1_metrics[metric_improve] > 0.01
    improve_mask_2 = combination_metrics[metric_improve] - element_2_metrics[metric_improve] > 0.01
    improve_mask = improve_mask_1 | improve_mask_2
    combination_metrics = combination_metrics[improve_mask]
    return combination_metrics


def evaluate_caller(caller_folder, config, output_folder, processes, indel_threshold, window_radius, sv_size_bins, contigs, variant_types, no_gzip=False):
    pipelines_vcf_paths = config['sample_name'].apply(
        lambda sample_name: ','.join([os.path.join(caller_folder, sample_name, '*.vcf.gz'),
                                      os.path.join(caller_folder, sample_name, '*.vcf'),
                                      os.path.join(caller_folder, sample_name, '*.bcf')]))
    # Create a new config file with the paths to the pipeline VCFs
    config_with_pipeline_vcf_paths = config.copy()
    config_with_pipeline_vcf_paths['test_vcf_paths'] = pipelines_vcf_paths
    # Save the new config file
    config_path = os.path.join(output_folder, 'config.tsv')
    config_with_pipeline_vcf_paths.to_csv(config_path, sep='\t', index=False)
    # Execute the assesment
    assesment_command = os.environ['ASSESMENT_COMMAND']
    evaluator_command_split = assesment_command.split()
    args = evaluator_command_split + \
        ['-c', config_path,
         '-p', str(processes),
         '-o', output_folder,
         '-it', str(indel_threshold),
         '-wr', str(window_radius),
         '--sv-size-bins'] + \
        [str(bin) for bin in sv_size_bins] + \
        ['--contigs'] + contigs + \
        ['--variant-types'] + variant_types
    if no_gzip:
        args.append('--no-gzip')
    subprocess.check_call(args, stdout=subprocess.DEVNULL)


def evaluate_callers(callers_folders: List[str], config: pd.DataFrame, output_folder: str, processes: int, **kwargs):
    pool = ProcessPoolExecutor(max_workers=processes)
    threads_per_caller = max(1, processes // len(callers_folders))
    futures = []
    for caller_folder in callers_folders:
        output_caller_folder = os.path.join(output_folder, os.path.basename(caller_folder))
        os.makedirs(output_caller_folder, exist_ok=True)
        futures.append(pool.submit(evaluate_caller, caller_folder, config, output_caller_folder, threads_per_caller, **kwargs))
    for future in as_completed(futures):
        future.result()
    pool.shutdown(wait=True)


def get_caller_variant_type(caller_evaluation_folder: str):
    # Get the variant type looking at the aggregated metrics from the caller in the output folder
    agg_metrics_path = glob.glob(os.path.join(caller_evaluation_folder, '*aggregated_metrics.csv'))
    agg_metrics = pd.read_csv(agg_metrics_path[0])
    # Possible variant types: SNV, INDEL and/or SV
    variant_types = set()
    if agg_metrics[agg_metrics['variant_type'] == 'SNV'].iloc[0]['recall'] > MIN_RECALL:
        variant_types.add('SNV')
    if agg_metrics[agg_metrics['variant_type'] == 'INDEL'].iloc[0]['recall'] > MIN_RECALL:
        variant_types.add('INDEL')
    if agg_metrics[agg_metrics['variant_type'] == 'SV'].iloc[0]['recall'] > MIN_RECALL:
        variant_types.add('SV')
    return variant_types


def intersect_callers(caller_1_prefix, caller_2_prefix, output_prefix, fasta_ref, indel_threshold, window_radius):
    # Read the VCFs
    df_1 = extract_vcfs(caller_1_prefix)
    df_2 = extract_vcfs(caller_2_prefix)
    # Intersect
    df_tp, _, _, _, _, _ = intersect(df_1, df_2, indel_threshold, window_radius, False)
    # Write VCF files
    if len(df_tp) > 0:
        write_masked_vcfs(df_tp, output_prefix, indel_threshold, fasta_ref)
        return True
    return False


def union_callers(caller_1_prefix: str, caller_2_prefix: str, output_prefix: str, fasta_ref, indel_threshold, window_radius):
    # Read the VCFs
    df_1 = extract_vcfs(caller_1_prefix)
    df_2 = extract_vcfs(caller_2_prefix)
    # Union
    df_union, _ = union(df_1, df_2, indel_threshold, window_radius)
    # Write VCF files
    if len(df_union) > len(df_1):
        write_masked_vcfs(df_union, output_prefix, indel_threshold, fasta_ref)
        return True
    return False


def op_callers_with_samples(operation_tuple, combinations_folder: str, evaluations_folder: str, threads: int, config: pd.DataFrame, **kwargs):
    element_1, operation_symbol, element_2, operation_str = operation_tuple
    print(f'Executing combination: {element_1} <{operation_symbol}> {element_2}')
    # Get names of the elements
    element_1_name = element_1 if element_1.count('(') == 0 else element_1[1:-1]
    element_2_name = element_2 if element_2.count('(') == 0 else element_2[1:-1]
    # Get folders of the elements
    combination_element_1_folder = os.path.join(combinations_folder, element_1_name)
    combination_element_2_folder = os.path.join(combinations_folder, element_2_name)
    # If any folder does not exist, skip
    if not os.path.exists(combination_element_1_folder):
        print(f'Folder {combination_element_1_folder} does not exist, skipping operation: {operation_str}')
        return
    if not os.path.exists(combination_element_2_folder):
        print(f'Folder {combination_element_2_folder} does not exist, skipping operation: {operation_str}')
        return
    # Get the name of the operation
    operation_name = operation_str[1:-1]
    combination_output_folder = os.path.join(combinations_folder, operation_name)
    combination_output_flag_file = os.path.join(combinations_folder, operation_name + '.done')
    # Avoid the operation if operation_name.done exists
    if os.path.exists(combination_output_flag_file):
        print(f'Flag file {combination_output_flag_file} exists, skipping')
        return
    # Avoid the operation if already evaluated
    evaluation_output_folder = os.path.join(evaluations_folder, operation_name)
    # Check if the evaluation has already been performed
    if os.path.exists(os.path.join(evaluation_output_folder, 'aggregated_metrics.csv')):
        print(f'Evaluation already performed for {operation_name}, skipping')
        return
    os.makedirs(combination_output_folder, exist_ok=True)
    operation = union_callers if operation_symbol == UNION_SYMBOL else intersect_callers
    sample_names = config['sample_name'].tolist()
    for sample in sample_names:
        fasta_ref = config[config['sample_name'] == sample]['reference_fasta_path'].iloc[0]
        caller_1_prefix = os.path.join(combination_element_1_folder, sample + '/')
        caller_2_prefix = os.path.join(combination_element_2_folder, sample + '/')
        output_prefix = os.path.join(combination_output_folder, sample, operation_name)
        # If the output folder already exists and is not empty, skip
        output_files = get_vcf_files(output_prefix)
        if len(output_files) > 0 and all(os.path.getsize(output_file) > 0 for output_file in output_files):
            print(f'Output folder {output_prefix} already exists and is not empty, skipping sample: {sample}')
            continue
        os.makedirs(os.path.dirname(output_prefix), exist_ok=True)
        written_data = operation(caller_1_prefix, caller_2_prefix, output_prefix, fasta_ref=fasta_ref,
                                 indel_threshold=kwargs['indel_threshold'], window_radius=kwargs['window_radius'])
        if not written_data:
            print(f'{operation_str}: no data written for sample: {sample}. Skipping the rest of the samples.')
            shutil.rmtree(combination_output_folder)
            # Write a file with the operation name to avoid repeating the operation
            with open(combination_output_flag_file, 'w') as f:
                f.write('')
            # If no data was written, skip the rest of the samples
            return
    # Evaluate the result
    os.makedirs(evaluation_output_folder, exist_ok=True)
    evaluate_caller(combination_output_folder, config, evaluation_output_folder, threads, indel_threshold=kwargs['indel_threshold'],
                    window_radius=kwargs['window_radius'], sv_size_bins=kwargs['sv_size_bins'], contigs=kwargs['contigs'], variant_types=kwargs['variant_types'])
    # Check for improvement with the new combination
    evaluation_element_1_folder = os.path.join(evaluations_folder, element_1_name)
    evaluation_element_2_folder = os.path.join(evaluations_folder, element_2_name)
    improved_metrics_df = check_improvement(evaluation_output_folder, evaluation_element_1_folder,
                                            evaluation_element_2_folder, operation_symbol, kwargs['loss_margin'])
    # If there is no improvement, remove the combination folder
    if len(improved_metrics_df) == 0:
        shutil.rmtree(combination_output_folder)
        shutil.rmtree(evaluation_output_folder)
        # Write a file with the operation name to avoid repeating the operation
        with open(combination_output_flag_file, 'w') as f:
            f.write('')


def execute_operations(operations: List[str], combinations_folder: str, evaluations_folder: str, processes: int, config: pd.DataFrame, **kwargs):
    operations_to_execute = []
    for operation_str in operations:
        # Split the operation into the elements and the operation symbol
        element_1, operation_symbol, element_2 = split_operation(operation_str, UNION_SYMBOL, INTERSECTION_SYMBOL)
        operations_to_execute.append((element_1, operation_symbol, element_2, operation_str))
    pool = ProcessPoolExecutor(max_workers=processes)
    # Execute operations in batches of number of parentheses
    max_parentheses = max([operation[-1].count('(') for operation in operations_to_execute])
    operations_batches = [[] for _ in range(max_parentheses)]  # type: ignore
    for operation in operations_to_execute:
        operations_batches[operation[-1].count('(') - 1].append(operation)
    futures = []

    for operation_batch in operations_batches:
        threads_per_operation = max(1, processes // len(operation_batch))
        for operation in operation_batch:
            futures.append(pool.submit(op_callers_with_samples, operation, combinations_folder,
                           evaluations_folder, threads_per_operation, config, **kwargs))
        # Wait for the operations to finish
        for future in as_completed(futures):
            future.result()
    pool.shutdown(wait=True)


def create_improvement_list(evaluation_callers_folders: List[str], output_folder: str, processes: int):
    # Read all aggregated metrics files in each thread
    def read_aggregated_metrics(caller_folder):
        df = pd.read_csv(glob.glob(os.path.join(caller_folder, '*aggregated_metrics.csv'))[0])
        # Add a column with the operation name at the start of the dataframe
        operation = os.path.basename(caller_folder)
        df.insert(0, 'operation', operation)
        num_callers = operation.count(UNION_SYMBOL) + operation.count(INTERSECTION_SYMBOL)
        df['num_callers'] = num_callers + 1
        return df
    pool = ThreadPoolExecutor(max_workers=processes)
    all_dfs = []
    futures = []
    for caller_folder in evaluation_callers_folders:
        futures.append(pool.submit(read_aggregated_metrics, caller_folder))
    for future in as_completed(futures):
        all_dfs.append(future.result())
    pool.shutdown(wait=True)
    # Create a dataframe with all the aggregated metrics for each row of the first aggregated metrics file
    for idx, row in all_dfs[0].iterrows():
        name = cleanup_text(f'{row["variant_type"]}_{row["variant_size"]}')
        output_file = os.path.join(output_folder, name + '.csv')
        improvement_group_list = []
        for df in all_dfs:
            improvement_group_list.append(df.loc[idx])
        improvement_df = pd.DataFrame(improvement_group_list)
        # Filter out the rows without minimum recall
        improvement_df = improvement_df[improvement_df['recall'] >= MIN_RECALL]
        improvement_df.to_csv(output_file, index=False)


def get_recall_precision_samples(config: pd.DataFrame) -> Tuple[List[str], List[str]]:
    sample_type_set = config['sample_types'].map(lambda x: set(x.split(',')))
    recall_samples = config[sample_type_set.apply(lambda x: 'recall' in x)]['sample_name'].tolist()
    precision_samples = config[sample_type_set.apply(lambda x: 'precision' in x)]['sample_name'].tolist()
    return recall_samples, precision_samples


def main(args):
    # Read the config file
    config = pd.read_csv(args.config, sep='\t')

    # Get callers names
    callers_names = os.listdir(args.variant_callers)
    callers_names.sort()

    # Get sample names
    recall_samples, precision_samples = get_recall_precision_samples(config)
    sample_names = sorted(set(recall_samples).union(precision_samples))

    # All test folders (callers) must contain the same subfolders (samples)
    for caller_folder in callers_names:
        for sample in sample_names:
            if not os.path.exists(os.path.join(args.variant_callers, caller_folder, sample)):
                raise Exception(f'Caller {caller_folder} is missing sample {sample} subfolder')

    # Create output folder
    os.makedirs(args.output, exist_ok=True)
    # Create output folder for evaluations
    output_evaluations = os.path.join(args.output, 'evaluations')
    os.makedirs(output_evaluations, exist_ok=True)
    # Create output folder for combinations
    output_combinations = os.path.join(args.output, 'combinations')
    os.makedirs(output_combinations, exist_ok=True)
    # Evaluate the callers
    print('Evaluating callers...')
    original_caller_folders = [os.path.join(args.variant_callers, caller_name) for caller_name in callers_names]
    evaluate_callers(original_caller_folders, config, output_evaluations, args.processes,
                     indel_threshold=args.indel_threshold, window_radius=args.window_radius,
                     sv_size_bins=args.sv_size_bins, contigs=args.contigs, variant_types=args.variant_types, no_gzip=args.no_gzip)

    # Copy each variant caller TP+FP files to its corresponding output_combinations folder
    for caller_name in callers_names:
        caller_combination_folder = os.path.join(output_combinations, caller_name)
        os.makedirs(caller_combination_folder, exist_ok=True)
        for sample in sample_names:
            caller_combination_sample_folder = os.path.join(caller_combination_folder, sample)
            os.makedirs(caller_combination_sample_folder, exist_ok=True)
            for file in get_vcf_files(os.path.join(output_evaluations, caller_name, 'samples', sample, '')):
                # Filter TP+FP files
                if 'tp.' not in file and 'fp.' not in file:
                    continue
                shutil.copy(file, caller_combination_sample_folder)
    # Get the variant types for each caller
    # Create a dict variant_type -> callers
    callers_variant_types = {
        'SNV': [],
        'INDEL': [],
        'SV': []
    }
    for caller_name in callers_names:
        for variant_type in get_caller_variant_type(os.path.join(output_evaluations, caller_name)):
            callers_variant_types[variant_type].append(caller_name)
    print(f'Callers variant types: {callers_variant_types}')
    # Define all the possible the operations (intersections and/or unions) to perform between callers of the same variant type
    print('Generating combinations...')
    callers_operations_by_variant_type = {}
    for variant_type, callers in callers_variant_types.items():
        callers_operations_by_variant_type[variant_type] = generate_combinations(
            callers, args.max_combinations, UNION_SYMBOL, INTERSECTION_SYMBOL)
    # Perform the operations
    for operations in callers_operations_by_variant_type.values():
        print(f'Executing {len(operations)} combinations...')
        if len(operations) == 0:
            continue
        execute_operations(operations, output_combinations, output_evaluations, args.processes, config,
                           indel_threshold=args.indel_threshold, window_radius=args.window_radius, sv_size_bins=args.sv_size_bins,
                           contigs=args.contigs, variant_types=args.variant_types, loss_margin=args.loss_margin)

    # Create improvement list
    print('Creating improvement list...')
    evaluation_callers_folders = glob.glob(os.path.join(output_evaluations, '*'))
    output_list_folder = os.path.join(args.output, 'improvement_list')
    os.makedirs(output_list_folder, exist_ok=True)
    create_improvement_list(evaluation_callers_folders, output_list_folder, args.processes)
    print('Improvement list in folder: ' + output_list_folder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pipeline designer')
    parser.add_argument('-c', '--config', help='Path to the config file', required=True, type=str)
    parser.add_argument('-vc', '--variant-callers', help='Path to the variant callers folder', required=True, type=str)
    parser.add_argument('-o', '--output', help='Path to the output folder', required=True, type=str)
    parser.add_argument('-lm', '--loss-margin', type=float, default=0.05, help='Loss margin for improvement')
    parser.add_argument('-it', '--indel-threshold',
                        help=f'Indel threshold, inclusive (default={DEFAULT_INDEL_THRESHOLD})', default=DEFAULT_INDEL_THRESHOLD, type=int)
    parser.add_argument('-wr', '--window-radius',
                        help=f'Window ratio (default={DEFAULT_WINDOW_RADIUS})', default=DEFAULT_WINDOW_RADIUS, type=int)
    parser.add_argument(
        '--sv-size-bins', help=f'SV size bins for the output_prefix metrics (default={DEFAULT_SV_BINS})', nargs='+', default=DEFAULT_SV_BINS, type=int)
    parser.add_argument('--contigs', nargs='+', default=DEFAULT_CONTIGS, type=str,
                        help=f'Contigs to process (default={DEFAULT_CONTIGS})')
    parser.add_argument('--variant-types', nargs='+', default=DEFAULT_VARIANT_TYPES, type=str,
                        help=f'Variant types to process (default={DEFAULT_VARIANT_TYPES})')
    parser.add_argument('--no-gzip', action='store_true', help='Do not gzip the output VCF files')
    parser.add_argument('-p', '--processes', type=int, default=1, help='Number of processes to use')
    parser.add_argument('--max-combinations', type=int, default=4,
                        help='Maximum number of combinations to perform (-1) for all combinations')
    main(parser.parse_args())
