
export EVALUATOR_COMMAND='python3 ./example/variant-evaluator/src/variant_evaluator/main.py'
python3 src/main.py -t ./example/input/truth -v ./example/input/test -o ./example/output \
    -f  ./example/input/genome.fa \
    -rs PCAWG_pilot_1 PCAWG_pilot_2 \
    -ps PCAWG_pilot_2 \
    -p 32 \
    --max-combinations 5

