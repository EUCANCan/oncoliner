from typing import List
import os
import subprocess
import sys
import argparse
import glob
import shutil
import re
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor

# Add vcf-ops to the path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', '..', 'shared', 'vcf_ops', 'src'))

from vcf_ops.constants import DEFAULT_INDEL_THRESHOLD, DEFAULT_WINDOW_RADIUS, DEFAULT_SV_BINS, DEFAULT_CONTIGS  # noqa
from vcf_ops.metrics import aggregate_metrics, combine_precision_recall_metrics  # noqa
from vcf_ops.intersect import intersect  # noqa
from vcf_ops.union import union  # noqa
from vcf_ops.i_o import read_vcfs, write_masked_vcfs  # noqa
from combinator import ADDITION_SYMBOL, INTERSECTION_SYMBOL, generate_combinations, split_operation  # noqa

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


def evaluate_sample(truth_sample_folder, test_sample_folder, output_prefix, fasta_ref, indel_threshold, window_radius, sv_size_bins, contigs):
    # If output_prefix*metrics.csv exists and is not empty, skip
    output_metrics = glob.glob(output_prefix + '*metrics.csv')
    if len(output_metrics) > 0 and os.path.getsize(output_metrics[0]) > 0:
        return
    # Get evaluator path from the environment
    assesment_command = os.environ.get('ASSESMENT_COMMAND')
    if assesment_command is None:
        raise Exception('ASSESMENT_COMMAND environment variable not defined')
    # Get files
    truth_sample_vcfs = get_vcf_files(truth_sample_folder + '/')
    test_sample_vcfs = get_vcf_files(test_sample_folder + '/')
    subprocess.check_call(
        assesment_command.split() + [
            '-t'] + truth_sample_vcfs + [
            '-v'] + test_sample_vcfs + [
            '-o', output_prefix,
            '-f', fasta_ref,
            '-it', str(indel_threshold),
            '-wr', str(window_radius),
            '--sv-size-bins'] + [str(bin) for bin in sv_size_bins] + [
            '--contigs'] + contigs
    )


def evaluate_caller(caller_folder, truth_folder, output_folder, processes, **kwargs):
    pool = ThreadPoolExecutor(max_workers=processes)
    caller_folder_name = os.path.basename(caller_folder)
    futures = []
    for sample in os.listdir(truth_folder):
        truth_sample_folder = os.path.join(truth_folder, sample)
        test_sample_folder = os.path.join(caller_folder, sample)
        output_prefix = os.path.join(output_folder, caller_folder_name, sample, caller_folder_name)
        os.makedirs(os.path.dirname(output_prefix), exist_ok=True)
        futures.append(pool.submit(evaluate_sample, truth_sample_folder, test_sample_folder, output_prefix, **kwargs))
    for future in as_completed(futures):
        future.result()
    pool.shutdown(wait=True)


