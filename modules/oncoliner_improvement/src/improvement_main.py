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
    parser.add_argument('-lm', '--loss-margin', type=float, default=0.05,
                        help='Maximum performance loss in a metric to consider a recommendation (default: 0.05). '\
                        'A value of 0.05 means that a recommendation will be provided if the performance loss (in any metric) is less than 5%% over the baseline, '\
                        'provided that --gain-margin is also satisfied. '\
                        'Increasing this value will increase the number of recommendations and execution time')
    parser.add_argument('-gm', '--gain-margin', type=float, default=0.05,
                        help='Minimum performance gain in a metric to consider a recommendation (default: 0.05). '\
                        'A value of 0.05 means that a recommendation will be provided if the performance gain (in any metric) is greater than 5%% over the baseline, '\
                        'provided that --loss-margin is also satisfied. '\
                        'Increasing this value will reduce the number of recommendations and execution time')
    parser.add_argument('-mr', '--max-recommendations', type=float, default=1,
                        help='Maximun number of recommendations to provide for each performance metric per variant type and size and number of variant callers added (default: 1). Set to -1 to provide all recommendations')
    parser.add_argument('-wr', '--window-radius',
                        help='Window radius used for the evaluation. It will be inferred automatically by default', type=int)
    parser.add_argument('-p', '--processes', type=int, default=1, help='Number of processes to use (default: 1)')
    args = parser.parse_args()

    main(args.evaluation_results, args.callers_folder, args.output, args.recall_samples, args.precision_samples,
         args.loss_margin, args.gain_margin, args.max_recommendations, args.window_radius, args.processes)
