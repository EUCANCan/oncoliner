export UI_COMMAND="python3 ../modules/oncoliner_ui/src/main.py"
export ASSESMENT_COMMAND="python3 ../modules/oncoliner_assesment/src/assesment_bulk.py"
export IMPROVEMENT_COMMAND="python3 ../modules/oncoliner_improvement/src/improvement_main.py"
export HARMONIZATION_COMMAND="python3 ../modules/oncoliner_harmonization/src/harmonization_main.py"

python3 src/main.py -c example/input/config.tsv -cf example/callers_folder -pf example/input/pipeline_1 example/input/pipeline_2 -o example/output