def evaluate_callers(callers_folders, truth_folder, output_folder, processes, **kwargs):
    pool = ProcessPoolExecutor(max_workers=processes)
    threads_per_caller = max(1, processes // len(callers_folders))
    futures = []
    for caller_folder in callers_folders:
        futures.append(pool.submit(evaluate_caller, caller_folder, truth_folder,
                       output_folder, threads_per_caller, **kwargs))
    for future in as_completed(futures):
        future.result()
    pool.shutdown(wait=True)


def get_caller_variant_type(caller_folder):
    # Get the variant type looking at the aggregated metrics from the caller in the output folder
    metrics_files_list = glob.glob(os.path.join(caller_folder, '*', '*metrics.csv'))
    metrics_list = [pd.read_csv(metrics_file) for metrics_file in metrics_files_list]
    agg_metrics = aggregate_metrics(metrics_list)
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
    df_tp, _, _, _, _, _ = intersect(df_1, df_2, indel_threshold, window_radius)
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


def op_callers_with_samples(caller_1_folder: str, caller_2_folder: str, operation, output_folder: str, **kwargs):
    os.makedirs(output_folder, exist_ok=True)
    for sample in os.listdir(caller_1_folder):
        caller_1_prefix = os.path.join(caller_1_folder, sample + '/')
        caller_2_prefix = os.path.join(caller_2_folder, sample + '/')
        output_prefix = os.path.join(output_folder, sample, os.path.basename(output_folder))
        # If the output folder already exists and is not empty, skip
        output_files = get_vcf_files(output_prefix)
        if len(output_files) > 0 and all([os.path.getsize(output_file) > 0 for output_file in output_files]):
            print(f'Output folder {output_prefix} already exists and is not empty, skipping sample: {sample}')
            continue
        os.makedirs(os.path.dirname(output_prefix), exist_ok=True)
        written_data = operation(caller_1_prefix, caller_2_prefix, output_prefix, **kwargs)
        if not written_data:
            print(f'{output_folder}: no data written for sample: {sample}')
            shutil.rmtree(output_folder)
            break


def execute_operations(operations: List[str], folder: str, processes: int, **kwargs):
    operations_to_execute = []
    for operation in operations:
        # Split the operation into the elements and the operation symbol
        element_1, operation_symbol, element_2 = split_operation(operation)
        operations_to_execute.append((element_1, operation_symbol, element_2, operation))
    pool = ProcessPoolExecutor(max_workers=processes)
    # Execute operations in batches of number of parentheses
    max_parentheses = max([operation[-1].count('(') for operation in operations_to_execute])
    operations_batches = [[] for _ in range(max_parentheses + 1)]
    for operation in operations_to_execute:
        operations_batches[operation[-1].count('(')].append(operation)
    futures = []

    for operation_batch in operations_batches:
        for operation in operation_batch:
            element_1, operation_symbol, element_2, operation_str = operation
            # Get folders of the elements
            element_1_folder = os.path.join(folder, element_1) if element_1.count('(') == 0 else os.path.join(folder, element_1[1:-1])
            element_2_folder = os.path.join(folder, element_2) if element_2.count('(') == 0 else os.path.join(folder, element_2[1:-1])
            # If any folder does not exist, skip
            if not os.path.exists(element_1_folder):
                print(f'Folder {element_1_folder} does not exist, skipping operation: {operation_str}')
                continue
            if not os.path.exists(element_2_folder):
                print(f'Folder {element_2_folder} does not exist, skipping operation: {operation_str}')
                continue
            output_folder = os.path.join(folder, operation_str[1:-1])
            # Perform the operation
            operation = union_callers if operation_symbol == ADDITION_SYMBOL else intersect_callers
            futures.append(pool.submit(op_callers_with_samples, element_1_folder,
                           element_2_folder, operation, output_folder, **kwargs))
        # Wait for the operations to finish
        for future in as_completed(futures):
            future.result()
    pool.shutdown(wait=True)


def calculate_aggregated_metrics_caller(caller_folder: str, recall_samples: List[str], precision_samples: List[str]):
    output_file = os.path.join(caller_folder, 'aggregated_metrics.csv')
    # If the output file already exists and is not empty, skip
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        print(f'Agregated metrics file {output_file} already exists and is not empty, skipping')
        return
    recall_metrics_files = [glob.glob(os.path.join(caller_folder, sample, '*metrics.csv'))[0] for sample in recall_samples]
    recall_aggregated_metrics = aggregate_metrics([pd.read_csv(metrics_file) for metrics_file in recall_metrics_files])
    precision_metrics_files = [glob.glob(os.path.join(caller_folder, sample, '*metrics.csv'))[0] for sample in precision_samples]
    precision_aggregated_metrics = aggregate_metrics([pd.read_csv(metrics_file) for metrics_file in precision_metrics_files])
    final_metrics = combine_precision_recall_metrics(recall_aggregated_metrics, precision_aggregated_metrics)
    final_metrics.to_csv(output_file, index=False)


def calculate_aggregated_metrics(callers_folders: List[str], recall_samples: List[str], precision_samples: List[str], processes: int):
    pool = ProcessPoolExecutor(max_workers=processes)
    futures = []
    for caller_folder in callers_folders:
        futures.append(pool.submit(calculate_aggregated_metrics_caller, caller_folder, recall_samples, precision_samples))
    for future in as_completed(futures):
        future.result()
    pool.shutdown(wait=True)


def create_improvement_list(evaluation_callers_folders: List[str], output_folder: str, processes: int):
    # Read all aggregated metrics files in each thread
    def read_aggregated_metrics(caller_folder):
        df = pd.read_csv(os.path.join(caller_folder, 'aggregated_metrics.csv'))
        # Add a column with the operation name at the start of the dataframe
        operation = os.path.basename(caller_folder)
        df.insert(0, 'operation', operation)
        num_callers = operation.count(ADDITION_SYMBOL) + operation.count(INTERSECTION_SYMBOL)
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


def main(args):
    # Convert to absolute paths
    args.truth = os.path.abspath(args.truth)
    args.test = os.path.abspath(args.test)

    # Get callers names
    callers_names = os.listdir(args.test)
    callers_names.sort()

    # All test folders (callers) must contain the same subfolders (samples)
    for caller_folder in callers_names:
        missing_truth_samples = set(os.listdir(args.truth)) - set(os.listdir(os.path.join(args.test, caller_folder)))
        missing_test_samples = set(os.listdir(os.path.join(args.test, caller_folder))) - set(os.listdir(args.truth))
        if len(missing_truth_samples) > 0:
            raise Exception(f'Caller {caller_folder} is missing samples from the truth folder: {missing_truth_samples}')
        if len(missing_test_samples) > 0:
            raise Exception(f'Caller {caller_folder} has more samples than the truth folder: {missing_test_samples}')

    # Create output folder
    os.makedirs(args.output, exist_ok=True)
    # Create output folder for evaluations
    output_evaluations = os.path.join(args.output, 'evaluations')
    os.makedirs(output_evaluations, exist_ok=True)
    # Create output folder for combinations
    output_combinations = os.path.join(args.output, 'combinations')
    os.makedirs(output_combinations, exist_ok=True)
    # Evaluate the callers
    original_caller_folders = [os.path.join(args.test, caller_name) for caller_name in callers_names]
    evaluate_callers(original_caller_folders, args.truth, output_evaluations, args.processes, fasta_ref=args.fasta_ref,
                     indel_threshold=args.indel_threshold, window_radius=args.window_radius,
                     sv_size_bins=args.sv_size_bins, contigs=args.contigs)

    # Copy each variant caller TP+FP files to its corresponding output_combinations folder
    for caller_name in callers_names:
        caller_combination_folder = os.path.join(output_combinations, caller_name)
        os.makedirs(caller_combination_folder, exist_ok=True)
        for sample in os.listdir(os.path.join(args.test, caller_name)):
            caller_combination_sample_folder = os.path.join(caller_combination_folder, sample)
            os.makedirs(caller_combination_sample_folder, exist_ok=True)
            for file in get_vcf_files(os.path.join(output_evaluations, caller_name, sample, '')):
                # Filter TP+FP files
                if 'tp.' not in file and 'fp.' not in file:
                    continue
                shutil.copy(file, caller_combination_sample_folder)
    # Get callers prefixes
    callers_folders = [os.path.join(output_combinations, caller_name) for caller_name in os.listdir(output_combinations)]
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
    # Define all the possible the operations (intersections and/or unions) to perform between callers of the same variant type
    callers_operations_by_variant_type = {}
    for variant_type, callers in callers_variant_types.items():
        callers_operations_by_variant_type[variant_type] = generate_combinations(callers, args.max_combinations)
    # Perform the operations
    for operations in callers_operations_by_variant_type.values():
        if len(operations) == 0:
            continue
        execute_operations(operations, output_combinations, args.processes, fasta_ref=args.fasta_ref,
                           indel_threshold=args.indel_threshold, window_radius=args.window_radius)
    # Evaluate the combinations
    combinations_prefixes = list(set(os.listdir(output_combinations)) - set(callers_folders))
    combinations_folders = [os.path.join(output_combinations, combination_prefix) for combination_prefix in combinations_prefixes]
    evaluate_callers(combinations_folders, args.truth, output_evaluations, args.processes, fasta_ref=args.fasta_ref,
                     indel_threshold=args.indel_threshold, window_radius=args.window_radius,
                     sv_size_bins=args.sv_size_bins, contigs=args.contigs)

    # Calculate aggregated metrics
    evaluation_callers_folders = [os.path.join(output_evaluations, name) for name in os.listdir(output_combinations)]
    calculate_aggregated_metrics(evaluation_callers_folders, args.recall_samples, args.precision_samples, args.processes)
    # Create a list of all the aggregated metrics files
    output_list_folder = os.path.join(args.output, 'improvement_list')
    os.makedirs(output_list_folder, exist_ok=True)
    create_improvement_list(evaluation_callers_folders, output_list_folder, args.processes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pipeline designer')
    parser.add_argument('-t', '--truth', help='Path to the VCF truth folder', required=True, type=str)
    parser.add_argument('-v', '--test', help='Path to the VCF test folder', required=True, type=str)
    parser.add_argument('-o', '--output', help='Path to the output folder', required=True, type=str)
    parser.add_argument('-f', '--fasta-ref', help='Path to reference FASTA file', required=True, type=str)
    parser.add_argument('-rs', '--recall-samples', type=str, required=True, nargs='+', help='Recall samples names')
    parser.add_argument('-ps', '--precision-samples', type=str, required=True,
                        nargs='+', help='Precision samples names')
    parser.add_argument('-it', '--indel-threshold',
                        help=f'Indel threshold, inclusive (default={DEFAULT_INDEL_THRESHOLD})', default=DEFAULT_INDEL_THRESHOLD, type=int)
    parser.add_argument('-wr', '--window-radius',
                        help=f'Window ratio (default={DEFAULT_WINDOW_RADIUS})', default=DEFAULT_WINDOW_RADIUS, type=int)
    parser.add_argument(
        '--sv-size-bins', help=f'SV size bins for the output_prefix metrics (default={DEFAULT_SV_BINS})', nargs='+', default=DEFAULT_SV_BINS, type=int)
    parser.add_argument(
        '--contigs', help=f'Contigs to process (default={DEFAULT_CONTIGS})', nargs='+', default=DEFAULT_CONTIGS, type=str)
    parser.add_argument('-p', '--processes', type=int, default=1, help='Number of processes to use')
    parser.add_argument('--max-combinations', type=int, default=-1,
                        help='Maximum number of combinations to perform (-1) for all')

    args = parser.parse_args()

    main(args)
