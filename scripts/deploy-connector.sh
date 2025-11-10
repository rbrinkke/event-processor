#!/bin/bash
# Debezium Connector Deployment Script
# Deploys and verifies the PostgreSQL connector

set -e

echo "=================================================="
echo "🔌 Debezium Connector Deployment"
echo "=================================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DEBEZIUM_URL="http://localhost:8083"
CONNECTOR_NAME="postgres-event-outbox-connector"
CONNECTOR_CONFIG="debezium/postgres-connector.json"

# 1. Check Debezium is ready
echo "🔍 Checking Debezium Status..."
DEBEZIUM_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $DEBEZIUM_URL/)

if [ "$DEBEZIUM_STATUS" != "200" ]; then
    echo -e "${RED}✗${NC} Debezium is not ready (HTTP $DEBEZIUM_STATUS)"
    echo "  Wait for Debezium to start: docker-compose logs -f debezium"
    exit 1
fi

echo -e "${GREEN}✓${NC} Debezium REST API is accessible"
echo ""

# 2. Check if connector already exists
echo "🔍 Checking Existing Connectors..."
EXISTING_CONNECTORS=$(curl -s $DEBEZIUM_URL/connectors)

if echo "$EXISTING_CONNECTORS" | grep -q "\"$CONNECTOR_NAME\""; then
    echo -e "${YELLOW}⚠${NC} Connector '$CONNECTOR_NAME' already exists"
    echo ""
    echo "Options:"
    echo "  1. Delete existing connector: curl -X DELETE $DEBEZIUM_URL/connectors/$CONNECTOR_NAME"
    echo "  2. Update connector configuration (not recommended)"
    echo "  3. Check connector status: curl $DEBEZIUM_URL/connectors/$CONNECTOR_NAME/status"
    echo ""
    read -p "Delete existing connector and redeploy? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Deleting existing connector..."
        curl -s -X DELETE $DEBEZIUM_URL/connectors/$CONNECTOR_NAME
        sleep 2
        echo -e "${GREEN}✓${NC} Connector deleted"
    else
        echo "Checking existing connector status instead..."
        curl -s $DEBEZIUM_URL/connectors/$CONNECTOR_NAME/status | json_pp
        exit 0
    fi
fi
echo ""

# 3. Validate connector configuration file
echo "📋 Validating Connector Configuration..."
if [ ! -f "$CONNECTOR_CONFIG" ]; then
    echo -e "${RED}✗${NC} Configuration file not found: $CONNECTOR_CONFIG"
    exit 1
fi

# Check for placeholder values
if grep -q "YOUR_POSTGRES" "$CONNECTOR_CONFIG"; then
    echo -e "${RED}✗${NC} Configuration contains placeholder values"
    echo "  Edit $CONNECTOR_CONFIG and replace placeholders"
    exit 1
fi

echo -e "${GREEN}✓${NC} Configuration file is valid"
echo ""

# 4. Deploy connector
echo "🚀 Deploying Connector..."
DEPLOY_RESPONSE=$(curl -s -X POST $DEBEZIUM_URL/connectors \
    -H "Content-Type: application/json" \
    -d @$CONNECTOR_CONFIG)

if echo "$DEPLOY_RESPONSE" | grep -q "error_code"; then
    echo -e "${RED}✗${NC} Deployment failed"
    echo "$DEPLOY_RESPONSE" | json_pp
    exit 1
fi

echo -e "${GREEN}✓${NC} Connector deployed successfully"
echo ""

