maxtokens=3000
python3 generate.py --texttype synthetic --task cite2text         --output "BLT4k/test4k_syn_c2t(100)  ;BLT4k/train4k_syn_c2t(1000)"    --maxtokens $maxtokens --widthdepth "2,2;2,3;2,4;2,5;3,2;3,3;3,4;4,2;4,3"
python3 generate.py --texttype synthetic --task text2cite         --output "BLT4k/test4k_syn_t2c(100)  ;BLT4k/train4k_syn_t2c(1000)"    --maxtokens $maxtokens --widthdepth "2,2;2,3;2,4;2,5;3,2;3,3;3,4;4,2;4,3"
python3 generate.py --texttype synthetic --task cite2defined      --output "BLT4k/test4k_syn_c2def(100);BLT4k/train4k_syn_c2def(1000)"  --maxtokens $maxtokens --widthdepth "2,2;2,3;2,4;2,5;3,2;3,3;3,4;4,2;4,3"
python3 generate.py --texttype synthetic --task defined2cite      --output "BLT4k/test4k_syn_def2c(100);BLT4k/train4k_syn_def2c(1000)"  --maxtokens $maxtokens --widthdepth "2,2;2,3;2,4;2,5;3,2;3,3;3,4;4,2;4,3"
python3 generate.py --texttype uscode --task cite2text            --output "BLT4k/test4k_usc_c2t(100)  ;BLT4k/train4k_usc_c2t(1000)"    --maxtokens $maxtokens --mintokens 1000
python3 generate.py --texttype uscode --task cite2amendedtext     --output "BLT4k/test4k_usc_c2amt(100);BLT4k/train4k_usc_c2amt(1000)"  --maxtokens $maxtokens --mintokens 1000
python3 generate.py --texttype uscode --task text2cite            --output "BLT4k/test4k_usc_t2c(100)  ;BLT4k/train4k_usc_t2c(1000)"    --maxtokens $maxtokens --mintokens 1000
python3 generate.py --texttype uscode --task cite2defined         --output "BLT4k/test4k_usc_c2def(100);BLT4k/train4k_usc_c2def(1000)"  --maxtokens $maxtokens --mintokens 1000
python3 generate.py --texttype uscode --task defined2cite         --output "BLT4k/test4k_usc_def2c(100);BLT4k/train4k_usc_def2c(1000)"  --maxtokens $maxtokens --mintokens 1000
python3 generate.py --texttype transcript --task cite2text        --output "BLT4k/test4k_trans_c2t(100);BLT4k/train4k_trans_c2t(1000)"  --maxtokens $maxtokens --numpages "1,2"
python3 generate.py --texttype transcript --task text2cite        --output "BLT4k/test4k_trans_t2c(100);BLT4k/train4k_trans_t2c(1000)"  --maxtokens $maxtokens --numpages "1,2"
