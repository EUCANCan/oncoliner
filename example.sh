export UI_COMMAND="python3 example/ui/src/main.py"
export EVALUATOR_COMMAND="python3 example/evaluator/src/wrapper.py"
export IMPROVER_COMMAND="python3 example/improver/src/main.py"
export HARMONIZATOR_COMMAND="python3 example/harmonizator/src/main.py"

python3 src/main.py -c example/input/config.tsv -cf example/callers_folder -pf example/input/pipeline_1 example/input/pipeline_2 -o example/output
