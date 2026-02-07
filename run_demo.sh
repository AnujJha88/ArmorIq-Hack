#!/bin/bash
# ArmorIQ Demo Runner
# Automatically loads .env and runs the demo

set -e

cd "$(dirname "$0")"

echo "Loading .env..."
export $(grep -v '^#' .env | xargs)

echo "ARMORIQ_API_KEY: ${ARMORIQ_API_KEY:0:15}...${ARMORIQ_API_KEY: -8}"
echo ""

python3 demo/dev_demo.py "$@"
