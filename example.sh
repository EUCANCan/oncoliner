export EVALUATOR_COMMAND="python3 example/evaluator/src/main.py"
export IMPROVER_COMMAND="python3 example/improver/src/main.py"
export HARMONIZATOR_COMMAND="python3 example/harmonizator/src/main.py"

python3 src/main.py -c example/input/config.tsv -pf example/input/pipeline_1 -o example/output
