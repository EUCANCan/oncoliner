from typing import Dict, List, Tuple
import pandas as pd

from ..model.shared.metrics_table import MetricsTable


def _generate_improvement_plot_data(df: pd.DataFrame) -> List[List[float]]:
    recall_values = df['recall'].tolist()
    precision_values = df['precision'].tolist()
    f1_values = df['f1_score'].tolist()
    return [recall_values, precision_values, f1_values]


def _generate_plot_labels(df: pd.DataFrame) -> Tuple[List[str], Dict[str, List[str]]]:
    labels_groups = dict()
    # We actively ignore the INS variants
    labels_groups['snv_indel_sv'] = ['SNV', 'INDEL', 'SV']
    labels_groups['sv_subtypes'] = ['SNV', 'INDEL', 'TRA', 'INV', 'DEL (SV)', 'DUP (SV)']
    labels_groups['sv_subtypes_sizes'] = ['SNV', 'INDEL', 'TRA']
    # Get the indel threshold
    indel_threshold = int(df[df['variant_type'] == 'INDEL']['variant_size'].iloc[0].split('-')[-1].strip())
    # Labels are a list of "variant_type; variant_size", except when the variant_size is the whole variant type
    labels = []
    for _, row in df.iterrows():
        if row['variant_type'] == 'INDEL' or row['variant_type'] == 'SV' or \
                row['variant_type'] == 'TRA' or row['variant_type'] == 'SNV' or \
                (row['variant_type'] == 'INV' and row['variant_size'].split('>')[-1].strip() == '0'):
            labels.append(row['variant_type'])
        elif (row['variant_type'] == 'DEL' or row['variant_type'] == 'INS' or row['variant_type'] == 'DUP') and \
                row['variant_size'].split('>')[-1].strip() == f'{indel_threshold}':
            labels.append(f'{row["variant_type"]} (SV)')
        else:
            label_name = f'{row["variant_type"]}; {row["variant_size"]}'
            labels.append(label_name)
            if not ((row['variant_type'] == 'DEL' and row['variant_size'].split('-')[-1].strip() == f'{indel_threshold}') or \
                    'INS' in row['variant_type']):
                labels_groups['sv_subtypes_sizes'].append(label_name)
    return labels, labels_groups


class ImprovementPlot():
    def __init__(self, operations_dict: Dict[str, MetricsTable]):
        self._operations_dict = operations_dict

    def get_plot_data(self):
        # Get the labels from the first operation, concatenating variant_type and variant_name
        first_operation_name = list(self._operations_dict.keys())[0]
        first_df = self._operations_dict[first_operation_name].get_df()
        labels, labels_groups = _generate_plot_labels(first_df)
        # Get the values for each operation name
        operation_values = dict()
        for operation_name, metrics_table in self._operations_dict.items():
            operation_values[operation_name] = _generate_improvement_plot_data(metrics_table.get_df())

        return {
            'titles': ['Recall', 'Precision', 'F1 Score'],
            'labels': labels,
            'labels_groups': labels_groups,
            'operation_values': operation_values
        }
