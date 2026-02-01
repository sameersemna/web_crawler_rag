#!/bin/bash
# Start Background Crawler Service only

echo "Starting Background Crawler Service..."
echo "This service runs automatic scheduled crawling"
echo "The API server must be running separately"
echo ""

cd /root/web_crawler_rag
source venv/bin/activate

# Check if background crawling is enabled
if grep -q "ENABLE_BACKGROUND_CRAWLING=True" .env; then
    echo "Background crawling is ENABLED"
    echo "Starting crawler service..."
    python main_crawl.py
else
    echo "ERROR: Background crawling is DISABLED in .env"
    echo "Set ENABLE_BACKGROUND_CRAWLING=True to enable"
    echo "Service will not start."
    exit 1
fi
