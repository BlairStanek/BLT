maxtokens=12600
python3 generate.py --texttype synthetic --task cite2text           --seed 2 --output "BLT16k/test16k_syn_c2t(100);BLT16k/train16k_syn_c2t(1000)"      --maxtokens $maxtokens --widthdepth "5,4;8,3;9,3;30,2"
python3 generate.py --texttype synthetic --task text2cite           --seed 2 --output "BLT16k/test16k_syn_t2c(100);BLT16k/train16k_syn_t2c(1000)"      --maxtokens $maxtokens --widthdepth "5,4;8,3;9,3;30,2"
python3 generate.py --texttype synthetic --task cite2defined        --seed 2 --output "BLT16k/test16k_syn_c2def(100);BLT16k/train16k_syn_c2def(1000)"  --maxtokens $maxtokens --widthdepth "5,4;8,3;9,3;30,2"
python3 generate.py --texttype synthetic --task defined2cite        --seed 2 --output "BLT16k/test16k_syn_def2c(100);BLT16k/train16k_syn_def2c(1000)"  --maxtokens $maxtokens --widthdepth "5,4;8,3;9,3;30,2"
python3 generate.py --texttype uscode --task cite2text              --seed 2 --output "BLT16k/test16k_usc_c2t(100);BLT16k/train16k_usc_c2t(1000)"      --maxtokens $maxtokens --mintokens 3000
python3 generate.py --texttype uscode --task cite2amendedtext       --seed 2 --output "BLT16k/test16k_usc_c2amt(100);BLT16k/train16k_usc_c2amt(1000)"  --maxtokens $maxtokens --mintokens 3000
python3 generate.py --texttype uscode --task text2cite              --seed 2 --output "BLT16k/test16k_usc_t2c(100);BLT16k/train16k_usc_t2c(1000)"      --maxtokens $maxtokens --mintokens 3000
python3 generate.py --texttype uscode --task cite2defined           --seed 2 --output "BLT16k/test16k_usc_c2def(100);BLT16k/train16k_usc_c2def(1000)"  --maxtokens $maxtokens --mintokens 3000
python3 generate.py --texttype uscode --task defined2cite           --seed 2 --output "BLT16k/test16k_usc_def2c(100);BLT16k/train16k_usc_def2c(1000)"  --maxtokens $maxtokens --mintokens 3000
python3 generate.py --texttype transcript --task cite2text          --seed 2 --output "BLT16k/test16k_trans_c2t(100);BLT16k/train16k_trans_c2t(1000)"  --maxtokens $maxtokens --numpages "25,40"
python3 generate.py --texttype transcript --task text2cite          --seed 2 --output "BLT16k/test16k_trans_t2c(100);BLT16k/train16k_trans_t2c(1000)"  --maxtokens $maxtokens --numpages "25,40"
