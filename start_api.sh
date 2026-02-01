#!/bin/bash
# Start API Server only (no background crawling)

echo "Starting Web Crawler RAG API Server..."
echo "This service handles API requests only"
echo "Background crawling will NOT run automatically"
echo ""

cd /root/web_crawler_rag
source venv/bin/activate

# Run API server
python main.py
