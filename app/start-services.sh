#!/bin/bash
set -euo pipefail

cat > "$HADOOP_HOME/etc/hadoop/workers" <<'EOF'
cluster-slave-1
EOF

# Start HDFS services
hdfs --daemon start namenode
hdfs --daemon start secondarynamenode

# Start YARN services
yarn --daemon start resourcemanager
mapred --daemon start historyserver

# Create base HDFS directories
hdfs dfs -mkdir -p /user/root
hdfs dfs -mkdir -p /input
hdfs dfs -mkdir -p /indexer

jps -lm
hdfs dfsadmin -report