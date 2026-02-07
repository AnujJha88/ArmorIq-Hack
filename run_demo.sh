#!/bin/bash
# Watchtower Demo Runner
# Automatically loads .env and runs the demo

set -e

cd "$(dirname "$0")"

echo "Loading .env..."
export $(grep -v '^#' .env | xargs)

echo "WATCHTOWER_API_KEY: ${WATCHTOWER_API_KEY:0:15}...${WATCHTOWER_API_KEY: -8}"
echo ""

python3 demo/dev_demo.py "$@"
