maxtokens=51000
python3 generate.py --texttype synthetic --task cite2text           --seed 4 --output "BLT64k/test64k_syn_c2t(100);BLT64k/train64k_syn_c2t(1000)"      --maxtokens $maxtokens --widthdepth "7,4;16,3;15,3;14,3;13,3;60,2;65,2"
python3 generate.py --texttype synthetic --task text2cite           --seed 4 --output "BLT64k/test64k_syn_t2c(100);BLT64k/train64k_syn_t2c(1000)"      --maxtokens $maxtokens --widthdepth "7,4;16,3;15,3;14,3;13,3;60,2;65,2"
python3 generate.py --texttype synthetic --task cite2defined        --seed 4 --output "BLT64k/test64k_syn_c2def(100);BLT64k/train64k_syn_c2def(1000)"  --maxtokens $maxtokens --widthdepth "7,4;16,3;15,3;14,3;13,3;60,2;65,2"
python3 generate.py --texttype synthetic --task defined2cite        --seed 4 --output "BLT64k/test64k_syn_def2c(100);BLT64k/train64k_syn_def2c(1000)"  --maxtokens $maxtokens --widthdepth "7,4;16,3;15,3;14,3;13,3;60,2;65,2"
python3 generate.py --texttype uscode --task cite2text              --seed 4 --output "BLT64k/test64k_usc_c2t(100);BLT64k/train64k_usc_c2t(1000)"      --maxtokens $maxtokens --mintokens 5000
python3 generate.py --texttype uscode --task cite2amendedtext       --seed 4 --output "BLT64k/test64k_usc_c2amt(100);BLT64k/train64k_usc_c2amt(1000)"  --maxtokens $maxtokens --mintokens 5000
python3 generate.py --texttype uscode --task text2cite              --seed 4 --output "BLT64k/test64k_usc_t2c(100);BLT64k/train64k_usc_t2c(1000)"      --maxtokens $maxtokens --mintokens 5000
python3 generate.py --texttype uscode --task cite2defined           --seed 4 --output "BLT64k/test64k_usc_c2def(100);BLT64k/train64k_usc_c2def(1000)"  --maxtokens $maxtokens --mintokens 5000
python3 generate.py --texttype uscode --task defined2cite           --seed 4 --output "BLT64k/test64k_usc_def2c(100);BLT64k/train64k_usc_def2c(1000)"  --maxtokens $maxtokens --mintokens 5000
python3 generate.py --texttype transcript --task cite2text          --seed 4 --output "BLT64k/test64k_trans_c2t(100);BLT64k/train64k_trans_c2t(1000)"  --maxtokens $maxtokens --numpages "100,130"
python3 generate.py --texttype transcript --task text2cite          --seed 4 --output "BLT64k/test64k_trans_t2c(100);BLT64k/train64k_trans_t2c(1000)"  --maxtokens $maxtokens --numpages "100,130"
