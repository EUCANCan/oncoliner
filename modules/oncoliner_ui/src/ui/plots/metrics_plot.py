from typing import List, Dict
import pandas as pd

from ..model.shared.metrics_table import MetricsTable


def _generate_chart_data(df: pd.DataFrame):
    chart_data = []
    for index, row in df.iterrows():
        if row['variant_type'] == 'SNV':
            axis_id = 'snv'
        elif row['variant_type'] == 'SV' or row['variant_type'] == 'INV' or \
                row['variant_type'] == 'DUP' or row['variant_type'] == 'TRA' or \
                (row['variant_type'] == 'DEL' and not row['variant_size'].startswith('1 -')) or \
                (row['variant_type'] == 'INS' and not row['variant_size'].startswith('1 -')):
            axis_id = 'sv'
        else:
            axis_id = 'indel'
        chart_data.append({
            'xLabel1': row['variant_type'],
            'xLabel2': row['variant_size'],
            'tp': row['tp'],
            'fn': row['fn'],
            'fp': row['fp'] if 'fp' in row else -1,
            'recall': row['recall'],
            'precision': row['precision'] if 'precision' in row else -1,
            'axisId': axis_id,
        })
    return chart_data


class MetricsPlot():
    def __init__(self, metrics_table: MetricsTable):
        self._metrics_table = metrics_table

    def generate_snv_indel_sv_chart_data(self) -> List[Dict]:
        df = self._metrics_table.get_snv_indel_sv()
        return _generate_chart_data(df)

    def generate_sv_subtypes_chart_data(self) -> List[Dict]:
        df = self._metrics_table.get_sv_subtypes()
        return _generate_chart_data(df)

    def generate_sv_subtypes_sizes_chart_data(self) -> List[Dict]:
        df = self._metrics_table.get_sv_subtypes_sizes()
        return _generate_chart_data(df)
