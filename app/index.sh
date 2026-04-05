#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"
bash create_index.sh "${1:-/input/data}"
bash store_index.sh "${2:-/indexer}"