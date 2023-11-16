maxtokens=102200
python3 generate.py --texttype synthetic --task cite2text           --seed 5 --output "BLT128k/test128k_syn_c2t(100);BLT128k/train128k_syn_c2t(1000)"      --maxtokens $maxtokens --widthdepth "5,5;4,6;8,4;9,4;20,3;80,2"
python3 generate.py --texttype synthetic --task text2cite           --seed 5 --output "BLT128k/test128k_syn_t2c(100);BLT128k/train128k_syn_t2c(1000)"      --maxtokens $maxtokens --widthdepth "5,5;4,6;8,4;9,4;20,3;80,2"
python3 generate.py --texttype synthetic --task cite2defined        --seed 5 --output "BLT128k/test128k_syn_c2def(100);BLT128k/train128k_syn_c2def(1000)"  --maxtokens $maxtokens --widthdepth "5,5;4,6;8,4;9,4;20,3;80,2"
python3 generate.py --texttype synthetic --task defined2cite        --seed 5 --output "BLT128k/test128k_syn_def2c(100);BLT128k/train128k_syn_def2c(1000)"  --maxtokens $maxtokens --widthdepth "5,5;4,6;8,4;9,4;20,3;80,2"
python3 generate.py --texttype uscode --task cite2text              --seed 5 --output "BLT128k/test128k_usc_c2t(100);BLT128k/train128k_usc_c2t(1000)"      --maxtokens $maxtokens --mintokens 7000
python3 generate.py --texttype uscode --task cite2amendedtext       --seed 5 --output "BLT128k/test128k_usc_c2amt(100);BLT128k/train128k_usc_c2amt(1000)"  --maxtokens $maxtokens --mintokens 7000
python3 generate.py --texttype uscode --task text2cite              --seed 5 --output "BLT128k/test128k_usc_t2c(100);BLT128k/train128k_usc_t2c(1000)"      --maxtokens $maxtokens --mintokens 7000
python3 generate.py --texttype uscode --task cite2defined           --seed 5 --output "BLT128k/test128k_usc_c2def(100);BLT128k/train128k_usc_c2def(1000)"  --maxtokens $maxtokens --mintokens 7000
python3 generate.py --texttype uscode --task defined2cite           --seed 5 --output "BLT128k/test128k_usc_def2c(100);BLT128k/train128k_usc_def2c(1000)"  --maxtokens $maxtokens --mintokens 7000
python3 generate.py --texttype transcript --task cite2text          --seed 5 --output "BLT128k/test128k_trans_c2t(100);BLT128k/train128k_trans_c2t(1000)"  --maxtokens $maxtokens --numpages "120,140"
python3 generate.py --texttype transcript --task text2cite          --seed 5 --output "BLT128k/test128k_trans_t2c(100);BLT128k/train128k_trans_t2c(1000)"  --maxtokens $maxtokens --numpages "120,140"
