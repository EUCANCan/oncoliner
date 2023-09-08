import argparse

from harmonizator.harmonizator import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Harmonizator')
    parser.add_argument('-i', '--input-pipelines-improvements', type=str, required=True,
                        nargs='+', help='Paths to each pipeline improvement folder')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output folder')
    parser.add_argument('-wr', '--window-radius',
                        help='Window radius used for the evaluation. It will be inferred automatically by default.', type=int)
    parser.add_argument('-p', '--processes', help='Number of CPU processes', type=int, default=1)

    args = parser.parse_args()

    main(args.input_pipelines_improvements, args.output, args.window_radius, args.processes)
