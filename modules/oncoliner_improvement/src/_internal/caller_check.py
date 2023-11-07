import os
import glob
import logging
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from vcf_ops.i_o import read_vcfs, write_masked_vcfs  # noqa
from vcf_ops.intersect import intersect  # noqa
from vcf_ops.union import union  # noqa
from vcf_ops.metrics import compute_metrics, aggregate_metrics  # noqa
from .common import build_result_dataframe, INTERSECTION_SYMBOL, UNION_SYMBOL  # noqa

MIN_RECALL = 0.05


def _caller_metrics_mask(caller_samples_folder, recall_samples, precision_samples):
    # Get all metrics files from the caller in the samples folder
    metrics_files = []
    for sample in precision_samples + recall_samples:
        metrics_files.extend(glob.glob(os.path.join(caller_samples_folder, sample, '*metrics.csv')))
    # Aggregate metrics
    metrics_df = aggregate_metrics([pd.read_csv(f) for f in metrics_files])
    # Return the variant types that have at least one TP
    return metrics_df['recall'] > MIN_RECALL


def _caller_masked_variants(df, masked_metrics):
    final_mask = pd.Series(False, index=df.index)
    for _, row in masked_metrics.iterrows():
        variant_type = row['variant_type']
        if variant_type == 'INDEL' or variant_type == 'SV':
            continue
        else:
            if '/' in variant_type:
                variant_type_1, variant_type_2 = variant_type.split('/')
                current_mask = (df['type_inferred'] == variant_type_1) | (df['type_inferred'] == variant_type_2)
            else:
                current_mask = df['type_inferred'] == variant_type
            if '>' in row['variant_size']:
                variant_size = int(row['variant_size'].replace('>', '').strip())
                current_mask &= df['length'] > variant_size
            elif '-' in row['variant_size']:
                variant_size_1, variant_size_2 = row['variant_size'].split('-')
                variant_size_1 = int(variant_size_1.strip())
                variant_size_2 = int(variant_size_2.strip())
                current_mask &= (df['length'] >= variant_size_1) & (df['length'] <= variant_size_2)
            final_mask |= current_mask
    return final_mask


def _execute_intersection(user_sample_folder, caller_sample_folder, indel_threshold, window_radius, sv_size_bins, variant_types):
    # Read TP files
    tp_user_path = glob.glob(os.path.join(user_sample_folder, '*tp.*'))
    tp_df_user = read_vcfs(tp_user_path)
    tp_caller_path = glob.glob(os.path.join(caller_sample_folder, '*tp.*'))
    tp_df_caller = read_vcfs(tp_caller_path)
    # Intersect TP files
    tp_df_tp, _, _, _, tp_df_fn, _ = \
        intersect(tp_df_caller, tp_df_user, indel_threshold, window_radius, True)

    # Read FP files
    fp_user_path = glob.glob(os.path.join(user_sample_folder, '*fp.*'))
    fp_df_user = read_vcfs(fp_user_path)
    fp_caller_path = glob.glob(os.path.join(caller_sample_folder, '*fp.*'))
    fp_df_caller = read_vcfs(fp_caller_path)
    # Intersect FP files
    fp_df_tp, _, _, _, _, _ = \
        intersect(fp_df_caller, fp_df_user, indel_threshold, window_radius, False)

    # Read FN files
    fn_user_path = glob.glob(os.path.join(user_sample_folder, '*fn.*'))
    fn_df_user = read_vcfs(fn_user_path)

    # Construct output dataframes
    df_tp = tp_df_tp
    df_fp = fp_df_tp
    df_fn = pd.concat([tp_df_fn, fn_df_user], ignore_index=True)

    # Calculate metrics
    metrics = compute_metrics(df_tp, df_fp, df_fn, indel_threshold, window_radius, sv_size_bins, variant_types)

    def save_results_vcfs(output_folder, caller_mask):
        masked_metrics = metrics[caller_mask]
        # Save TP
        df_tp_baseline = tp_df_user[~_caller_masked_variants(tp_df_user, masked_metrics)]
        df_tp_concat = pd.concat([df_tp_baseline, df_tp], ignore_index=True)
        write_masked_vcfs(df_tp_concat, os.path.join(output_folder, 'tp.'), indel_threshold)
        # Save FP
        df_fp_baseline = fp_df_user[~_caller_masked_variants(fp_df_user, masked_metrics)]
        df_fp_concat = pd.concat([df_fp_baseline, df_fp], ignore_index=True)
        write_masked_vcfs(df_fp_concat, os.path.join(output_folder, 'fp.'), indel_threshold)
        # Save FN
        write_masked_vcfs(df_fn, os.path.join(output_folder, 'fn.'), indel_threshold)
        # Save metrics
        concat_metrics = compute_metrics(df_tp_concat, df_fp_concat, df_fn,
                                         indel_threshold, window_radius, sv_size_bins, variant_types)
        concat_metrics.to_csv(os.path.join(output_folder, 'metrics.csv'), index=False)

    return metrics, save_results_vcfs


