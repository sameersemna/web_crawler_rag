#!/bin/bash

# Quick rebuild and restart script with resource limits
# Run this after making resource configuration changes

echo "🔄 Stopping existing container..."
docker-compose down

echo "🏗️  Rebuilding with resource limits..."
docker-compose build --no-cache

echo "🚀 Starting with resource limits..."
docker-compose up -d

echo "⏳ Waiting for container to be ready..."
sleep 5

echo "📊 Current resource limits:"
docker inspect web_crawler_rag_api | grep -A 10 "NanoCpus\|Memory" | head -20

echo ""
echo "✅ Container started with resource limits:"
echo "   - CPU: 4 cores maximum"
echo "   - Memory: 4GB maximum"
echo "   - Workers: 2"
echo "   - Concurrent requests: 4"
echo ""
echo "📈 Monitor resource usage with:"
echo "   docker stats web_crawler_rag_api"
echo ""
echo "📝 View logs with:"
echo "   docker-compose logs -f"
echo ""
echo "🔍 Check health:"
echo "   curl http://localhost:8000/api/v1/health"
