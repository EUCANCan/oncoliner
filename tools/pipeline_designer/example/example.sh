export ASSESMENT_COMMAND='python3 ../../../modules/oncoliner_assesment/src/assesment_bulk.py'
python3 ../src/main.py -c ./example_config.tsv -vc ./input/test -o ./output \
    -p 4 \
    --max-combinations 5 \
    --no-gzip
