# Generate test
python3 generate.py --texttype synthetic --task cite2text    --output "basic_syn_c2t(20)"   --widthdepth "2,2;2,3;3,2"
python3 generate.py --texttype synthetic --task text2cite    --output "basic_syn_t2c(20)"   --widthdepth "2,2;2,3;3,2"
python3 generate.py --texttype synthetic --task cite2defined --output "basic_syn_c2def(20)" --widthdepth "2,2;2,3;3,2"
python3 generate.py --texttype synthetic --task defined2cite --output "basic_syn_def2c(20)" --widthdepth "2,2;2,3;3,2"
python3 generate.py --texttype synthetic --task appliesto    --output "basic_syn_a2(20)"    --widthdepth "2,2;2,3;3,2"
python3 generate.py --texttype uscode --task cite2text       --output "basic_usc_c2t(20)"   --mintokens 1000   --maxtokens 3000
python3 generate.py --texttype uscode --task text2cite       --output "basic_usc_t2c(20)"   --mintokens 1000   --maxtokens 3000
python3 generate.py --texttype uscode --task cite2defined    --output "basic_usc_c2def(20)" --mintokens 1000   --maxtokens 3000
python3 generate.py --texttype uscode --task defined2cite    --output "basic_usc_def2c(20)" --mintokens 1000   --maxtokens 3000
python3 generate.py --texttype transcript --task cite2text   --output "basic_trans_c2t(20)" --maxtokens 3000
python3 generate.py --texttype transcript --task text2cite   --output "basic_trans_t2c(20)" --maxtokens 3000
