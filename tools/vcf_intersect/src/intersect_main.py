import argparse
import os
import sys

# Add vcf-ops to the path
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', '..', 'shared', 'vcf_ops', 'src'))
from vcf_ops.i_o import read_vcfs, write_masked_vcfs  # noqa
from vcf_ops.constants import DEFAULT_INDEL_THRESHOLD, DEFAULT_WINDOW_RADIUS  # noqa
from vcf_ops.intersect import intersect  # noqa

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Intersect two sets of VCF/BCF/VCF.GZ files')
    parser.add_argument('--files-1', nargs='+', required=True, help='VCF/BCF/VCF.GZ files from the first set')
    parser.add_argument('--files-2', nargs='+', required=True, help='VCF/BCF/VCF.GZ files from the second set')
    parser.add_argument('-o', '--output', help='Prefix path for the output VCF files', required=True, type=str)
    parser.add_argument('-it', '--indel-threshold',
                        help=f'Indel threshold, inclusive (default={DEFAULT_INDEL_THRESHOLD})', default=DEFAULT_INDEL_THRESHOLD, type=int)
    parser.add_argument('-wr', '--window-radius',
                        help=f'Window radius (default={DEFAULT_WINDOW_RADIUS})', default=DEFAULT_WINDOW_RADIUS, type=float)
    parser.add_argument('--combine-genes-annotations', action='store_true',
                        help='Combine genes and annotations from the input VCF files')
    args = parser.parse_args()

    # Read the input files
    df_truth = read_vcfs(args.files_1)
    df_test = read_vcfs(args.files_2)

    # Intersect
    df_tp, df_tp_dup, df_fp, df_fp_dup, df_fn, df_fn_dup = intersect(df_truth, df_test, args.indel_threshold, args.window_radius, args.combine_genes_annotations)

    # Write VCF files
    if len(df_tp) > 0:
        write_masked_vcfs(df_tp, args.output + 'intersect_in.', args.indel_threshold)
        print(f'True positives can be found in {args.output}intersect_in.*')
    if len(df_tp_dup) > 0:
        write_masked_vcfs(df_tp_dup, args.output + 'intersect_in_dup.', args.indel_threshold)
        print(f'True positives with duplicates can be found in {args.output}intersect_in_dup.*')
    if len(df_fp) > 0:
        write_masked_vcfs(df_fp, args.output + 'intersect_outside_2.', args.indel_threshold)
        print(f'False positives can be found in {args.output}intersect_outside_2.*')
    if len(df_fp_dup) > 0:
        write_masked_vcfs(df_fp_dup, args.output + 'intersect_outside_2_dup.',args.indel_threshold)
        print(f'False positives with duplicates can be found in {args.output}intersect_outside_2_dup.*')
    if len(df_fn) > 0:
        write_masked_vcfs(df_fn, args.output + 'intersect_outside_1.', args.indel_threshold)
        print(f'False negatives can be found in {args.output}intersect_out_1.*')
    if len(df_fn_dup) > 0:
        write_masked_vcfs(df_fn_dup, args.output + 'intersect_outside_1_dup.', args.indel_threshold)
        print(f'False negatives with duplicates can be found in {args.output}intersect_outside_1_dup.*')
