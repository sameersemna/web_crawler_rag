#!/bin/bash
# Emergency Stop Script
# Use this if the application is hanging

echo "=========================================="
echo "EMERGENCY STOP - Killing Web Crawler RAG"
echo "=========================================="

# Find and kill all related processes
echo "Searching for processes..."

# Kill uvicorn processes
pkill -9 -f "uvicorn.*main:app" && echo "✓ Killed uvicorn processes"

# Kill python processes running main.py
pkill -9 -f "python.*main.py" && echo "✓ Killed main.py processes"

# Kill any python processes with web_crawler_rag in path
pkill -9 -f "web_crawler_rag" && echo "✓ Killed web_crawler_rag processes"

# Stop Docker containers if running
docker ps | grep web_crawler_rag_api && {
    echo "Found Docker container, stopping..."
    docker stop web_crawler_rag_api
    echo "✓ Docker container stopped"
}

echo ""
echo "Checking remaining processes..."
ps aux | grep -E "uvicorn|main.py|web_crawler" | grep -v grep

echo ""
echo "=========================================="
echo "If processes are still running:"
echo "1. Restart your terminal"
echo "2. Check system monitor (htop/top)"
echo "3. Reboot if necessary"
echo "=========================================="
