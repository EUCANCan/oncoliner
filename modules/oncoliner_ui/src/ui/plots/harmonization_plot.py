from typing import Dict

from ..model.shared.metrics_table import MetricsTable
from .improvement_plot import ImprovementPlot


class HarmonizationPlot():
    def __init__(self, operations_dict: Dict[str, Dict[str, MetricsTable]]):
        # Create a dict of pipeline_name -> improvement_plot
        self._improvement_plots = dict()
        # Let improvement plot do the heavy lifting
        for operation_name, harmonization_dict in operations_dict.items():
            self._improvement_plots[operation_name] = ImprovementPlot(harmonization_dict)

    def get_plot_data(self):
        # Get the pipeline names from the keys of the operations dict
        pipelines_names = list(self._improvement_plots.keys())
        # Get the titles and labels from the first improvement plot
        first_improvement_plot = self._improvement_plots[pipelines_names[0]]
        titles = first_improvement_plot.get_plot_data()['titles']
        labels = first_improvement_plot.get_plot_data()['labels']
        labels_groups = first_improvement_plot.get_plot_data()['labels_groups']

        # Get the values for each pipeline name
        operation_values = dict()
        for pipeline_name, improvement_plot in self._improvement_plots.items():
            operation_values[pipeline_name] = improvement_plot.get_plot_data()['operation_values']

        return {
            'titles': titles,
            'pipelines_names': pipelines_names,
            'labels': labels,
            'labels_groups': labels_groups,
            'operation_values': operation_values
        }