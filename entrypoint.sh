#!/bin/bash
set -e

CONFIG_FILE="./config.yaml"
CONFIG_DEFAULT="./config.default.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚠️ Config file not found at $CONFIG_FILE"
    echo "Starting with default config..."
    cp "$CONFIG_DEFAULT" "$CONFIG_FILE"
fi

python -m src.apigator
