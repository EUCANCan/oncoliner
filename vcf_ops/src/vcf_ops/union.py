# Copyright 2023 - Barcelona Supercomputing Center
# Author: Rodrigo Martín
# BSC Dual License
import pandas as pd

from .intersect import intersect


def union(df_truth, df_test, indel_threshold, window_radius):
    # Intersect
    df_tp, df_tp_dup, df_fp, df_fp_dup, df_fn, df_fn_dup = intersect(
        df_truth, df_test, indel_threshold, window_radius)

    # Union
    df_union = pd.concat([df_tp, df_fp, df_fn])
    df_union_dup = pd.concat([df_tp_dup, df_fp_dup, df_fn_dup])

    return df_union, df_union_dup


if __name__ == '__main__':
    import argparse
    from .i_o import read_vcfs, write_masked_vcfs
    from .constants import DEFAULT_INDEL_THRESHOLD, DEFAULT_WINDOW_RADIUS

    parser = argparse.ArgumentParser(description='Union two sets of VCF/BCF/VCF.GZ files')
    parser.add_argument('--truth-files', nargs='+', required=True, help='VCF/BCF/VCF.GZ files to use as truth')
    parser.add_argument('--test-files', nargs='+', required=True, help='VCF/BCF/VCF.GZ files to use as test')
    parser.add_argument('-o', '--output', help='Prefix path for the output VCF files', required=True, type=str)
    parser.add_argument('-it', '--indel-threshold',
                        help=f'Indel threshold, inclusive (default={DEFAULT_INDEL_THRESHOLD})', default=DEFAULT_INDEL_THRESHOLD, type=int)
    parser.add_argument('-wr', '--window-radius',
                        help=f'Window radius (default={DEFAULT_WINDOW_RADIUS})', default=DEFAULT_WINDOW_RADIUS, type=int)
    args = parser.parse_args()

    # Read the input files
    df_truth = read_vcfs(args.truth_files)
    df_test = read_vcfs(args.test_files)

    # Union
    df_union, df_union_dup = union(df_truth, df_test, args.indel_threshold, args.window_ratio, args.window_limit)

    # Write VCF files
    if len(df_union) > 0:
        write_masked_vcfs(df_union, args.output + 'union.', args.test_files, args.indel_threshold)
        print(f'Union VCF file written to {args.output}union.*')
    if len(df_union_dup):
        write_masked_vcfs(df_union_dup, args.output + 'union_dup.', args.test_files, args.indel_threshold)
        print(f'Union duplicate VCF file written to {args.output}union_dup.*')
