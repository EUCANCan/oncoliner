import argparse

from harmonizator.harmonizator import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Harmonizator')
    parser.add_argument('-i', '--input-pipelines-improvements', type=str, required=True,
                        nargs='+', help='Paths to each pipeline improvement folder')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output folder')
    parser.add_argument('-t', '--threads', help='Number of CPU threads', type=int, default=1)

    args = parser.parse_args()

    main(args.input_pipelines_improvements, args.output, args.threads)
