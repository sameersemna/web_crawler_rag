#!/bin/bash

# Web Crawler RAG API - Setup Script
# This script sets up the application for first-time use

set -e

echo "=========================================="
echo "Web Crawler RAG API - Setup"
echo "=========================================="

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p data/logs
mkdir -p data/vector_db
mkdir -p config
mkdir -p tests

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your API keys!"
    echo "   - GEMINI_API_KEY"
    echo "   - DEEPSEEK_API_KEY"
    echo ""
fi

# Create example domains CSV if it doesn't exist
if [ ! -f "data/domains.csv" ]; then
    echo "Creating example domains.csv..."
    echo "domain" > data/domains.csv
    echo "example.com" >> data/domains.csv
    echo "wikipedia.org" >> data/domains.csv
    echo ""
    echo "📝 Example domains.csv created. Edit data/domains.csv to add your domains."
    echo ""
fi

# Check Tesseract installation
echo "Checking Tesseract OCR installation..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -n 1)
    echo "✓ Tesseract found: $tesseract_version"
else
    echo "⚠️  Tesseract OCR not found!"
    echo "   Please install Tesseract for OCR functionality:"
    echo "   Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "   macOS: brew install tesseract"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Edit data/domains.csv to add domains to crawl"
echo "3. Run: python main.py"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
