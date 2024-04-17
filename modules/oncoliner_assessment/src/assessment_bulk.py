from typing import Iterable, List
import os
import argparse
import glob
from concurrent.futures import ProcessPoolExecutor

from assessment_main import main  # noqa
from vcf_ops.constants import DEFAULT_CONTIGS, DEFAULT_VARIANT_TYPES, DEFAULT_INDEL_THRESHOLD, DEFAULT_WINDOW_RADIUS, DEFAULT_SV_BINS  # noqa
from vcf_ops.metrics import aggregate_metrics, combine_precision_recall_metrics  # noqa

import pandas as pd
import logging


def read_config(config_path: str) -> pd.DataFrame:
    """
    Reads the config file and returns a dataframe
    """
    config = pd.read_csv(config_path, sep='\t')
    # Strip all strings
    config = config.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    config['truth_vcf_paths'] = config['truth_vcf_paths'].map(lambda x: [f.strip() for f in x.split(',')])
    config['test_vcf_paths'] = config['test_vcf_paths'].map(lambda x: [f.strip() for f in x.split(',')])
    config['bed_mask_paths'] = config['bed_mask_paths'].map(lambda x: [f.strip() for f in x.split(',')]) if 'bed_mask_paths' in config else [''] * len(config)
    config['sample_types'] = config['sample_types'].map(lambda x: set([f.strip() for f in x.split(',')]))
    # There must be at least one recall and one precision sample
    if len(config[config['sample_types'].map(lambda x: 'recall' in x)]) == 0:
        raise ValueError('There must be at least one recall sample')
    if len(config[config['sample_types'].map(lambda x: 'precision' in x)]) == 0:
        raise ValueError('There must be at least one precision sample')
    return config


def run_evaluator_sample(output_folder: str, sample: pd.Series, indel_threshold: int, window_radius: int, sv_size_bins: List[str], contigs: List[str], variant_types: List[str], keep_intermediates: bool, no_gzip: bool) -> None:
    """
    Runs the evaluator for a single sample
    """
    sample_name = sample['sample_name']
    truth_vcf_paths = sample['truth_vcf_paths']
    test_vcf_paths = sample['test_vcf_paths']
    bed_mask_paths = sample['bed_mask_paths'] if 'bed_mask_paths' in sample else []
    fasta_path = sample['reference_fasta_path']
    output_folder = os.path.join(output_folder, sample_name)
    os.makedirs(output_folder, exist_ok=True)
    output_prefix = os.path.join(output_folder, 'pipeline')
    # If output_prefixmetrics.csv already exists and is not empty, skip the evaluation
    if os.path.exists(output_prefix + 'metrics.csv') and os.path.getsize(output_prefix + 'metrics.csv') > 0:
        logging.info(f'Skipping {sample_name} evaluation because the metrics file already exists')
        return
    main(truth_vcf_paths, test_vcf_paths, bed_mask_paths, output_prefix, fasta_path, indel_threshold,
         window_radius, sv_size_bins, contigs, variant_types, keep_intermediates, no_gzip)


def aggregate_metrics_from_samples(output_file: str, samples_folder: str, recall_samples: Iterable[str], precision_samples: Iterable[str]):
    # List all folders in the output folder
    recall_samples_folders = [os.path.join(samples_folder, sample) for sample in recall_samples]
    precision_samples_folders = [os.path.join(samples_folder, sample) for sample in precision_samples]
    # List all metrics files
    recall_samples_files = [glob.glob(os.path.join(sample_folder, '*metrics.csv'))[0] for sample_folder in recall_samples_folders]
    precision_samples_files = [glob.glob(os.path.join(sample_folder, '*metrics.csv'))[0] for sample_folder in precision_samples_folders]
    recall_dfs = [pd.read_csv(file) for file in recall_samples_files]
    precision_dfs = [pd.read_csv(file) for file in precision_samples_files]
    # Aggregate metrics
    recall_agg_df = aggregate_metrics(recall_dfs)
    precision_agg_df = aggregate_metrics(precision_dfs)
    agg_metrics = combine_precision_recall_metrics(recall_agg_df, precision_agg_df)
    # Write to file
    agg_metrics.to_csv(output_file, index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ONCOLINER Assessment Bulk')
    parser.add_argument('-c', '--config-file', required=True, type=str, help='Path to the config TSV file')
    parser.add_argument('-o', '--output-folder', required=True, type=str, help='Path to the output folder')
    parser.add_argument('-it', '--indel-threshold',
                        help=f'Indel threshold, inclusive (default={DEFAULT_INDEL_THRESHOLD})', default=DEFAULT_INDEL_THRESHOLD, type=int)
    parser.add_argument('-wr', '--window-radius',
                        help=f'Window radius (default={DEFAULT_WINDOW_RADIUS})', default=DEFAULT_WINDOW_RADIUS, type=int)
    parser.add_argument(
        '--sv-size-bins', help=f'SV size bins for the output_prefix metrics (default={DEFAULT_SV_BINS})', nargs='+', default=DEFAULT_SV_BINS, type=int)
    parser.add_argument('--contigs', nargs='+', default=DEFAULT_CONTIGS, type=str,
                        help=f'Contigs to process (default={DEFAULT_CONTIGS})')
    parser.add_argument('--variant-types', nargs='+', default=DEFAULT_VARIANT_TYPES, type=str,
                        help=f'Variant types to process (default={DEFAULT_VARIANT_TYPES})')
    parser.add_argument('--keep-intermediates',
                        help='Keep intermediate CSV/VCF files from input VCF files', action='store_true', default=False)
    parser.add_argument('--no-gzip', help='Do not gzip output_prefix VCF files', action='store_true', default=False)
    parser.add_argument('-p', '--max-processes', type=int, default=1, help='Maximum number of processes to use (defaults to 1)')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    # Convert to absolute paths
    args.config_file = os.path.abspath(args.config_file)

    config = read_config(args.config_file)
    pool = ProcessPoolExecutor(max_workers=args.max_processes)
    samples_output_folder = os.path.join(args.output_folder, 'samples')
    os.makedirs(samples_output_folder, exist_ok=True)
    futures = []
    for _, sample in config.iterrows():
        futures.append(pool.submit(run_evaluator_sample, samples_output_folder, sample, args.indel_threshold, args.window_radius,
                       args.sv_size_bins, args.contigs, args.variant_types, args.keep_intermediates, args.no_gzip))
    for future in futures:
        future.result()

    pool.shutdown()

    # Aggregate metrics
    output_file = os.path.join(args.output_folder, 'aggregated_metrics.csv')
    recall_samples = set(config[config['sample_types'].map(lambda x: 'recall' in x)]['sample_name'].tolist())
    precision_samples = set(config[config['sample_types'].map(lambda x: 'precision' in x)]['sample_name'].tolist())
    aggregate_metrics_from_samples(output_file, samples_output_folder, recall_samples, precision_samples)
