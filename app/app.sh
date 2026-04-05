#!/bin/bash
set -euo pipefail

service ssh restart

bash start-services.sh

wait_for_hdfs() {
    echo "Waiting for HDFS and YARN..."
    for i in $(seq 1 60); do
        if hdfs dfs -ls / > /dev/null 2>&1 && \
           yarn node -list -all 2>/dev/null | grep -q RUNNING; then
            echo "Cluster is ready"
            return 0
        fi
        sleep 3
    done
    echo "Cluster did not start in time"
    return 1
}

# Setup Python environment
rm -rf .venv .venv.tar.gz
python3 -m venv .venv
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt
venv-pack -o .venv.tar.gz

wait_for_hdfs

# Run indexing
bash index.sh

# Run some test queries
bash search.sh "machine learning"
bash search.sh "history of art"
bash search.sh "it is a query!"

exec tail -f /dev/null