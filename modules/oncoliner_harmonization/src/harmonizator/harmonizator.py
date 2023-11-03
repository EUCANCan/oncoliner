from typing import List, Dict
import os
import sys
import glob
import itertools
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

# Add vcf-ops to the path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', '..', '..', 'shared', 'vcf_ops', 'src'))

from vcf_ops.union import union  # noqa
from vcf_ops.i_o import read_vcfs  # noqa
from vcf_ops.metrics import infer_parameters_from_metrics  # noqa
from vcf_ops.masks import indel_mask, snv_mask  # noqa
from .utils import cleanup_text  # noqa


def _read_pipeline_improvements(pipeline_folder: str) -> Dict[str, pd.DataFrame]:
    # Read all .csv files in the pipeline folder
    csv_files = glob.glob(os.path.join(pipeline_folder, 'improvement_list', '*.csv'))
    if len(csv_files) == 0:
        raise Exception(f'No improvement files found in {pipeline_folder}')
    pipeline_improvements = map(pd.read_csv, csv_files)
    # Concatenate all the improvements into a single dataframe
    pipeline_improvements = pd.concat(pipeline_improvements, ignore_index=True)
    # Create a dict with the variant_type and variant_size
    variant_types_sizes = pipeline_improvements[['variant_type', 'variant_size']].drop_duplicates()
    result = dict()
    for variant_type, variant_size in variant_types_sizes.values:
        result[f'{variant_type};{variant_size}'] = pipeline_improvements[(
            pipeline_improvements['variant_type'] == variant_type) & (pipeline_improvements['variant_size'] == variant_size)]
    return result


def _get_pipelines_combinations(pipelines_folders: List[str], threads: int) -> Dict[str, Dict[str, pd.DataFrame]]:
    # Each pipeline folder contains a list of .csv files with its possible improvements
    # Read all of them and concatenate them into a single dataframe
    pool = ThreadPoolExecutor(max_workers=threads)
    futures = []
    for pipeline_folder in pipelines_folders:
        futures.append(pool.submit(_read_pipeline_improvements, pipeline_folder))
    pipeline_improvements = [f.result() for f in futures]
    # Create a dictionary with the pipeline name as key and the improvements dataframe as value
    pipelines_combinations = OrderedDict()
    pipeline_names = sorted([os.path.basename(pipeline_folder) for pipeline_folder in pipelines_folders])
    # Make sure the pipeline names are unique
    if len(pipeline_names) != len(set(pipeline_names)):
        raise Exception('Pipeline names (i.e. their subfolder) must be unique')
    for pipeline_name, pipeline_improvement in zip(pipeline_names, pipeline_improvements):
        pipelines_combinations[pipeline_name] = pipeline_improvement
    return pipelines_combinations


def _group_combinations(improvements_combinations_metrics: Dict[str, Dict[str, pd.DataFrame]]):
    first_pipeline_improvements = list(improvements_combinations_metrics.values())[0]
    combinations_groups_dict = dict()
    for variant_type_size in first_pipeline_improvements.keys():
        # Combine all the operation possibilities for each pipeline
        operations_combinations = list(itertools.product(*[[f'{pipeline_name};{op}'
                                                           for op in pipeline_improvements[variant_type_size]['operation'].unique()]
                                                           for pipeline_name, pipeline_improvements in improvements_combinations_metrics.items()]))
        # For each combination, get the metrics
        combinations_rows = []
        for operations_combination in operations_combinations:
            # Get the metrics for each pipeline
            combinations_row = OrderedDict()
            for op in operations_combination:
                pipeline_name, operation = op.split(';')
                combinations_row[pipeline_name] = operation
            combinations_row['variant_type'] = variant_type_size.split(';')[0]
            combinations_row['variant_size'] = variant_type_size.split(';')[1]
            combinations_row['recall_avg'] = 0
            combinations_row['precision_avg'] = 0
            combinations_row['f1_score_avg'] = 0
            combinations_row['protein_affected_genes_count_avg'] = 0
            combinations_row['protein_affected_driver_genes_count_avg'] = 0
            combinations_row['added_callers_sum'] = 0
            # Calculate the metrics for each pipeline
            for op in operations_combination:
                pipeline_name, operation = op.split(';')
                metrics = improvements_combinations_metrics[pipeline_name][variant_type_size]
                # Get the metrics for the current operation
                metrics = metrics[metrics['operation'] == operation].iloc[0]
                # Calculate the metrics for the current operation
                for combinations_row_key in combinations_row.keys():
                    if combinations_row_key.endswith('_avg'):
                        combinations_row[combinations_row_key] += metrics[combinations_row_key.replace('_avg', '')] / len(operations_combination)
                    elif combinations_row_key.endswith('_sum'):
                        combinations_row[combinations_row_key] += metrics[combinations_row_key.replace('_sum', '')]
            combinations_rows.append(combinations_row)
        # Create a dataframe with the metrics
        combinations_df = pd.DataFrame(combinations_rows)
        yield variant_type_size, combinations_df


def main(input_pipelines_improvements: List[str], output: str, threads: int = 1):
    # Create output folder
    os.makedirs(output, exist_ok=True)

    # Compute combinations
    improvements_combinations_metrics = _get_pipelines_combinations(input_pipelines_improvements, threads)
    # Save results
    for variant_type_size, combinations_group in _group_combinations(improvements_combinations_metrics):
        combinations_group.to_csv(os.path.join(output, f'{cleanup_text(variant_type_size)}.csv'), index=False)
