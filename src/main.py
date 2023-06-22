from typing import Set
import os
import argparse
import subprocess
from concurrent.futures import ProcessPoolExecutor
import logging

import pandas as pd


def read_config(config_path: str) -> pd.DataFrame:
    """
    Reads the config file and returns a dataframe
    """
    config = pd.read_csv(config_path, sep='\t')
    config['truth_vcf_paths'] = config['truth_vcf_paths'].map(lambda x: x.split(','))
    config['sample_type'] = config['sample_type'].map(lambda x: set(x.split(',')))
    return config


def run_evaluator_sample(pipeline_folder_path: str, output_folder: str, sample: pd.Series) -> None:
    """
    Runs the evaluator for a single sample
    """
    sample_name = sample['sample_name']
    truth_vcf_paths = sample['truth_vcf_paths']
    fasta_path = sample['reference_fasta_path']
    evaluator_command = os.environ['EVALUATOR_COMMAND']
    evaluator_command_split = evaluator_command.split()
    pipeline_vcf_paths = [os.path.join(pipeline_folder_path, sample_name, '*.vcf.gz'),
                          os.path.join(pipeline_folder_path, sample_name, '*.vcf'),
                          os.path.join(pipeline_folder_path, sample_name, '*.bcf')]
    output_folder = os.path.join(output_folder, sample_name)
    os.makedirs(output_folder, exist_ok=True)
    output_prefix = os.path.join(output_folder, os.path.basename(pipeline_folder_path))
    # If output_prefixmetrics.csv already exists and is not empty, skip the evaluation
    if os.path.exists(output_prefix + 'metrics.csv') and os.path.getsize(output_prefix + 'metrics.csv') > 0:
        logging.info(f'Skipping {sample_name} for {os.path.basename(pipeline_folder_path)} because the metrics file already exists')
        return
    args = evaluator_command_split + ['-t', *truth_vcf_paths, '-v', *pipeline_vcf_paths, '-f', fasta_path, '-o', output_prefix]
    print(args)
    subprocess.check_call(args)


def run_evaluator(pipeline_folder_path: str, output_folder: str, config: pd.DataFrame, max_processes: int) -> None:
    pool = ProcessPoolExecutor(max_workers=max_processes)
    futures = []
    for _, row in config.iterrows():
        futures.append(pool.submit(run_evaluator_sample, pipeline_folder_path, output_folder, row))
    for future in futures:
        future.result()
    pool.shutdown()


def run_improver(pipeline_evaluations_folder_path: str, output_folder: str, callers_folder: str, config: pd.DataFrame, max_processes: int) -> None:
    improver_command = os.environ['IMPROVER_COMMAND']
    improver_command_split = improver_command.split()
    recall_samples = config['recall' in config['sample_type']]['sample_name'].tolist()
    precision_samples = config['precision' in config['sample_type']].tolist()
    # TODO: Callers folder is missing
    args = improver_command_split + ['-e', pipeline_evaluations_folder_path,
                                     '-c', callers_folder,
                                     '-rs', *recall_samples, '-ps', *precision_samples,
                                     '-o', output_folder, '-p', max_processes]
    subprocess.check_call(args)  # type: ignore


def check_samples_folders(pipeline_folder_path: str, sample_names: Set[str]) -> None:
    """
    Checks if all the samples in the config file are in the pipeline folder
    """
    pipeline_samples = set(os.listdir(pipeline_folder_path))
    missing_samples = sample_names - pipeline_samples
    missing_pipeline_samples = pipeline_samples - sample_names
    if missing_samples:
        raise Exception(f'The following samples are missing from {pipeline_folder_path}: {missing_samples}')
    if missing_pipeline_samples:
        raise Exception(f'The following samples are missing from the config file: {missing_pipeline_samples}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, required=True, help='Path to config file')
    parser.add_argument('-pf', '--pipelines-folders', type=str, required=True, nargs='+', help='Paths to pipelines folders')
    parser.add_argument('-o', '--output', type=str, required=True, help='Path to output folder')
    parser.add_argument('-cf', '--callers-folder', type=str, help='Path to callers folder')
    parser.add_argument('--max-processes', type=int, default=len(os.sched_getaffinity(0)),
                        help='Maximum number of processes to use (defaults to the number of cores)')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    # Make sure the paths are absolute
    args.config = os.path.abspath(args.config)
    args.pipelines_folders = [os.path.abspath(folder) for folder in args.pipelines_folders]
    args.output = os.path.abspath(args.output)
    if args.callers_folder:
        args.callers_folder = os.path.abspath(args.callers_folder)
    # Check if the environment variables are set
    if 'EVALUATOR_COMMAND' not in os.environ:
        raise Exception('EVALUATOR_COMMAND environment variable is not set')
    if args.callers_folder and 'IMPROVER_COMMAND' not in os.environ:
        raise Exception('IMPROVER_COMMAND environment variable is not set')
    if args.callers_folder and len(args.pipelines_folders) > 1 and 'HARMONIZATOR_COMMAND' not in os.environ:
        raise Exception('HARMONIZATOR_COMMAND environment variable is not set')
    # Make sure the basenames of the pipelines folders are unique
    if len(args.pipelines_folders) != len(set([os.path.basename(folder) for folder in args.pipelines_folders])):
        raise Exception('The basenames of the pipelines folders must be unique')

    # Read the config file
    config = read_config(args.config)

    # Check if all the folders inside the pipelines are in the config file
    sample_names = set(config['sample_name'].unique())
    for folder in args.pipelines_folders:
        check_samples_folders(folder, sample_names)

    # Create the output folder
    os.makedirs(args.output, exist_ok=True)

    # Run the evaluator
    for pipeline_folder in args.pipelines_folders:
        output_pipeline_evaluation_folder = os.path.join(args.output, 'evaluation', os.path.basename(pipeline_folder))
        os.makedirs(output_pipeline_evaluation_folder, exist_ok=True)
        run_evaluator(pipeline_folder, output_pipeline_evaluation_folder, config, args.max_processes)

    # Run the improver
    if not args.callers_folder:
        exit(0)

    for pipeline_evaluation_folder in os.listdir(os.path.join(args.output, 'evaluation')):
        pipeline_evaluation_folder = os.path.join(args.output, 'evaluation', pipeline_evaluation_folder)
        output_pipeline_improvement_folder = os.path.join(args.output, 'improvement', os.path.basename(pipeline_evaluation_folder))
        os.makedirs(output_pipeline_improvement_folder, exist_ok=True)
        run_improver(pipeline_evaluation_folder, output_pipeline_improvement_folder, args.callers_folder, config, args.max_processes)

    exit(0)

    # Run the harmonizator
    if len(args.pipelines_folders) > 1:
        output_harmonization_folder = os.path.join(args.output, 'harmonization')
        os.makedirs(output_harmonization_folder, exist_ok=True)
        # TODO: run harmonizator
