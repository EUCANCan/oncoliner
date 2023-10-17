import argparse
from vcf_ops.i_o import read_vcfs, write_masked_vcfs
from vcf_ops.constants import DEFAULT_INDEL_THRESHOLD, DEFAULT_WINDOW_RADIUS
from vcf_ops.union import union

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Union two sets of VCF/BCF/VCF.GZ files')
    parser.add_argument('--files-1', nargs='+', required=True, help='VCF/BCF/VCF.GZ files from the first set')
    parser.add_argument('--files-2', nargs='+', required=True, help='VCF/BCF/VCF.GZ files from the second set')
    parser.add_argument('-o', '--output', help='Prefix path for the output VCF files', required=True, type=str)
    parser.add_argument('-it', '--indel-threshold',
                        help=f'Indel threshold, inclusive (default={DEFAULT_INDEL_THRESHOLD})', default=DEFAULT_INDEL_THRESHOLD, type=int)
    parser.add_argument('-wr', '--window-radius',
                        help=f'Window radius (default={DEFAULT_WINDOW_RADIUS})', default=DEFAULT_WINDOW_RADIUS, type=float)
    args = parser.parse_args()

    # Read the input files
    df_truth = read_vcfs(args.files_1)
    df_test = read_vcfs(args.files_2)

    # Union
    df_union, df_union_dup = union(df_truth, df_test, args.indel_threshold, args.window_radius)

    # Write VCF files
    if len(df_union) > 0:
        write_masked_vcfs(df_union, args.output + 'union.', args.indel_threshold)
        print(f'Union VCF file written to {args.output}union.*')
    if len(df_union_dup):
        write_masked_vcfs(df_union_dup, args.output + 'union_dup.', args.indel_threshold)
        print(f'Union duplicate VCF file written to {args.output}union_dup.*')
