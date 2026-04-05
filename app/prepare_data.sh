#!/bin/bash
set -euo pipefail

source .venv/bin/activate
export PYSPARK_DRIVER_PYTHON=$(which python)
unset PYSPARK_PYTHON

local_parquet="${LOCAL_PARQUET_FILE:-/datasets/a.parquet}"
hdfs_parquet="${HDFS_PARQUET_FILE:-hdfs://cluster-master:9000/parquet/a.parquet}"
staging="./staging_docs"

# Cleanup old data
hdfs dfs -rm -r -f /parquet /data /input/data > /dev/null 2>&1 || true
rm -rf "$staging" data
mkdir -p "$staging" data

# Upload parquet to HDFS
hdfs dfs -mkdir -p /parquet
hdfs dfs -put "$local_parquet" /parquet/a.parquet

# Convert parquet to txt files
spark-submit prepare_data.py "$hdfs_parquet"

# Filter only ASCII-safe filenames
file_count=0
while IFS= read -r f; do
    base="$(basename "$f")"
    if LC_ALL=C printf '%s' "$base" | grep -qP '^[\x20-\x7E]+$'; then
        cp "$f" "$staging/$base"
        file_count=$((file_count + 1))
    fi
done < <(find data -maxdepth 1 -name "*.txt" -type f | sort)

echo "Staged $file_count documents"
[ "$file_count" -gt 0 ]

# Upload docs to HDFS
hdfs dfs -mkdir -p /data
hdfs dfs -put "$staging"/* /data/

# Convert docs to single input file
spark-submit prepare_data.py /data /input/data

hdfs dfs -ls /input/data
rm -rf "$staging"