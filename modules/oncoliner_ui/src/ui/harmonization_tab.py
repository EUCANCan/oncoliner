import os

from .utils import flatten_dict, flatten_dict_keys
from .plots.harmonization_plot import HarmonizationPlot


class HarmonizationTab():
    def __init__(self, env, dao):
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
        return template.render(ctrl=self, id=f'table_{id_}', data=data)

    def get_flatten_tree(self):
        return flatten_dict(self._harmonization_tree_dict, 'id')

    # def get_harmonization_keys(self):
    #     return self._harmonization_keys

    # def get_harmonization_keys_ids(self):
    #     return self._harmonization_keys_ids

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


