import argparse

from harmonizator.harmonizator import main

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Harmonizator')
    parser.add_argument('-i', '--input-pipelines-improvements', type=str, required=True,
                        nargs='+', help='Paths to each pipeline improvement folder')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output folder')
    parser.add_argument('-lm', '--loss-margin', type=float, default=0.05,
                        help='Maximum performance loss from the maximum in a metric to consider a recommendation (default: 0.05). '\
                        'A value of 0.05 means that a recommendation will be provided if the performance loss (in any metric) is less than 5%% over the maximum of all recommendations. '\
                        'Decreasing this value will decrease the number of recommendations after --max-recommendations is applied')
    parser.add_argument('-mr', '--max-recommendations', type=float, default=1,
                        help='Maximun number of recommendations to provide for each performance metric per variant type and size and number of variant callers added (default: 1). Set to -1 to provide all recommendations')
    parser.add_argument('-t', '--threads', help='Number of CPU threads', type=int, default=1)

    args = parser.parse_args()

    main(args.input_pipelines_improvements, args.output, args.loss_margin, args.max_recommendations, args.threads)
