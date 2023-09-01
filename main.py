from typing import Set, List, Union, Tuple
import os
import glob
import argparse
import subprocess
import logging

import pandas as pd


def read_config(config_path: str) -> pd.DataFrame:
    """
    Reads the config file and returns a dataframe
    """
    config = pd.read_csv(config_path, sep='\t')
    return config


def get_recall_precision_samples(config: pd.DataFrame) -> Tuple[List[str], List[str]]:
    sample_type_set = config['sample_types'].map(lambda x: set(x.split(',')))
    recall_samples = config[sample_type_set.apply(lambda x: 'recall' in x)]['sample_name'].tolist()
    precision_samples = config[sample_type_set.apply(lambda x: 'precision' in x)]['sample_name'].tolist()
    return recall_samples, precision_samples


def run_evaluator(pipeline_folder_path: str, output_folder: str, config: pd.DataFrame, max_processes: int) -> None:
    pipelines_vcf_paths = config['sample_name'].apply(
        lambda sample_name: ','.join([os.path.join(pipeline_folder_path, sample_name, '*.vcf.gz'),
                                      os.path.join(pipeline_folder_path, sample_name, '*.vcf'),
                                      os.path.join(pipeline_folder_path, sample_name, '*.bcf')]))
    # Create a new config file with the paths to the pipeline VCFs
    config_with_pipeline_vcf_paths = config.copy()
    config_with_pipeline_vcf_paths['test_vcf_paths'] = pipelines_vcf_paths
    # Save the new config file
    config_path = os.path.join(output_folder, 'config.tsv')
    config_with_pipeline_vcf_paths.to_csv(config_path, sep='\t', index=False)
    # Execute the assesment
    assesment_command = os.environ['ASSESMENT_COMMAND']
    evaluator_command_split = assesment_command.split()
    args = evaluator_command_split + ['-c', config_path, '-o', output_folder, '-p', str(max_processes)]
    subprocess.check_call(args)


def run_improver(pipeline_evaluations_folder_path: str, output_folder: str, callers_folder: str, config: pd.DataFrame, max_processes: int) -> None:
    improver_command = os.environ['IMPROVER_COMMAND']
    improver_command_split = improver_command.split()
    recall_samples, precision_samples = get_recall_precision_samples(config)
    args = improver_command_split + ['-e', pipeline_evaluations_folder_path,
                                     '-c', callers_folder,
                                     '-rs', *recall_samples, '-ps', *precision_samples,
                                     '-o', output_folder, '-p', str(max_processes)]
    subprocess.check_call(args)


def run_harmonizator(pipeline_improvements_folder_paths: List[str], output_folder: str, config: pd.DataFrame, max_processes: int) -> None:
    harmonizer_command = os.environ['HARMONIZATION_COMMAND']
    harmonizer_command_split = harmonizer_command.split()
    args = harmonizer_command_split + ['-i', *pipeline_improvements_folder_paths, '-o', output_folder, '-p', str(max_processes)]
    subprocess.check_call(args)


def run_ui(pipelines_evaluation_folder_paths: List[str], pipeline_improvements_folder_paths: Union[List[str], None], callers_folder: Union[str, None], harmonization_folder: Union[str, None], output_folder: str, config: pd.DataFrame) -> None:
    ui_command = os.environ['UI_COMMAND']
    ui_command_split = ui_command.split()
    recall_samples, precision_samples = get_recall_precision_samples(config)
    args = ui_command_split + ['-pe', *pipelines_evaluation_folder_paths, '-rs', *recall_samples, '-ps', *precision_samples]
    if pipeline_improvements_folder_paths:
        args += ['-pi', *pipeline_improvements_folder_paths]
    if callers_folder:
        args += ['-c', callers_folder]
    if harmonization_folder:
        args += ['-ha', harmonization_folder]
    args += ['-o', output_folder]
    subprocess.check_call(args)


