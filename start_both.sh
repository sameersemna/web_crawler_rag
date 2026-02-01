#!/bin/bash
# Start both API Server and Background Crawler

echo "Starting Web Crawler RAG - Full Stack"
echo "This will start both:"
echo "  1. API Server (port 8000)"
echo "  2. Background Crawler Service"
echo ""

cd /root/web_crawler_rag
source venv/bin/activate

# Start API server in background
echo "Starting API Server..."
python main.py &
API_PID=$!
echo "API Server started (PID: $API_PID)"

# Wait a moment for API to start
sleep 2

# Start crawler service in background
echo "Starting Background Crawler Service..."
python main_crawl.py &
CRAWLER_PID=$!
echo "Crawler Service started (PID: $CRAWLER_PID)"

echo ""
echo "Both services are running:"
echo "  API Server PID: $API_PID"
echo "  Crawler Service PID: $CRAWLER_PID"
echo ""
echo "Press Ctrl+C to stop both services"

# Function to stop both services
stop_services() {
    echo ""
    echo "Stopping services..."
    kill $API_PID 2>/dev/null
    kill $CRAWLER_PID 2>/dev/null
    echo "Services stopped"
    exit 0
}

# Trap Ctrl+C
trap stop_services SIGINT SIGTERM

# Wait for both processes
wait
