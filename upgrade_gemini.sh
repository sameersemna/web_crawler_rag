#!/bin/bash
# Upgrade google-generativeai library to fix Gemini API issues

echo "Stopping server..."
./emergency_stop.sh 2>/dev/null || true

echo "Upgrading google-generativeai library..."
cd /root/web_crawler_rag
source venv/bin/activate
pip install --upgrade google-generativeai

echo "Library upgraded successfully!"
echo "Starting server..."
./start_minimal.sh

echo ""
echo "Test with: curl -X POST http://localhost:8000/api/v1/query -H 'Content-Type: application/json' -d '{\"query\": \"test\"}'"
