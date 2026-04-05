#!/bin/bash
set -euo pipefail

source .venv/bin/activate
export PYSPARK_DRIVER_PYTHON=$(which python)
export PYSPARK_PYTHON=python3

tmp_err=$(mktemp)

spark-submit \
    --master yarn \
    --deploy-mode client \
    --conf "spark.executor.instances=1" \
    --conf "spark.ui.showConsoleProgress=false" \
    --conf "spark.yarn.jars=local:///usr/local/spark/jars/*" \
    query.py "$@" 2>"$tmp_err" || {
        cat "$tmp_err" >&2
        rm -f "$tmp_err"
        exit 1
    }

rm -f "$tmp_err"