# 5. Wait for connector to be ready
echo "⏳ Waiting for connector to initialize..."
for i in {1..30}; do
    STATUS=$(curl -s $DEBEZIUM_URL/connectors/$CONNECTOR_NAME/status)
    CONNECTOR_STATE=$(echo "$STATUS" | grep -o '"state":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [ "$CONNECTOR_STATE" == "RUNNING" ]; then
        echo -e "${GREEN}✓${NC} Connector is RUNNING"
        break
    elif [ "$CONNECTOR_STATE" == "FAILED" ]; then
        echo -e "${RED}✗${NC} Connector FAILED to start"
        echo "$STATUS" | json_pp
        exit 1
    fi

    echo "  Status: $CONNECTOR_STATE (attempt $i/30)"
    sleep 2
done

if [ "$CONNECTOR_STATE" != "RUNNING" ]; then
    echo -e "${RED}✗${NC} Connector did not reach RUNNING state"
    exit 1
fi
echo ""

# 6. Check connector tasks
echo "📊 Checking Connector Tasks..."
TASKS=$(curl -s $DEBEZIUM_URL/connectors/$CONNECTOR_NAME/status | grep -o '"tasks":\[.*\]' | json_pp)
echo "$TASKS"

TASK_STATE=$(curl -s $DEBEZIUM_URL/connectors/$CONNECTOR_NAME/status | grep -o '"state":"[^"]*"' | tail -1 | cut -d'"' -f4)
if [ "$TASK_STATE" == "RUNNING" ]; then
    echo -e "${GREEN}✓${NC} All tasks are RUNNING"
else
    echo -e "${YELLOW}⚠${NC} Task state: $TASK_STATE"
fi
echo ""

# 7. Verify Kafka topic created
echo "🎯 Verifying Kafka Topic..."
sleep 3  # Give Debezium time to create topic

EXPECTED_TOPIC="postgres.activity.event_outbox"
TOPICS=$(docker-compose exec -T kafka kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null)

if echo "$TOPICS" | grep -q "$EXPECTED_TOPIC"; then
    echo -e "${GREEN}✓${NC} Kafka topic '$EXPECTED_TOPIC' exists"

    # Get topic details
    echo ""
    echo "Topic Details:"
    docker-compose exec -T kafka kafka-topics --describe --topic $EXPECTED_TOPIC --bootstrap-server localhost:9092 2>/dev/null
else
    echo -e "${YELLOW}⚠${NC} Kafka topic '$EXPECTED_TOPIC' not yet created"
    echo "  It will be created when first event is captured"
fi
echo ""

# 8. Check replication slot created
echo "🔄 Checking PostgreSQL Replication Slot..."
SLOT_EXISTS=$(docker exec auth-postgres psql -U activity_user -d activity_db -t -c "SELECT COUNT(*) FROM pg_replication_slots WHERE slot_name='debezium_slot';" 2>/dev/null | xargs)

if [ "$SLOT_EXISTS" == "1" ]; then
    echo -e "${GREEN}✓${NC} Replication slot 'debezium_slot' exists"
    docker exec auth-postgres psql -U activity_user -d activity_db -c "SELECT slot_name, plugin, slot_type, active, restart_lsn FROM pg_replication_slots WHERE slot_name='debezium_slot';" 2>/dev/null
else
    echo -e "${YELLOW}⚠${NC} Replication slot 'debezium_slot' not yet created"
    echo "  It will be created on first snapshot"
fi
echo ""

# Summary
echo "=================================================="
echo "✅ Connector Deployment Complete!"
echo "=================================================="
echo ""
echo "Connector Status:"
curl -s $DEBEZIUM_URL/connectors/$CONNECTOR_NAME/status | json_pp
echo ""
echo "Next Steps:"
echo "  1. Monitor connector: docker-compose logs -f debezium"
echo "  2. Insert test event: ./scripts/test-e2e.sh"
echo "  3. Check Kafka UI: http://localhost:8080"
echo ""
echo "Useful Commands:"
echo "  • Connector status: curl $DEBEZIUM_URL/connectors/$CONNECTOR_NAME/status"
echo "  • Restart connector: curl -X POST $DEBEZIUM_URL/connectors/$CONNECTOR_NAME/restart"
echo "  • Delete connector: curl -X DELETE $DEBEZIUM_URL/connectors/$CONNECTOR_NAME"
echo ""
