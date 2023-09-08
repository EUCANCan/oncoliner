from typing import List, Union
import os
import argparse

from ui import ui_manager


def main(pipelines_evaluations_folders: List[str], output_file: str, pipelines_improvements_folders: Union[List[str], None], harmonization_folder: Union[str, None], callers_evaluation_folder: Union[str, None]):
    for pipeline_ev_folder in pipelines_evaluations_folders:
        if not os.path.exists(pipeline_ev_folder):
            raise Exception(f'Pipeline evaluation folder {pipeline_ev_folder} does not exist')
    if callers_evaluation_folder and not os.path.exists(callers_evaluation_folder):
        raise Exception(f'Callers evaluation folder {callers_evaluation_folder} does not exist')
    if harmonization_folder and not os.path.exists(harmonization_folder):
        raise Exception(f'Harmonization folder {harmonization_folder} does not exist')
    if pipelines_improvements_folders:
        for pipeline_impr_folder in pipelines_improvements_folders:
            if not os.path.exists(pipeline_impr_folder):
                raise Exception(f'Pipeline improvement folder {pipeline_impr_folder} does not exist')

    # Convert everything to absolute paths
    pipelines_evaluations_folders = [os.path.abspath(pipeline_folder) for pipeline_folder in pipelines_evaluations_folders]
    if callers_evaluation_folder:
        callers_evaluation_folder = os.path.abspath(callers_evaluation_folder)
    if harmonization_folder:
        harmonization_folder = os.path.abspath(harmonization_folder)
    if pipelines_improvements_folders:
        pipelines_improvements_folders = [os.path.abspath(pipeline_folder) for pipeline_folder in pipelines_improvements_folders]

    ui_manager.generate_html(pipelines_evaluations_folders, output_file, pipelines_improvements_folders,
                             harmonization_folder, callers_evaluation_folder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='UI HTML generator')
    parser.add_argument('-pe', '--pipelines-evaluations-folders', nargs='+', type=str,
                        required=True, help='Pipelines evaluation folders paths')
    parser.add_argument('-o', '--output-file', type=str, required=True, help='Output file path')
    parser.add_argument('-pi', '--pipelines-improvements-folders', nargs='+', type=str, help='Pipelines improvement folders paths')
    parser.add_argument('-c', '--callers-evaluation-folder', type=str, help='Callers evaluation folder path')
    parser.add_argument('-ha', '--harmonization-folder', type=str, help='Harmonization folder path')

    args = parser.parse_args()

    main(args.pipelines_evaluations_folders, args.output_file, args.pipelines_improvements_folders,
         args.harmonization_folder, args.callers_evaluation_folder)
