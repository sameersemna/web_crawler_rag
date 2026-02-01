#!/bin/bash
# Install system dependencies for PDF processing

echo "Installing system dependencies for PDF processing..."

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        echo "Detected Debian/Ubuntu system"
        sudo apt-get update
        sudo apt-get install -y poppler-utils tesseract-ocr
        
        # Optional: Additional language packs for OCR
        echo "Installing Tesseract language packs..."
        sudo apt-get install -y tesseract-ocr-ara tesseract-ocr-hin tesseract-ocr-urd
        
    elif command -v yum &> /dev/null; then
        # RedHat/CentOS
        echo "Detected RedHat/CentOS system"
        sudo yum install -y poppler-utils tesseract
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS system"
    if command -v brew &> /dev/null; then
        brew install poppler tesseract
        
        # Optional: Additional language packs
        echo "Installing Tesseract language packs..."
        brew install tesseract-lang
    else
        echo "Homebrew not found. Please install Homebrew first:"
        echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
fi

# Verify installations
echo ""
echo "Verifying installations..."

if command -v pdfinfo &> /dev/null; then
    echo "✓ Poppler installed: $(pdfinfo -v 2>&1 | head -1)"
else
    echo "✗ Poppler NOT installed"
fi

if command -v tesseract &> /dev/null; then
    echo "✓ Tesseract installed: $(tesseract --version 2>&1 | head -1)"
    echo "  Available languages: $(tesseract --list-langs 2>&1 | tail -n +2 | tr '\n' ', ')"
else
    echo "✗ Tesseract NOT installed"
fi

echo ""
echo "Installation complete!"
echo "Restart the server to use PDF processing features."