def _execute_union(user_sample_folder, caller_sample_folder, indel_threshold, window_radius, sv_size_bins, variant_types):
    # Read TP files
    tp_user_path = glob.glob(os.path.join(user_sample_folder, '*tp.*'))
    tp_df_user = read_vcfs(tp_user_path)
    tp_caller_path = glob.glob(os.path.join(caller_sample_folder, '*tp.*'))
    tp_df_caller = read_vcfs(tp_caller_path)
    # Union TP files
    tp_df_tp, _ = union(tp_df_caller, tp_df_user, indel_threshold, window_radius)

    # Read FP files
    fp_user_path = glob.glob(os.path.join(user_sample_folder, '*fp.*'))
    fp_df_user = read_vcfs(fp_user_path)
    fp_caller_path = glob.glob(os.path.join(caller_sample_folder, '*fp.*'))
    fp_df_caller = read_vcfs(fp_caller_path)
    # Union FP files
    fp_df_tp, _ = union(fp_df_caller, fp_df_user, indel_threshold, window_radius)

    # Read FN files
    fn_user_path = glob.glob(os.path.join(user_sample_folder, '*fn.*'))
    fn_df_user = read_vcfs(fn_user_path)
    fn_df_caller = read_vcfs(glob.glob(os.path.join(caller_sample_folder, '*fn.*')))
    # Intersect FN files
    fn_df_tp, _, _, _, _, _ = \
        intersect(fn_df_caller, fn_df_user, indel_threshold, window_radius, False)

    # Construct output dataframes
    df_tp = tp_df_tp
    df_fp = fp_df_tp
    df_fn = fn_df_tp

    # Calculate metrics
    metrics = compute_metrics(df_tp, df_fp, df_fn, indel_threshold, window_radius, sv_size_bins, variant_types)

    def save_results_vcfs(output_folder, _):
        # Save TP
        write_masked_vcfs(df_tp, os.path.join(output_folder, 'tp.'), indel_threshold)
        # Save FP
        write_masked_vcfs(df_fp, os.path.join(output_folder, 'fp.'), indel_threshold)
        # Save FN
        write_masked_vcfs(df_fn, os.path.join(output_folder, 'fn.'), indel_threshold)
        # Save metrics
        metrics.to_csv(os.path.join(output_folder, 'metrics.csv'), index=False)

    return metrics, save_results_vcfs


