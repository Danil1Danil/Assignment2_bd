#!/bin/bash
set -euo pipefail

input="${1:-/input/data}"
jar="$(ls /usr/local/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar | head -n 1)"

hdfs dfs -test -e "$input" || bash prepare_data.sh

run_mr() {
    local in_path="$1"
    local out_path="$2"
    local mapper="$3"
    local reducer="$4"

    hdfs dfs -rm -r -f "$out_path" > /dev/null 2>&1 || true

    hadoop jar "$jar" \
        -D mapreduce.job.reduces=1 \
        -files "$mapper","$reducer" \
        -input "$in_path" \
        -output "$out_path" \
        -mapper "python3 $(basename "$mapper")" \
        -reducer "python3 $(basename "$reducer")"
}

hdfs dfs -rm -r -f /indexer > /dev/null 2>&1 || true

# Pipeline 1: /input/data -> /indexer/index (term, doc_id, tf)
run_mr "$input" /indexer/index \
    /app/mapreduce/mapper1.py \
    /app/mapreduce/reducer1.py

# Pipeline 2: /input/data -> /indexer/docs (doc_id, title, doc_len)
run_mr "$input" /indexer/docs \
    /app/mapreduce/mapper2.py \
    /app/mapreduce/reducer2.py

# Pipeline 3: /indexer/index -> /indexer/vocab_and_stats (vocab + stats)
run_mr /indexer/index /indexer/vocab_and_stats \
    /app/mapreduce/mapper3.py \
    /app/mapreduce/reducer3.py

echo "=== Index created successfully ==="
hdfs dfs -ls /indexer