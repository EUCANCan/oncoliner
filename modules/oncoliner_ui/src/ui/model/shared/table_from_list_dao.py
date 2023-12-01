from typing import List, Tuple
import glob
import os
import re

import pandas as pd

from ...utils import clean_string, to_sorted_dict
from .metrics_table import read_csv


class TableFromListDAO():
    def __init__(self, list_folder: str):
        self._dfs = []
        self.tree = None
        for file in glob.glob(os.path.join(list_folder, '*.csv')):
            self._dfs.append(read_csv(file))
        concat_df = pd.concat(self._dfs)
        # Find indel_threshold
        self._indel_threshold = int(concat_df[concat_df['variant_type'] == 'INDEL']
                                    ['variant_size'].iloc[0].split('-')[-1].strip())

    def get_df(self):
        return pd.concat(self._dfs)
    
    def get_first_from_ordered(self, variant_type: str, metric_order: List[Tuple[str, str]]):
        df = self.get_df()
        df = df[df['variant_type'] == variant_type]
        for metric, order in metric_order[::-1]:
            df = df.sort_values(by=[metric], ascending=order == 'asc')
        return df.iloc[0]
        

    def get_tree(self, prefix_id):
        if self.tree:
            return self.tree
        # Create a dictionary tree with each variant type and size as a keys, except for INDELs
        result = dict()
        for df in self._dfs:
            first_row = df.iloc[0]
            variant_type = first_row["variant_type"]
            variant_size = str(first_row["variant_size"])
            tree_levels = []
            # Set to _all_ for sizes that contain the others
            variant_size_split = variant_size.split('-')
            if variant_type == 'TRA':
                tree_levels.append('SV')
                tree_levels.append(variant_type)
                # tree_levels.append('_all_')
            elif variant_type == 'INDEL' or variant_type == 'SNV' or variant_type == 'SV':
                tree_levels.append(variant_type)
                if variant_type != 'SNV':
                    tree_levels.append('_all_')
            elif len(variant_size_split) > 1 and variant_type != 'INV' \
                    and int(variant_size_split[-1].strip()) == self._indel_threshold:
                # INDELs are grouped by type
                tree_levels.append('INDEL')
                tree_levels.append(variant_type)
            elif len(variant_size_split) == 1 and variant_type == 'INV' \
                    and int(variant_size.replace('>', '').strip()) == 0:
                tree_levels.append('SV')
                tree_levels.append(variant_type)
                tree_levels.append('_all_')
            elif len(variant_size_split) == 1 and variant_type != 'INV' \
                    and int(variant_size.replace('>', '').strip()) == self._indel_threshold:
                tree_levels.append('SV')
                tree_levels.append(variant_type)
                tree_levels.append('_all_')
            else:
                tree_levels.append('SV')
                tree_levels.append(variant_type)
                tree_levels.append(variant_size)
            
            last_dict = result
            hierarchy = []
            for tree_level in tree_levels:
                if tree_level != '_all_':
                    hierarchy.append(tree_level)
                last_dict[tree_level] = last_dict.get(tree_level, dict())
                last_dict = last_dict[tree_level]
            last_dict['hierarchy'] = ' > '.join(hierarchy)
            last_dict['id'] = clean_string(f'{prefix_id}_{variant_type}_{variant_size}')
            # Round all floats to 2 decimals
            last_dict['data'] = df

        # Sort by variant size
        def extract_lower_limit_size(variant_size):
            matches = re.findall(r'\d+', variant_size)
            if len(matches) > 0:
                return int(matches[0])
            return 0

        def comparator(x, y):
            return extract_lower_limit_size(x) < extract_lower_limit_size(y)

        for key in result['SV']:
            result['SV'][key] = to_sorted_dict(result['SV'][key], comparator)

        self.tree = result
        return self.tree


