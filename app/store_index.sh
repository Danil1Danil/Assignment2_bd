#!/bin/bash
set -euo pipefail

source .venv/bin/activate
python app.py "${1:-/indexer}"