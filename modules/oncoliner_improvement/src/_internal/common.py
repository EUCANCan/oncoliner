import re

from vcf_ops.metrics import combine_precision_recall_metrics  # noqa

UNION_SYMBOL = '$or$'
INTERSECTION_SYMBOL = '$and$'
REMOVE_SYMBOL = '$not$'


def build_result_dataframe(operation, mask, precision_df, recall_df):
    df = combine_precision_recall_metrics(recall_df, precision_df)
    df = df[mask]
    added_callers = operation.count(UNION_SYMBOL) + operation.count(INTERSECTION_SYMBOL)
    removed_callers = operation.count(REMOVE_SYMBOL)
    df.insert(0, 'operation', operation)
    df['added_callers'] = added_callers
    df['removed_callers'] = removed_callers
    df['total_changed_callers'] = added_callers + removed_callers
    return df


def cleanup_text(path: str):
    special_chars_regex = r'[^a-zA-Z0-9]'
    return re.sub(special_chars_regex, '_', path)
