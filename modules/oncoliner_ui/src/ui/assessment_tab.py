import os

from .model.assessment.assessment_dao import AssessmentDAO
from .plots.metrics_plot import MetricsPlot


class AssessmentTab():
    def __init__(self, env, dao: AssessmentDAO):
        self._env = env
        self._assessment_dao = dao

    def render(self):
        return self._env.get_template(os.path.join("index", "assessment_tab.html")).render(ctrl=self)

    def get_pipelines_names(self):
        return self._assessment_dao.get_pipelines_names()

    def render_pipeline(self, pipeline_name):
        template = self._env.get_template(os.path.join("assessment_tab", "pipeline.html"))
        return template.render(ctrl=self, pipeline_name=pipeline_name)

    def render_warning_panel(self, pipeline_name, sample=None):
        warnings = self._assessment_dao.get_warnings(pipeline_name, sample)
        # Check if there are warnings (all values are empty)
        if not warnings or not any(warnings.values()):
            return ''
        template = self._env.get_template(os.path.join("shared", "warning_panel.html"))
        return template.render(ctrl=self, id=f'assessment_{pipeline_name}_{sample if sample is not None else ""}', warnings=warnings, single_sample=sample is not None)

    def render_metrics_panel(self, pipeline_name):
        template = self._env.get_template(os.path.join("assessment_tab", "metrics_panel.html"))
        metrics_table = self._assessment_dao.get_metrics_table_by_pipeline(pipeline_name)
        return template.render(ctrl=self, id=f'assessment_{pipeline_name}', metrics_table=metrics_table, sample=None)

    def render_sample_metrics_panel(self, pipeline_name, sample):
        template = self._env.get_template(os.path.join("assessment_tab", "metrics_panel.html"))
        metrics_table = self._assessment_dao.get_metrics_table_by_pipeline_and_sample(pipeline_name, sample)
        return template.render(ctrl=self, id=f'assessment_{pipeline_name}_{sample}', metrics_table=metrics_table, sample=sample)

    def render_metrics_table(self, metrics_table, id, table_type, sample):
        template = self._env.get_template(os.path.join("shared", "table.html"))

        id_ = table_type + '_' + id

        data = self._assessment_dao.transform_and_get_by_table_type(table_type, metrics_table)
        return template.render(ctrl=self, data=data, id=id_, hide_legend=sample is not None)

    def render_metrics_plot(self, metrics_table, id, plot_type):
        # Generate metric plot
        metric_plot = MetricsPlot(metrics_table)
        id_ = id + '_' + plot_type
        # Generate dicts
        if plot_type == 'snv_indel_sv':
            chart_data = metric_plot.generate_snv_indel_sv_chart_data()
        elif plot_type == 'sv_subtypes':
            chart_data = metric_plot.generate_sv_subtypes_chart_data()
        elif plot_type == 'sv_subtypes_sizes':
            chart_data = metric_plot.generate_sv_subtypes_sizes_chart_data()
        else:
            raise ValueError('Invalid plot type: ' + plot_type)
        # Integrate ChartJS object into HTML
        template = self._env.get_template(os.path.join("assessment_tab", "metrics_plot.html"))
        return template.render(chart_data=chart_data, id=id_, plot_type=plot_type)

    def get_samples(self, pipeline_name: str):
        return self._assessment_dao.get_samples(pipeline_name)

    def get_sample_types(self, pipeline_name: str, sample: str):
        return self._assessment_dao.get_sample_types(pipeline_name, sample)

    def get_recall_samples(self, pipeline_name: str):
        return self._assessment_dao.get_recall_samples(pipeline_name)

    def get_precision_samples(self, pipeline_name: str):
        return self._assessment_dao.get_precision_samples(pipeline_name)
