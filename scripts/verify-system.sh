#!/bin/bash
# System Verification Script
# Checks all prerequisites for event processor deployment

set -e

echo "=================================================="
echo "🔍 Event Processor - System Verification"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check function
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1"
        return 1
    fi
}

# 1. Check Docker Network
echo "📡 Checking Docker Network..."
docker network inspect activity-network &>/dev/null
check "activity-network exists"
echo ""

# 2. Check Services Status
echo "🐳 Checking Docker Services..."
docker-compose ps | grep -q "zookeeper.*Up"
check "Zookeeper is running"

docker-compose ps | grep -q "kafka.*Up"
check "Kafka is running"

docker-compose ps | grep -q "debezium.*Up"
check "Debezium is running"

docker-compose ps | grep -q "kafka-ui.*Up"
check "Kafka UI is running"
echo ""

# 3. Check Kafka Health
echo "🎯 Checking Kafka Health..."
docker-compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 &>/dev/null
check "Kafka broker is responsive"
echo ""

# 4. Check Debezium Health
echo "🔄 Checking Debezium Health..."
DEBEZIUM_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8083/)
if [ "$DEBEZIUM_STATUS" == "200" ]; then
    echo -e "${GREEN}✓${NC} Debezium REST API is accessible"
else
    echo -e "${RED}✗${NC} Debezium REST API is not accessible (HTTP $DEBEZIUM_STATUS)"
fi
echo ""

# 5. Check PostgreSQL Connection
echo "🐘 Checking PostgreSQL Connection..."
docker exec auth-postgres psql -U activity_user -d activity_db -c "SELECT 1;" &>/dev/null
check "PostgreSQL is accessible"

# Check wal_level
WAL_LEVEL=$(docker exec auth-postgres psql -U activity_user -d activity_db -t -c "SHOW wal_level;" 2>/dev/null | xargs)
if [ "$WAL_LEVEL" == "logical" ]; then
    echo -e "${GREEN}✓${NC} PostgreSQL wal_level is 'logical'"
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL wal_level is '$WAL_LEVEL' (should be 'logical')"
    echo "  Run: docker exec auth-postgres psql -U activity_user -d activity_db -c \"ALTER SYSTEM SET wal_level = 'logical';\""
    echo "  Then restart PostgreSQL"
fi

# Check publication
PUBLICATION_EXISTS=$(docker exec auth-postgres psql -U activity_user -d activity_db -t -c "SELECT COUNT(*) FROM pg_publication WHERE pubname='debezium_publication';" 2>/dev/null | xargs)
if [ "$PUBLICATION_EXISTS" == "1" ]; then
    echo -e "${GREEN}✓${NC} Debezium publication exists"
else
    echo -e "${YELLOW}⚠${NC} Debezium publication does not exist"
    echo "  Run: docker exec auth-postgres psql -U activity_user -d activity_db -c \"CREATE PUBLICATION debezium_publication FOR TABLE activity.event_outbox;\""
fi
echo ""

# 6. Check MongoDB Connection
echo "🍃 Checking MongoDB Connection..."
if command -v mongosh &> /dev/null; then
    mongosh "mongodb://localhost:27025/activity_read" --eval "db.adminCommand('ping')" --quiet &>/dev/null
    check "MongoDB is accessible"
else
    echo -e "${YELLOW}⚠${NC} mongosh not installed - cannot verify MongoDB connection"
    echo "  Install: https://www.mongodb.com/docs/mongodb-shell/install/"
fi
echo ""

# 7. Check .env file
echo "⚙️  Checking Configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"

    # Check required variables
    grep -q "MONGODB_URI" .env
    check "MONGODB_URI is configured"

    grep -q "KAFKA_BOOTSTRAP_SERVERS" .env
    check "KAFKA_BOOTSTRAP_SERVERS is configured"

    grep -q "POSTGRES_HOST" .env
    check "POSTGRES_HOST is configured"
else
    echo -e "${RED}✗${NC} .env file not found"
    echo "  Copy .env.example to .env and configure"
fi
echo ""

# 8. Check Connector Configuration
echo "🔌 Checking Connector Configuration..."
if [ -f "debezium/postgres-connector.json" ]; then
    echo -e "${GREEN}✓${NC} postgres-connector.json exists"

    grep -q "host.docker.internal" debezium/postgres-connector.json
    check "Connector has correct hostname"
else
    echo -e "${RED}✗${NC} postgres-connector.json not found"
fi
echo ""

# Summary
echo "=================================================="
echo "✅ Verification Complete!"
echo "=================================================="
echo ""
echo "Next Steps:"
echo "1. Fix any warnings above"
echo "2. Run: docker-compose build event-processor"
echo "3. Run: docker-compose restart event-processor"
echo "4. Run: ./scripts/deploy-connector.sh"
echo "5. Run: ./scripts/test-e2e.sh"
echo ""
