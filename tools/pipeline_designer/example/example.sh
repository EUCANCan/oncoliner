
export ASSESMENT_COMMAND='python3 ../../../modules/oncoliner_assesment/src/assesment_bulk.py'
python3 ../src/main.py -t ./input/truth -v ./input/test -o ./output \
    -f  ./fake_ref.fa \
    -rs sample_1 \
    -ps sample_2 \
    -p 32 \
    --max-combinations 5 \
    --no-gzip
