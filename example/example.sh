export UI_COMMAND="python3 ../modules/oncoliner_ui/src/main.py"
export ASSESMENT_COMMAND="python3 ../modules/oncoliner_assesment/src/assesment_bulk.py"
export IMPROVEMENT_COMMAND="python3 ../modules/oncoliner_improvement/src/improvement_main.py"
export HARMONIZATION_COMMAND="python3 ../modules/oncoliner_harmonization/src/harmonization_main.py"

python3 ../oncoliner_launcher.py -c ./example_config.tsv -cf input/callers_folder -pf ./input/pipeline_1 ./input/pipeline_2 -o ./output
