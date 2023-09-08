from typing import List

import os
import glob
from ..shared.table_from_list_dao import TableFromListDAO
from ..shared.metrics_table import MetricsTable
from ...utils import path_to_pipeline_name


class ImprovementDAO():
    def __init__(self, pipeline_folders: List[str]) -> None:
        # Create a dict of pipeline_name -> pipeline_dao
        self._pipeline_dao = dict()
        self._pipelines_names = []

        for pipeline_folder in pipeline_folders:
            improvement_list_folder = os.path.join(pipeline_folder, 'improvement_list')
            results_folder = os.path.join(pipeline_folder, 'results')
            pipeline_name = path_to_pipeline_name(pipeline_folder)
            self._pipelines_names.append(pipeline_name)
            self._pipeline_dao[pipeline_name] = ImprovementPipelineDAO(improvement_list_folder, results_folder)

    def get_pipelines_names(self):
        return self._pipelines_names

    def get_pipeline_improvement_tree(self, pipeline_name: str):
        return self._pipeline_dao[pipeline_name].get_tree('improvement_' + pipeline_name)

    def get_pipeline_improvement_operations_metrics(self, pipeline_name: str):
        return self._pipeline_dao[pipeline_name].get_operations_metrics()


class ImprovementPipelineDAO():
    def __init__(self, improvement_list_folder: str, results_folder: str):
        self._table = TableFromListDAO(improvement_list_folder)
        # Create a dict of operation_name -> metrics_table
        self._operations_dict = dict()
        # Iterate over all the aggregated_metrics.csv files
        for agg_metrics_file in glob.glob(os.path.join(results_folder, '*', 'aggregated_metrics.csv')):
            agg_metrics_metrics_table = MetricsTable(agg_metrics_file)
            op_name = os.path.basename(os.path.dirname(agg_metrics_file))
            self._operations_dict[op_name] = agg_metrics_metrics_table

    def get_operations_metrics(self):
        return self._operations_dict

    def get_tree(self, prefix_id):
        return self._table.get_tree(prefix_id)
