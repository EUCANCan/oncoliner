import os

from .utils import flatten_dict
from .plots.improvement_plot import ImprovementPlot


class ImprovementTab():
    def __init__(self, env, dao):
        self._env = env
        self._improvement_dao = dao

    def render_pipeline(self, pipeline_name, is_first):
        template = self._env.get_template(os.path.join("improvement_tab", "pipeline.html"))
        return template.render(ctrl=self, pipeline_name=pipeline_name, is_first=is_first)

    def render(self):
        return self._env.get_template(os.path.join("index", "improvement_tab.html")).render(ctrl=self)

    def get_pipelines_names(self):
        return self._improvement_dao.get_pipelines_names()

    def get_tree(self, pipeline_name):
        return self._improvement_dao.get_pipeline_improvement_tree(pipeline_name)

    def get_flatten_tree(self, pipeline_name):
        return flatten_dict(self._improvement_dao.get_pipeline_improvement_tree(pipeline_name), 'id')

    def get_improvement_plot_data(self, pipeline_name):
        improvement_plot = ImprovementPlot(
            self._improvement_dao.get_pipeline_improvement_operations_metrics(pipeline_name))
        return improvement_plot.get_plot_data()

    def render_panel(self, pipeline_name):
        template = self._env.get_template(os.path.join("improvement_tab", "improvement_panel.html"))
        return template.render(ctrl=self, pipeline_name=pipeline_name)

    def render_table(self, id_, pipeline_name, data):
        template = self._env.get_template(os.path.join("improvement_tab", "improvement_table.html"))
        return template.render(ctrl=self, id=f'table_{id_}', pipeline_name=pipeline_name, data=data)

    def render_tree_branch(self, data, prefix_id, target_group, depth=0):
        template = self._env.get_template(os.path.join("shared", "tree", "wrapper_template.html"))
        return template.render(ctrl=self, data=data, prefix_id=prefix_id, target_group=target_group, depth=depth)