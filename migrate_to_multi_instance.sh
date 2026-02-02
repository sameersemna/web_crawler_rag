#!/bin/bash
# Migrate current data folder to Islam instance

echo "=========================================="
echo "Migrating to Multi-Instance Setup"
echo "=========================================="
echo ""

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "ERROR: data directory not found"
    exit 1
fi

# Check if already migrated
if [ -d "data/islam" ]; then
    echo "ERROR: data/islam already exists"
    echo "Migration may have already been completed."
    exit 1
fi

echo "Step 1: Installing PyYAML..."
pip install pyyaml==6.0.2

echo ""
echo "Step 2: Creating instance directories..."

# Create islam instance directory
mkdir -p data/islam

echo "✓ Created data/islam/"

# Move existing data to islam instance
echo ""
echo "Step 3: Moving existing data to data/islam/..."

# Move database if exists
if [ -f "data/crawler_rag.db" ]; then
    mv data/crawler_rag.db data/islam/
    echo "✓ Moved crawler_rag.db"
fi

if [ -f "data/web_crawler.db" ]; then
    mv data/web_crawler.db data/islam/
    echo "✓ Moved web_crawler.db"
fi

# Move vector_db if exists
if [ -d "data/vector_db" ]; then
    mv data/vector_db data/islam/
    echo "✓ Moved vector_db/"
fi

# Move logs if exists
if [ -d "data/logs" ]; then
    mv data/logs data/islam/
    echo "✓ Moved logs/"
fi

# Copy domains.csv to islam instance
if [ -f "data/domains.csv" ]; then
    cp data/domains.csv data/islam/
    echo "✓ Copied domains.csv"
elif [ -f "data/domains_islam.csv" ]; then
    cp data/domains_islam.csv data/islam/domains.csv
    echo "✓ Copied domains_islam.csv as domains.csv"
fi

# Create law instance directory and sample domains file
echo ""
echo "Step 4: Creating law instance template..."
mkdir -p data/law

# Create sample domains.csv for law instance
cat > data/law/domains.csv << 'EOF'
domain
example-law-site.com
EOF

echo "✓ Created data/law/ with sample domains.csv"

echo ""
echo "=========================================="
echo "Migration Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the Islam instance:"
echo "   python main.py islam.yaml"
echo ""
echo "2. To create law instance, edit law.yaml and add domains to:"
echo "   data/law/domains.csv"
echo ""
echo "3. Start the Law instance (on different port):"
echo "   python main.py law.yaml"
echo ""
echo "You can run multiple instances simultaneously!"
echo ""
