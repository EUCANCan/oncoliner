from typing import List, Dict, Tuple

import os
from collections import OrderedDict
from ..shared.table_from_list_dao import TableFromListDAO
from ..shared.metrics_table import MetricsTable
from ...utils import path_to_pipeline_name


class HarmonizationDAO():
    def __init__(self, harmonization_folder: str, pipelines_improvements_folder: List[str]):
        self._harmonization_folder = harmonization_folder
        self._table = TableFromListDAO(harmonization_folder)
        self._pipelines_names = []
        # Create a dict of pipeline_name -> operation -> metrics_table
        temp_dict = dict()
        for pipeline_folder in pipelines_improvements_folder:
            results_folder = os.path.join(pipeline_folder, 'results')
            pipeline_name = path_to_pipeline_name(pipeline_folder)
            if pipeline_name not in temp_dict:
                temp_dict[pipeline_name] = dict()
            self._pipelines_names.append(pipeline_name)
            # Iterate over the operation subfolders in the results folder
            pipeline_operation_folders = self._table.get_df()[pipeline_name].unique()
            for agg_metrics_file in [os.path.join(results_folder, operation_folder, 'aggregated_metrics.csv') for operation_folder in pipeline_operation_folders]:
                op_name = os.path.basename(os.path.dirname(agg_metrics_file))
                agg_metrics_table = MetricsTable(agg_metrics_file)
                temp_dict[pipeline_name][op_name] = agg_metrics_table
        # Sort the pipelines names
        self._pipelines_names.sort()
        # Create an ordered dict of pipeline_name -> operation -> metrics_table
        self._pipelines_operations_metrics_dict = OrderedDict()
        for pipeline_name in self._pipelines_names:
            self._pipelines_operations_metrics_dict[pipeline_name] = temp_dict[pipeline_name]

    def get_default_order(self) -> List[Tuple[str, str]]:
        return [('h_score', 'asc'), ('gdr', 'asc'), ('f1_score_avg', 'desc'), ('added_callers_sum', 'asc')]

    def get_best_harmonization_names(self, variant_type: str) -> Dict[str, str]:
        first_row = self._table.get_first_from_ordered(variant_type, self.get_default_order())
        result = OrderedDict()
        for pipeline_name in self._pipelines_names:
            result[pipeline_name] = first_row[pipeline_name]
        return result

    def get_pipelines_names(self):
        return self._pipelines_names

    def get_tree(self):
        return self._table.get_tree('harmonization')

    def get_operations_metrics(self) -> Dict[str, Dict[str, MetricsTable]]:
        return self._pipelines_operations_metrics_dict
