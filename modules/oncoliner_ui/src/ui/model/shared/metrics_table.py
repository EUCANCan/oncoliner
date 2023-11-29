from typing import List, Optional
import pandas as pd


PRECISION_DEPENDENT_COLUMNS = ['fp', 'precision', 'f1_score']
PRECISION_THRESHOLD = 0.05
RECALL_THRESHOLD = 0.05


def _get_columns_to_drop(table_types: List[str]) -> List[str]:
    columns_to_drop = set()
    if 'precision' not in table_types:
        columns_to_drop.update(PRECISION_DEPENDENT_COLUMNS)
    return list(columns_to_drop)

def read_csv(csv_path: str, columns_to_drop: List[str] = []):
    # Read the first line to get the column names
    test_df = pd.read_csv(csv_path, nrows=1)
    # Remove nedded columns
    columns_to_drop_set = set(columns_to_drop)
    columns_to_drop_set.add('window_radius')
    # Drop all columns that end with _genes and window_radius
    columns_to_drop_set.update([col for col in test_df.columns if col.endswith('_genes')])
    used_columns = [col for col in test_df.columns if col not in columns_to_drop_set]
    # Read the whole csv
    return pd.read_csv(csv_path, usecols=used_columns).round(2)


class MetricsTable():
    def __init__(self, csv_path: str, table_types: Optional[List[str]] = None):
        columns_to_drop = _get_columns_to_drop(table_types) if table_types else []
        self._df = read_csv(csv_path, columns_to_drop)
        self._indel_threshold = int(self._df[self._df['variant_type'] == 'INDEL']
                                    ['variant_size'].iloc[0].split('-')[-1].strip())

    def get_df(self):
        return self._df

    def get_snv_indel_sv(self):
        snv_mask = (self._df['variant_type'] == 'SNV')
        indel_mask = (self._df['variant_type'] == 'INDEL')
        sv_mask = (self._df['variant_type'] == 'SV')
        return self.get_df()[snv_mask | indel_mask | sv_mask]

    def get_sv_subtypes(self):
        snv_mask = (self._df['variant_type'] == 'SNV')
        indel_mask = (self._df['variant_type'] == 'INDEL')
        inv_mask = ((self._df['variant_type'] == 'INV') & (self._df['variant_size'] == '> 0'))
        del_mask = ((self._df['variant_type'] == 'DEL') & (self._df['variant_size'] == f'> {self._indel_threshold}'))
        ins_mask = ((self._df['variant_type'] == 'INS') & (self._df['variant_size'] == f'> {self._indel_threshold}'))
        dup_mask = ((self._df['variant_type'] == 'DUP') & (self._df['variant_size'] == f'> {self._indel_threshold}'))
        tra_mask = (self._df['variant_type'] == 'TRA')
        return self.get_df()[snv_mask | indel_mask | inv_mask | del_mask | ins_mask | dup_mask | tra_mask]

    def get_sv_subtypes_sizes(self):
        snv_mask = (self._df['variant_type'] == 'SNV')
        indel_mask = (self._df['variant_type'] == 'INDEL')
        inv_mask = ((self._df['variant_type'] == 'INV') & (self._df['variant_size'] != '> 0'))
        ins_mask = ((self._df['variant_type'] == 'INS') & (self._df['variant_size'] != f'> {self._indel_threshold}'))
        del_mask = ((self._df['variant_type'] == 'DEL') & (self._df['variant_size'] != f'> {self._indel_threshold}') &
                    (self._df['variant_size'] != f'1 - {self._indel_threshold}'))
        dup_mask = ((self._df['variant_type'] == 'DUP') & (self._df['variant_size'] != f'> {self._indel_threshold}'))
        tra_mask = (self._df['variant_type'] == 'TRA')
        return self.get_df()[snv_mask | indel_mask | inv_mask | del_mask | ins_mask | dup_mask | tra_mask]

    def get_warnings(self):
        df = self.get_sv_subtypes()
        warning_dict = dict()
        # Find variant types with truth variants == 0 (TP + FN == 0)
        no_truth = set(df[df['tp'] + df['fn'] == 0]['variant_type'].tolist())
        if len(no_truth) > 0:
            warning_dict['no_truth'] = sorted(list(no_truth))
        # Find variant types with predicted variants == 0 (TP + FP == 0)
        no_predicted = set()
        if 'fp' in df.columns:
            no_predicted = set(df[df['tp'] + df['fp'] == 0]['variant_type'].tolist())
            no_predicted_total = no_predicted - no_truth
            if len(no_predicted_total) > 0:
                warning_dict['no_predicted'] = sorted(list(no_predicted_total))
        # Find variant types with precision < PRECISION_THRESHOLD
        if 'precision' in df.columns:
            low_precision = set(df[df['precision'] < PRECISION_THRESHOLD]['variant_type'].tolist())
            low_precision_total = low_precision - no_truth - no_predicted
            if len(low_precision_total) > 0:
                warning_dict['low_precision'] = sorted(list(low_precision_total))
        # Find variant types with recall < RECALL_THRESHOLD
        low_recall = set(df[df['recall'] < PRECISION_THRESHOLD]['variant_type'].tolist())
        low_recall_total = low_recall - no_truth - no_predicted
        if len(low_recall_total) > 0:
            warning_dict['low_recall'] = sorted(list(low_recall_total))
        return warning_dict
