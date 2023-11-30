import os

from .utils import flatten_dict, flatten_dict_keys
from .plots.harmonization_plot import HarmonizationPlot

from .model.harmonization.harmonization_dao import HarmonizationDAO


class HarmonizationTab():
    def __init__(self, env, dao: HarmonizationDAO):
        self._env = env
        self._harmonization_dao = dao
        self._harmonization_tree_dict = self._harmonization_dao.get_tree()

    def render(self):
        return self._env.get_template(os.path.join("index", "harmonization_tab.html")).render(ctrl=self)

    def render_panel(self):
        # Get keys and values
        template = self._env.get_template(os.path.join("harmonization_tab", "harmonization_panel.html"))
        return template.render(ctrl=self)

    def render_table(self, id_, data):
        template = self._env.get_template(os.path.join("harmonization_tab", "harmonization_table.html"))
        # Build the default order of the columns
        columns_order = list(map(lambda x: [data.columns.get_loc(x[0]), x[1]], self._harmonization_dao.get_default_order()))
        # Get the index of the row with all names 'baseline'
        pipelines_names = self._harmonization_dao.get_pipelines_names()
        baseline_index = data[data[pipelines_names].apply(lambda x: all(x == 'baseline'), axis=1)].index[0]
        return template.render(ctrl=self, id=f'table_{id_}', data=data, pipelines_names=pipelines_names, fixed_index=baseline_index, default_order=columns_order)

    def get_best_harmonization_names(self, variant_type: str):
        return self._harmonization_dao.get_best_harmonization_names(variant_type)

    def get_flatten_tree(self):
        return flatten_dict(self._harmonization_tree_dict, 'id')

    def get_pipelines_names(self):
        return self._harmonization_dao.get_pipelines_names()

    def render_dropdown_tree(self, prefix_id, target_group):
        template = self._env.get_template(os.path.join("shared", "dropdown_tree.html"))
        data = flatten_dict_keys(self.get_tree(), 'id')
        self.default_id = data[0]['id']
        return template.render(ctrl=self, data=data, prefix_id=prefix_id, target_group=target_group)

    def get_tree(self):
        return self._harmonization_tree_dict

    def render_tree_branch(self, data, prefix_id, target_group, depth=0, click_callback=None):
        template = self._env.get_template(os.path.join("shared", "tree", "wrapper_template.html"))
        return template.render(ctrl=self, data=data, prefix_id=prefix_id, target_group=target_group, depth=depth, click_callback=click_callback)

    def get_harmonization_plot_data(self):
        harmonization_plot = HarmonizationPlot(self._harmonization_dao.get_operations_metrics())
        return harmonization_plot.get_plot_data()