class CallerChecker:
    def __init__(self, results_output_folder, num_processes, baseline_metrics, caller_folder, user_folder, recall_samples, precision_samples, loss_margin, gain_margin):
        self.__results_output_folder = results_output_folder
        self.__caller_samples_folder = os.path.join(caller_folder, 'samples')
        self.__caller_name = os.path.basename(caller_folder)
        self.__recall_samples = recall_samples
        self.__precision_samples = precision_samples
        self.__loss_margin = loss_margin
        self.__gain_margin = gain_margin
        self.__user_folder = os.path.join(user_folder, 'samples')
        self.__baseline_metrics = baseline_metrics
        self.__caller_mask = _caller_metrics_mask(self.__caller_samples_folder, self.__recall_samples, self.__precision_samples)
        self.__num_processes = num_processes
        if num_processes > 1:
            self.__pool = ThreadPoolExecutor(num_processes)

    def _execute_operation(self, op, sample_names, indel_threshold, window_radius, sv_size_bins, variant_types):
        # Iterate over samples
        if self.__num_processes > 1:
            results = self.__pool.map(lambda p: op(*p), [(
                os.path.join(self.__user_folder, sample),
                os.path.join(self.__caller_samples_folder, sample), indel_threshold, window_radius, sv_size_bins, variant_types)
                for sample in sample_names])
            results = list(results)
        else:
            results = []
            for sample in sample_names:
                results.append(op(
                    os.path.join(self.__user_folder, sample),
                    os.path.join(self.__caller_samples_folder, sample), indel_threshold, window_radius, sv_size_bins, variant_types))

        def save_vcf_results(output_folder):
            samples_output_folder = os.path.join(output_folder, 'samples')
            for sample, (_, save_results) in zip(sample_names, results):
                # Save results to file
                sample_output_folder = os.path.join(samples_output_folder, sample)
                os.makedirs(sample_output_folder, exist_ok=True)
                save_results(sample_output_folder, self.__caller_mask)

        # Get metrics
        metrics_list = [r[0] for r in results]
        # Aggregate metrics
        new_metrics = aggregate_metrics(metrics_list)
        return new_metrics, save_vcf_results

    def _save_results(self, output_file, results_df, baseline_metrics):
        # Build the results dataframe filling in the baseline metrics
        for idx, row in baseline_metrics.iterrows():
            if idx not in results_df.index:
                results_df.loc[idx] = row
        results_df.sort_index(inplace=True)
        # Save the results
        results_df.to_csv(output_file, index=False)

    def _execute_union_check(self, **kwargs):
        # Check union performance on the precision samples
        union_precision_metrics, save_vcf_results_precision = \
            self._execute_operation(_execute_union, self.__precision_samples, **kwargs)
        # Get the rows where the caller union precision is not worse than baseline in caller_mask
        union_viable = (union_precision_metrics['precision'] >=
                        self.__baseline_metrics['precision'] - self.__loss_margin) & self.__caller_mask
        if not union_viable.any():
            return None
        # Check recall performance
        union_recall_metrics, save_vcf_results_recall = \
            self._execute_operation(_execute_union, self.__recall_samples, **kwargs)
        # Get the rows where the caller union recall is better than baseline in union_viable
        union_better = (union_recall_metrics['recall'] > self.__baseline_metrics['recall'] + self.__gain_margin) & union_viable
        if not union_better.any():
            return None
        return union_precision_metrics, union_recall_metrics, save_vcf_results_precision, save_vcf_results_recall

    def _execute_intersection_check(self, **kwargs):
        # Check intersection performance on the recall samples
        intersection_recall_metrics, save_vcf_results_recall = \
            self._execute_operation(_execute_intersection, self.__recall_samples, **kwargs)
        # Get the rows where the caller intersection recall is not worse than baseline in caller_mask
        intersection_viable = (intersection_recall_metrics['recall'] >=
                               self.__baseline_metrics['recall'] - self.__loss_margin) & self.__caller_mask
        if not intersection_viable.any():
            return None
        # Check precision performance
        intersection_precision_metrics, save_vcf_results_precision = \
            self._execute_operation(_execute_intersection, self.__precision_samples, **kwargs)
        # Get the rows where the caller intersection precision is better than baseline in intersection_viable
        intersection_better = (intersection_precision_metrics['precision'] >
                               self.__baseline_metrics['precision'] + self.__gain_margin) & intersection_viable
        if not intersection_better.any():
            return None
        return intersection_precision_metrics, intersection_recall_metrics, save_vcf_results_precision, save_vcf_results_recall

    def execute(self, **kwargs):
        # Check for union performance
        union_operation_name = f'baseline{UNION_SYMBOL}{self.__caller_name}'
        intersection_operation_name = f'baseline{INTERSECTION_SYMBOL}{self.__caller_name}'
        for operation_name, op in zip([union_operation_name, intersection_operation_name], [self._execute_union_check, self._execute_intersection_check]):
            # Avoid the operation if operation_name.done exists
            output_flag_file = os.path.join(self.__results_output_folder, operation_name + '.done')
            # Avoid the operation if already done, that is, if the aggregated metrics file exists and is not empty
            output_folder = os.path.join(self.__results_output_folder, operation_name)
            agg_file = os.path.join(output_folder, 'aggregated_metrics.csv')
            if os.path.exists(output_flag_file) or (os.path.exists(agg_file) and os.path.getsize(agg_file) > 0):
                logging.info(f'Skipping {operation_name} computation because it was already done')
                continue
            output = op(**kwargs)
            if output is None:
                # Write a file with the operation name to avoid repeating the operation
                with open(output_flag_file, 'w') as f:
                    f.write('')
                continue
            precision_metrics, recall_metrics, save_vcf_results_precision, save_vcf_results_recall = output
            # Build the output dataframe
            result_df = build_result_dataframe(operation_name, self.__caller_mask, precision_metrics, recall_metrics)
            # Save the results to file
            os.makedirs(output_folder, exist_ok=True)
            self._save_results(agg_file, result_df, self.__baseline_metrics)
            save_vcf_results_precision(output_folder)
            save_vcf_results_recall(output_folder)


def execute_caller_check(results_output_folder, num_processes, baseline_metrics,
                         caller_folder, user_folder, recall_samples, precision_samples, loss_margin, gain_margin, **kwargs):
    caller_checker = CallerChecker(results_output_folder, num_processes, baseline_metrics,
                                   caller_folder, user_folder, recall_samples, precision_samples, loss_margin, gain_margin)
    caller_checker.execute(**kwargs)
