from typing import Optional, List
import os
import glob
import pandas as pd

from ..shared.metrics_table import MetricsTable


class AssessmentPipelineDAO():
    def __init__(self, pipeline_results_folder: str) -> None:
        self._pipeline_results_folder = pipeline_results_folder

        csv_path = os.path.join(self._pipeline_results_folder, 'aggregated_metrics.csv')
        self._agg_metrics_table = MetricsTable(csv_path)

        # Read config file for samples
        config_file = os.path.join(self._pipeline_results_folder, 'config.tsv')
        config_df = pd.read_csv(config_file, sep='\t')

        self._sample_types = dict()
        for _, row in config_df.iterrows():
            sample = row['sample_name']
            sample_types = row['sample_types'].split(',')
            self._sample_types[sample] = sample_types

        # Create a dict of sample -> metrics_table
        self._metrics_table_by_sample = dict()
        # Iterate the samples in pipeline_results_folder
        for csv_file in glob.glob(os.path.join(self._pipeline_results_folder, 'samples', '*', '*metrics.csv')):
            sample = os.path.basename(os.path.dirname(csv_file))
            self._metrics_table_by_sample[sample] = MetricsTable(csv_file, self._sample_types[sample])

    def get_metrics_table(self, sample: Optional[str] = None) -> MetricsTable:
        if sample:
            return self._metrics_table_by_sample[sample]
        return self._agg_metrics_table

    def get_warnings(self, sample: Optional[str] = None):
        warnings = dict()
        sample_list = [sample] if sample else self.get_samples()
        for sample in sample_list:
            sample_warning = self.get_metrics_table(sample).get_warnings()
            # Add sample warnings to warnings dict
            for warning_id, affected_types in sample_warning.items():
                if warning_id not in warnings:
                    warnings[warning_id] = dict()
                warnings[warning_id][sample] = affected_types
        return warnings

    def get_samples(self) -> List[str]:
        return list(self._sample_types.keys())

    def get_sample_types(self, sample: str) -> List[str]:
        return self._sample_types[sample]

    def get_recall_samples(self) -> List[str]:
        return [sample for sample in self._sample_types.keys() if 'recall' in self._sample_types[sample]]

    def get_precision_samples(self) -> List[str]:
        return [sample for sample in self._sample_types.keys() if 'precision' in self._sample_types[sample]]
