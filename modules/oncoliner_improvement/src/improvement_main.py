import argparse

from _internal.recommendator import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ONCOLINER Improvement')
    parser.add_argument('-e', '--evaluation-results', type=str, required=True,
                        help='Pipeline evaluation results folder path')
    parser.add_argument('-c', '--callers-folder', type=str, required=True, help='Callers folder path')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output folder path')
    parser.add_argument('-rs', '--recall-samples', type=str, required=True, nargs='+', help='Recall samples names')
    parser.add_argument('-ps', '--precision-samples', type=str, required=True,
                        nargs='+', help='Precision samples names')
    parser.add_argument('-lm', '--loss-margin', type=float, default=0.05, help='Loss margin for the improvement')
    parser.add_argument('-wr', '--window-radius',
                        help='Window radius used for the evaluation. It will be inferred automatically by default', type=int)
    parser.add_argument('-p', '--processes', type=int, default=1, help='Number of processes to use')
    args = parser.parse_args()

    main(args.evaluation_results, args.callers_folder, args.output, args.recall_samples, args.precision_samples,
         args.loss_margin, args.window_radius, args.processes)
