#!/bin/bash
# Start background crawler for specific instance
# Usage: ./start_crawl.sh <config_file.yaml>

if [ -z "$1" ]; then
    echo "Usage: ./start_crawl.sh <config_file.yaml>"
    echo ""
    echo "Available configurations:"
    ls -1 *.yaml 2>/dev/null | grep -v "docker-compose"
    echo ""
    exit 1
fi

CONFIG_FILE="$1"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Configuration file not found: $CONFIG_FILE"
    echo ""
    echo "Available configurations:"
    ls -1 *.yaml 2>/dev/null | grep -v "docker-compose"
    echo ""
    exit 1
fi

echo "Starting background crawler with config: $CONFIG_FILE"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the background crawler
python main_crawl.py "$CONFIG_FILE"