def check_samples_folders(pipeline_folder_path: str, sample_names: Set[str]) -> None:
    """
    Checks if all the samples in the config file are in the pipeline folder
    """
    pipeline_samples = set(os.listdir(pipeline_folder_path))
    missing_samples = sample_names - pipeline_samples
    missing_pipeline_samples = pipeline_samples - sample_names
    if missing_samples:
        raise Exception(f'The following samples are missing in {pipeline_folder_path}: {missing_samples}')
    if missing_pipeline_samples:
        logging.warning(f'The following samples are missing from the config file: {missing_pipeline_samples}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, required=True, help='Path to config file')
    parser.add_argument('-pf', '--pipelines-folders', type=str, required=True, nargs='+', help='Paths to pipelines folders')
    parser.add_argument('-o', '--output', type=str, required=True, help='Path to output folder')
    parser.add_argument('-cf', '--callers-folder', type=str, help='Path to callers folder')
    parser.add_argument('--max-processes', type=int, default=1, help='Maximum number of processes to use (defaults to 1)')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    # Make sure the paths are absolute
    args.config = os.path.abspath(args.config)
    args.pipelines_folders = [os.path.abspath(folder) for folder in args.pipelines_folders]
    args.output = os.path.abspath(args.output)
    if args.callers_folder:
        args.callers_folder = os.path.abspath(args.callers_folder)
    # Check if the environment variables are set, set them if not
    if 'ASSESMENT_COMMAND' not in os.environ:
        logging.info('ASSESMENT_COMMAND environment variable is not set')
        os.environ['ASSESMENT_COMMAND'] = 'python3 modules/oncoliner_assesment/src/assesment_bulk.py'
    if 'UI_COMMAND' not in os.environ:
        logging.info('UI_COMMAND environment variable is not set')
        os.environ['UI_COMMAND'] = 'python3 modules/oncoliner_ui/src/ui_main.py'
    if args.callers_folder and 'IMPROVEMENT_COMMAND' not in os.environ:
        logging.info('IMPROVEMENT_COMMAND environment variable is not set')
        os.environ['IMPROVEMENT_COMMAND'] = 'python3 modules/oncoliner_improvement/src/improvement_main.py'
    if args.callers_folder and len(args.pipelines_folders) > 1 and 'HARMONIZATION_COMMAND' not in os.environ:
        logging.info('HARMONIZATION_COMMAND environment variable is not set')
        os.environ['HARMONIZATION_COMMAND'] = 'python3 modules/oncoliner_harmonization/src/harmonization_main.py'
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
    pipelines_evaluation_folder_paths = glob.glob(os.path.join(args.output, 'evaluation', '*'))

    # Run the improver
    pipeline_improvements_folder_paths = None
    if args.callers_folder:
        for pipeline_evaluation_folder in pipelines_evaluation_folder_paths:
            output_pipeline_improvement_folder = os.path.join(args.output, 'improvement', os.path.basename(pipeline_evaluation_folder))
            os.makedirs(output_pipeline_improvement_folder, exist_ok=True)
            run_improver(pipeline_evaluation_folder, output_pipeline_improvement_folder, args.callers_folder, config, args.max_processes)
        pipeline_improvements_folder_paths = glob.glob(os.path.join(args.output, 'improvement', '*'))

    # Run the harmonizator
    output_harmonization_folder = None
    if len(args.pipelines_folders) > 1 and pipeline_improvements_folder_paths:
        output_harmonization_folder = os.path.join(args.output, 'harmonization')
        os.makedirs(output_harmonization_folder, exist_ok=True)
        pipeline_improvements_folder_result_paths = [os.path.join(folder, 'results') for folder in pipeline_improvements_folder_paths]
        run_harmonizator(pipeline_improvements_folder_result_paths, output_harmonization_folder, config, args.max_processes)

    # Run the UI
    ui_output_folder = os.path.join(args.output, 'ui_report')
    os.makedirs(ui_output_folder, exist_ok=True)
    run_ui(pipelines_evaluation_folder_paths, pipeline_improvements_folder_paths,
           args.callers_folder, output_harmonization_folder, ui_output_folder, config)
