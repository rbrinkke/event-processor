#!/bin/bash
# Setup Script - Verify Services and Prepare Demo Environment

set -e

echo "=========================================="
echo "EVENT PROCESSOR DEMO - SETUP"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check PostgreSQL
echo -n "Checking PostgreSQL... "
if pg_isready -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not accessible${NC}"
    echo "Please start PostgreSQL or check POSTGRES_HOST/PORT environment variables"
    exit 1
fi

# Check Kafka
echo -n "Checking Kafka... "
if nc -zv ${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092} 2>&1 | grep -q "succeeded"; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not accessible${NC}"
    echo "Please start Kafka or check KAFKA_BOOTSTRAP_SERVERS environment variable"
    exit 1
fi

# Check MongoDB
echo -n "Checking MongoDB... "
MONGODB_HOST=$(echo ${MONGODB_URI:-mongodb://localhost:27017} | sed -e 's/mongodb:\/\///' -e 's/\/.*//')
if nc -zv $MONGODB_HOST 2>&1 | grep -q "succeeded"; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${YELLOW}⚠ Not accessible${NC}"
    echo "Warning: MongoDB may not be accessible. Verification will fail."
fi

# Verify event_outbox table exists
echo -n "Checking event_outbox table... "
if psql -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-activity} \
    -c "SELECT 1 FROM event_outbox LIMIT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Exists${NC}"
else
    echo -e "${RED}✗ Not found${NC}"
    echo "Please create event_outbox table using database/schema.sql"
    exit 1
fi

# Check Python dependencies
echo -n "Checking Python dependencies... "
if python3 -c "import rich, faker, psycopg2, pymongo, numpy" 2>/dev/null; then
    echo -e "${GREEN}✓ Installed${NC}"
else
    echo -e "${RED}✗ Missing${NC}"
    echo "Installing required packages..."
    pip install --break-system-packages rich faker psycopg2-binary pymongo numpy
fi

# Clean previous demo data (optional)
echo ""
echo "Clean previous demo data? (y/N)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Cleaning PostgreSQL event_outbox..."
    psql -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-activity} \
        -c "DELETE FROM event_outbox" > /dev/null 2>&1

    echo "Cleaning MongoDB collections..."
    python3 <<EOF
from pymongo import MongoClient
import os

uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.getenv("MONGODB_DATABASE", "activity_read")

client = MongoClient(uri)
db = client[db_name]

db.users.delete_many({})
db.activities.delete_many({})
db.statistics.delete_many({})

print(f"✓ Cleaned MongoDB database: {db_name}")
client.close()
EOF

    echo -e "${GREEN}✓ Demo data cleaned${NC}"
fi

echo ""
echo "=========================================="
echo "✓ SETUP COMPLETE - READY FOR DEMO"
echo "=========================================="
echo ""
echo "Run a load test:"
echo "  ./scripts/demo/load_10.sh"
echo "  ./scripts/demo/load_100.sh"
echo "  ./scripts/demo/load_1000.sh"
echo ""
echo "Or run the complete demo:"
echo "  ./scripts/demo/full_demo.sh"
echo ""
