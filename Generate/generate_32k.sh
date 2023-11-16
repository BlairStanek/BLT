maxtokens=25400
python3 generate.py --texttype synthetic --task cite2text           --seed 3 --output "BLT32k/test32k_syn_c2t(100);BLT32k/train32k_syn_c2t(1000)"      --maxtokens $maxtokens --widthdepth "3,6;4,5;6,4;12,3;11,3;44,2;40,2"
python3 generate.py --texttype synthetic --task text2cite           --seed 3 --output "BLT32k/test32k_syn_t2c(100);BLT32k/train32k_syn_t2c(1000)"      --maxtokens $maxtokens --widthdepth "3,6;4,5;6,4;12,3;11,3;44,2;40,2"
python3 generate.py --texttype synthetic --task cite2defined        --seed 3 --output "BLT32k/test32k_syn_c2def(100);BLT32k/train32k_syn_c2def(1000)"  --maxtokens $maxtokens --widthdepth "3,6;4,5;6,4;12,3;11,3;44,2;40,2"
python3 generate.py --texttype synthetic --task defined2cite        --seed 3 --output "BLT32k/test32k_syn_def2c(100);BLT32k/train32k_syn_def2c(1000)"  --maxtokens $maxtokens --widthdepth "3,6;4,5;6,4;12,3;11,3;44,2;40,2"
python3 generate.py --texttype uscode --task cite2text              --seed 3 --output "BLT32k/test32k_usc_c2t(100);BLT32k/train32k_usc_c2t(1000)"      --maxtokens $maxtokens --mintokens 4000
python3 generate.py --texttype uscode --task cite2amendedtext       --seed 3 --output "BLT32k/test32k_usc_c2amt(100);BLT32k/train32k_usc_c2amt(1000)"  --maxtokens $maxtokens --mintokens 4000
python3 generate.py --texttype uscode --task text2cite              --seed 3 --output "BLT32k/test32k_usc_t2c(100);BLT32k/train32k_usc_t2c(1000)"      --maxtokens $maxtokens --mintokens 4000
python3 generate.py --texttype uscode --task cite2defined           --seed 3 --output "BLT32k/test32k_usc_c2def(100);BLT32k/train32k_usc_c2def(1000)"  --maxtokens $maxtokens --mintokens 4000
python3 generate.py --texttype uscode --task defined2cite           --seed 3 --output "BLT32k/test32k_usc_def2c(100);BLT32k/train32k_usc_def2c(1000)"  --maxtokens $maxtokens --mintokens 4000
python3 generate.py --texttype transcript --task cite2text          --seed 3 --output "BLT32k/test32k_trans_c2t(100);BLT32k/train32k_trans_c2t(1000)"  --maxtokens $maxtokens --numpages "30,60,80"
python3 generate.py --texttype transcript --task text2cite          --seed 3 --output "BLT32k/test32k_trans_t2c(100);BLT32k/train32k_trans_t2c(1000)"  --maxtokens $maxtokens --numpages "30,60,80"
