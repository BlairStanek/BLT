maxtokens=6200
python3 generate.py --texttype synthetic --task cite2text           --seed 1 --output "BLT8k/test8k_syn_c2t(100);BLT8k/train8k_syn_c2t(1000)"      --maxtokens $maxtokens --widthdepth "2,6;3,5;4,4;7,3;20,2"
python3 generate.py --texttype synthetic --task text2cite           --seed 1 --output "BLT8k/test8k_syn_t2c(100);BLT8k/train8k_syn_t2c(1000)"      --maxtokens $maxtokens --widthdepth "2,6;3,5;4,4;7,3;20,2"
python3 generate.py --texttype synthetic --task cite2defined        --seed 1 --output "BLT8k/test8k_syn_c2def(100);BLT8k/train8k_syn_c2def(1000)"  --maxtokens $maxtokens --widthdepth "2,6;3,5;4,4;7,3;20,2"
python3 generate.py --texttype synthetic --task defined2cite        --seed 1 --output "BLT8k/test8k_syn_def2c(100);BLT8k/train8k_syn_def2c(1000)"  --maxtokens $maxtokens --widthdepth "2,6;3,5;4,4;7,3;20,2"
python3 generate.py --texttype uscode --task cite2text              --seed 1 --output "BLT8k/test8k_usc_c2t(100);BLT8k/train8k_usc_c2t(1000)"      --maxtokens $maxtokens --mintokens 1500
python3 generate.py --texttype uscode --task cite2amendedtext       --seed 1 --output "BLT8k/test8k_usc_c2amt(100);BLT8k/train8k_usc_c2amt(1000)"  --maxtokens $maxtokens --mintokens 1500
python3 generate.py --texttype uscode --task text2cite              --seed 1 --output "BLT8k/test8k_usc_t2c(100);BLT8k/train8k_usc_t2c(1000)"      --maxtokens $maxtokens --mintokens 1500
python3 generate.py --texttype uscode --task cite2defined           --seed 1 --output "BLT8k/test8k_usc_c2def(100);BLT8k/train8k_usc_c2def(1000)"  --maxtokens $maxtokens --mintokens 1500
python3 generate.py --texttype uscode --task defined2cite           --seed 1 --output "BLT8k/test8k_usc_def2c(100);BLT8k/train8k_usc_def2c(1000)"  --maxtokens $maxtokens --mintokens 1500
python3 generate.py --texttype transcript --task cite2text          --seed 1 --output "BLT8k/test8k_trans_c2t(100);BLT8k/train8k_trans_c2t(1000)"  --maxtokens $maxtokens --numpages "5,10,15"
python3 generate.py --texttype transcript --task text2cite          --seed 1 --output "BLT8k/test8k_trans_t2c(100);BLT8k/train8k_trans_t2c(1000)"  --maxtokens $maxtokens --numpages "5,10,15"
