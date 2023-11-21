echo "Running with model "$1
echo "Running tests for BLT"$2

# Deposition Transcript Tests
python3 answer_is_cite.py  --infile ../Data/BLT${2}/test${2}_trans_t2c.jsonl --model $1 --verbose
python3 answer_is_text.py  --infile ../Data/BLT${2}/test${2}_trans_c2t.jsonl --model $1 --verbose

# Synthetic Section Tests
python3 answer_is_cite.py  --infile ../Data/BLT${2}/test${2}_syn_t2c.jsonl --model $1 --verbose
python3 answer_is_text.py  --infile ../Data/BLT${2}/test${2}_syn_c2t.jsonl --model $1 --verbose
python3 answer_is_cite.py  --infile ../Data/BLT${2}/test${2}_syn_def2c.jsonl --model $1 --verbose
python3 answer_is_text.py  --infile ../Data/BLT${2}/test${2}_syn_c2def.jsonl --model $1 --verbose

# U.S. Code Tests
python3 answer_is_cite.py  --infile ../Data/BLT${2}/test${2}_usc_t2c.jsonl --model $1 --verbose
python3 answer_is_text.py  --infile ../Data/BLT${2}/test${2}_usc_c2t.jsonl --model $1 --verbose
python3 answer_is_text.py  --infile ../Data/BLT${2}/test${2}_usc_c2amt.jsonl --model $1 --verbose
python3 answer_is_cite.py  --infile ../Data/BLT${2}/test${2}_usc_def2c.jsonl --model $1 --verbose
python3 answer_is_text.py  --infile ../Data/BLT${2}/test${2}_usc_c2def.jsonl --model $1 --verbose
