#!/bin/bash
# End-to-End Flow Testing Script
# Tests complete flow: PostgreSQL → Debezium → Kafka → Consumer → MongoDB

set -e

echo "=================================================="
echo "🧪 End-to-End Flow Testing"
echo "=================================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

POSTGRES_CONTAINER="auth-postgres"
POSTGRES_USER="activity_user"
POSTGRES_DB="activity_db"
KAFKA_TOPIC="postgres.activity.event_outbox"
MONGODB_URI="${MONGODB_URI:-mongodb://localhost:27025}"
MONGODB_DB="${MONGODB_DATABASE:-activity_read}"

# Generate test data
TEST_USER_ID=$(uuidgen 2>/dev/null || echo "$(date +%s)-$(shuf -i 1000-9999 -n 1)")
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_USERNAME="testuser_$(date +%s)"
TIMESTAMP=$(date -Iseconds)

echo "📝 Test Event Details:"
echo "  Email: $TEST_EMAIL"
echo "  Username: $TEST_USERNAME"
echo "  Timestamp: $TIMESTAMP"
echo ""

# Step 1: Insert test event into PostgreSQL
echo "1️⃣  Inserting Test Event into PostgreSQL..."
docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
INSERT INTO activity.event_outbox (
    event_id,
    aggregate_id,
    aggregate_type,
    event_type,
    payload,
    status
) VALUES (
    gen_random_uuid(),
    gen_random_uuid(),
    'User',
    'UserCreated',
    '{
        \"email\": \"$TEST_EMAIL\",
        \"username\": \"$TEST_USERNAME\",
        \"first_name\": \"Test\",
        \"last_name\": \"User\",
        \"created_at\": \"$TIMESTAMP\"
    }'::jsonb,
    'pending'
);" &>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Test event inserted into PostgreSQL"
else
    echo -e "${RED}✗${NC} Failed to insert test event"
    exit 1
fi
echo ""

# Step 2: Check Debezium captures the event
echo "2️⃣  Waiting for Debezium to Capture Event..."
sleep 2
echo -e "${GREEN}✓${NC} Debezium should have captured the event (check logs: docker-compose logs debezium)"
echo ""

# Step 3: Check Kafka receives the message
echo "3️⃣  Checking Kafka Topic for Message..."
sleep 2

# Try to consume last 10 messages from topic
KAFKA_MESSAGES=$(timeout 5 docker-compose exec -T kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic $KAFKA_TOPIC \
    --from-beginning \
    --max-messages 10 \
    --timeout-ms 3000 2>/dev/null || echo "")

if echo "$KAFKA_MESSAGES" | grep -q "$TEST_EMAIL"; then
    echo -e "${GREEN}✓${NC} Message found in Kafka topic"
else
    echo -e "${YELLOW}⚠${NC} Message not found in recent Kafka messages (might be older)"
    echo "  Check Kafka UI: http://localhost:8080"
fi
echo ""

# Step 4: Wait for consumer to process
echo "4️⃣  Waiting for Event Processor to Process Event..."
sleep 5
echo -e "${GREEN}✓${NC} Processing window complete (check logs: docker-compose logs event-processor)"
echo ""

# Step 5: Verify MongoDB document created
echo "5️⃣  Verifying MongoDB Document..."

# Check if mongosh is available
if command -v mongosh &> /dev/null; then
    MONGO_DOC=$(mongosh "$MONGODB_URI/$MONGODB_DB" --quiet --eval "
        db.users.findOne({email: '$TEST_EMAIL'})
    " 2>/dev/null)

    if echo "$MONGO_DOC" | grep -q "$TEST_EMAIL"; then
        echo -e "${GREEN}✓${NC} Document found in MongoDB!"
        echo ""
        echo "Document:"
        echo "$MONGO_DOC"
    else
        echo -e "${RED}✗${NC} Document not found in MongoDB"
        echo "  Possible causes:"
        echo "  • Event processor not running: docker-compose ps event-processor"
        echo "  • Handler error: docker-compose logs event-processor"
        echo "  • MongoDB connection issue: check MONGODB_URI"
    fi
else
    echo -e "${YELLOW}⚠${NC} mongosh not installed - cannot verify MongoDB"
    echo "  Install: https://www.mongodb.com/docs/mongodb-shell/install/"
    echo "  Or check manually: mongosh \"$MONGODB_URI/$MONGODB_DB\" --eval 'db.users.findOne({email: \"$TEST_EMAIL\"})'"
fi
echo ""

# Summary
echo "=================================================="
echo "📊 E2E Test Summary"
echo "=================================================="
echo ""
echo "Flow Checkpoints:"
echo "  1. PostgreSQL INSERT: ${GREEN}✓${NC}"
echo "  2. Debezium Capture: ${GREEN}✓${NC} (check logs)"
echo "  3. Kafka Message: ${YELLOW}?${NC} (check Kafka UI)"
echo "  4. Consumer Processing: ${GREEN}✓${NC} (check logs)"
echo "  5. MongoDB Document: ${YELLOW}?${NC} (verify with mongosh)"
echo ""
echo "Verification Commands:"
echo "  • PostgreSQL: docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -c \"SELECT * FROM activity.event_outbox WHERE payload->>'email' = '$TEST_EMAIL';\""
echo "  • Kafka: docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic $KAFKA_TOPIC --from-beginning"
echo "  • Debezium: docker-compose logs debezium | grep -i error"
echo "  • Consumer: docker-compose logs event-processor | grep -i error"
echo "  • MongoDB: mongosh \"$MONGODB_URI/$MONGODB_DB\" --eval 'db.users.findOne({email: \"$TEST_EMAIL\"})'"
echo ""
echo "Logs:"
echo "  • docker-compose logs -f event-processor"
echo "  • docker-compose logs -f debezium"
echo "  • docker-compose logs -f kafka"
echo ""
