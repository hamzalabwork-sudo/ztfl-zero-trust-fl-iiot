#!/usr/bin/env bash
# E5b + E5c (EXPERIMENTS.md), run from the repository root
set -e
PY=".venv/bin/python -X faulthandler -u src/closed_loop.py --datasets edgeiiot,wustl,forge --seeds 42,43,44,45,46"
$PY --llr monotone --cusum-threshold empirical
$PY --llr monotone --cusum-threshold lorden
