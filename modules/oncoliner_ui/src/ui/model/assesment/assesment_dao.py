from typing import List, Optional

from .assesment_pipeline_dao import AssesmentPipelineDAO
from ..shared.metrics_table import MetricsTable
from ...utils import path_to_pipeline_name


class AssesmentDAO():
    def __init__(self, pipeline_folders: List[str], callers_folders: str) -> None:
        # Create a dict of pipeline_name -> pipeline_dao
        self._pipeline_dao = dict()
        self._pipelines_names = []
        for pipeline_folder in pipeline_folders:
            pipeline_name = path_to_pipeline_name(pipeline_folder)
            self._pipelines_names.append(pipeline_name)
            self._pipeline_dao[pipeline_name] = AssesmentPipelineDAO(pipeline_folder)

    def get_pipelines_names(self):
        return self._pipelines_names

    def get_metrics_table_by_pipeline(self, pipeline_name: str):
        return self._pipeline_dao[pipeline_name].get_metrics_table()

    def get_metrics_table_by_pipeline_and_sample(self, pipeline_name: str, sample: str):
        return self._pipeline_dao[pipeline_name].get_metrics_table(sample)

    def transform_and_get_by_table_type(self, table_type: str, metrics_table: MetricsTable):
        if table_type == 'snv_indel_sv':
            data = metrics_table.get_snv_indel_sv()
        elif table_type == 'sv_subtypes':
            data = metrics_table.get_sv_subtypes()
        elif table_type == 'sv_subtypes_sizes':
            data = metrics_table.get_sv_subtypes_sizes()
        else:
            raise ValueError('Invalid table type: ' + table_type)
        return data
    
    def get_warnings(self, pipeline_name: str, sample: Optional[str]):
        return self._pipeline_dao[pipeline_name].get_warnings(sample)

    def get_samples(self, pipeline_name: str):
        return self._pipeline_dao[pipeline_name].get_samples()

    def get_sample_types(self, pipeline_name: str, sample: str):
        return self._pipeline_dao[pipeline_name].get_sample_types(sample)

    def get_recall_samples(self, pipeline_name: str):
        return self._pipeline_dao[pipeline_name].get_recall_samples()

    def get_precision_samples(self, pipeline_name: str):
        return self._pipeline_dao[pipeline_name].get_precision_samples()
