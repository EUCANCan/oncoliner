mkdir -p output
python3 -O ../src/assessment_main.py -t ./input/truth/sample_1/*.vcf -v ./input/test/sample_1/*.vcf -f fake_ref.fa -o output/single_sample_example_ --no-gzip