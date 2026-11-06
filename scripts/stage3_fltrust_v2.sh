#!/usr/bin/env bash
# E7 variant: faithful FLTrust (root update with the same number of local steps as an average client).
cd "$(dirname "$0")/.."
CUDA_VISIBLE_DEVICES=1 .venv/bin/python src/stage3.py --datasets edgeiiot,wustl,forge --aggregators fltrust_v2 > logs/stage3_fltrust_v2.log 2>&1
echo "== done" >> logs/stage3_fltrust_v2.log
