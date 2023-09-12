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


class MetricsTable():
    def __init__(self, csv_path: str, table_types: Optional[List[str]] = None):
        self._df = pd.read_csv(csv_path)
        # Round all floats to 2 decimals
        self._df = self._df.round(2)
        self._indel_threshold = int(self._df[self._df['variant_type'] == 'INDEL']
                                    ['variant_size'].iloc[0].split('-')[-1].strip())
        self.columns_to_drop = _get_columns_to_drop(table_types) if table_types else []
        self.columns_to_drop.append('window_radius')

    def get_df(self):
        return self._df.drop(columns=self.columns_to_drop, errors='ignore').fillna('')

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
        # TODO: What about INS?
        # Find variant types with truth variants == 0 (TP + FN == 0)
        no_truth = set(df[df['tp'] + df['fn'] == 0]['variant_type'].tolist())
        warning_dict['no_truth'] = sorted(list(no_truth))
        # Find variant types with predicted variants == 0 (TP + FP == 0)ç
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
        print(warning_dict)
        return warning_dict
