#!/bin/bash
# PostgreSQL Configuration Checker and Fixer
# Ensures PostgreSQL is properly configured for Debezium CDC

set -e

echo "=================================================="
echo "🐘 PostgreSQL CDC Configuration Checker"
echo "=================================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

POSTGRES_CONTAINER="auth-postgres"
POSTGRES_USER="activity_user"
POSTGRES_DB="activity_db"

# 1. Check wal_level
echo "📋 Checking WAL Level..."
WAL_LEVEL=$(docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SHOW wal_level;" 2>/dev/null | xargs)

if [ "$WAL_LEVEL" == "logical" ]; then
    echo -e "${GREEN}✓${NC} wal_level is 'logical'"
else
    echo -e "${RED}✗${NC} wal_level is '$WAL_LEVEL' (must be 'logical')"
    echo ""
    echo "🔧 Fixing wal_level..."
    docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -c "ALTER SYSTEM SET wal_level = 'logical';"
    echo -e "${YELLOW}⚠${NC} PostgreSQL restart required for wal_level change"
    echo "  Run: docker restart $POSTGRES_CONTAINER"
    echo "  Then re-run this script"
    exit 1
fi
echo ""

# 2. Check max_wal_senders
echo "📡 Checking max_wal_senders..."
MAX_WAL_SENDERS=$(docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SHOW max_wal_senders;" 2>/dev/null | xargs)

if [ "$MAX_WAL_SENDERS" -ge "10" ]; then
    echo -e "${GREEN}✓${NC} max_wal_senders is $MAX_WAL_SENDERS (sufficient)"
else
    echo -e "${YELLOW}⚠${NC} max_wal_senders is $MAX_WAL_SENDERS (recommended >= 10)"
    echo "  Run: docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -c \"ALTER SYSTEM SET max_wal_senders = 10;\""
    echo "  Then restart PostgreSQL"
fi
echo ""

# 3. Check max_replication_slots
echo "🔌 Checking max_replication_slots..."
MAX_REPLICATION_SLOTS=$(docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SHOW max_replication_slots;" 2>/dev/null | xargs)

if [ "$MAX_REPLICATION_SLOTS" -ge "10" ]; then
    echo -e "${GREEN}✓${NC} max_replication_slots is $MAX_REPLICATION_SLOTS (sufficient)"
else
    echo -e "${YELLOW}⚠${NC} max_replication_slots is $MAX_REPLICATION_SLOTS (recommended >= 10)"
    echo "  Run: docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -c \"ALTER SYSTEM SET max_replication_slots = 10;\""
    echo "  Then restart PostgreSQL"
fi
echo ""

# 4. Check publication
echo "📢 Checking Debezium Publication..."
PUBLICATION_EXISTS=$(docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM pg_publication WHERE pubname='debezium_publication';" 2>/dev/null | xargs)

if [ "$PUBLICATION_EXISTS" == "1" ]; then
    echo -e "${GREEN}✓${NC} debezium_publication exists"

    # Check what tables are included
    TABLES=$(docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT schemaname || '.' || tablename FROM pg_publication_tables WHERE pubname='debezium_publication';" 2>/dev/null | xargs)
    echo "  Published tables: $TABLES"
else
    echo -e "${RED}✗${NC} debezium_publication does not exist"
    echo ""
    echo "🔧 Creating debezium_publication..."
    docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE PUBLICATION debezium_publication FOR TABLE activity.event_outbox;"
    echo -e "${GREEN}✓${NC} Publication created successfully"
fi
echo ""

# 5. Check event_outbox table exists
echo "📦 Checking event_outbox Table..."
TABLE_EXISTS=$(docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='activity' AND table_name='event_outbox';" 2>/dev/null | xargs)

if [ "$TABLE_EXISTS" == "1" ]; then
    echo -e "${GREEN}✓${NC} activity.event_outbox table exists"

    # Count events
    EVENT_COUNT=$(docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM activity.event_outbox;" 2>/dev/null | xargs)
    echo "  Current event count: $EVENT_COUNT"
else
    echo -e "${RED}✗${NC} activity.event_outbox table does not exist"
    echo "  This table should be created by the auth-api service"
fi
echo ""

# 6. Test INSERT capability
echo "🧪 Testing INSERT Capability..."
TEST_EVENT_ID=$(uuidgen 2>/dev/null || echo "$(date +%s)-test")

docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
INSERT INTO activity.event_outbox (
    event_id, aggregate_id, aggregate_type, event_type, payload, status
) VALUES (
    gen_random_uuid(),
    gen_random_uuid(),
    'TestAggregate',
    'TestEvent',
    '{\"test\": true, \"timestamp\": \"$(date -Iseconds)\"}'::jsonb,
    'pending'
);" &>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Successfully inserted test event"
    echo "  Cleaning up test event..."
    docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -c "DELETE FROM activity.event_outbox WHERE aggregate_type='TestAggregate';" &>/dev/null
else
    echo -e "${RED}✗${NC} Failed to insert test event"
fi
echo ""

# 7. Check replication slots
echo "🔄 Checking Replication Slots..."
SLOT_COUNT=$(docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM pg_replication_slots;" 2>/dev/null | xargs)

if [ "$SLOT_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✓${NC} Found $SLOT_COUNT replication slot(s)"
    docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT slot_name, plugin, slot_type, active FROM pg_replication_slots;" 2>/dev/null
else
    echo -e "${YELLOW}⚠${NC} No replication slots found (will be created by Debezium)"
fi
echo ""

# Summary
echo "=================================================="
echo "✅ PostgreSQL Configuration Check Complete"
echo "=================================================="
echo ""
echo "Configuration Summary:"
echo "  • WAL Level: $WAL_LEVEL"
echo "  • Max WAL Senders: $MAX_WAL_SENDERS"
echo "  • Max Replication Slots: $MAX_REPLICATION_SLOTS"
echo "  • Publication Exists: $([ "$PUBLICATION_EXISTS" == "1" ] && echo 'Yes' || echo 'No')"
echo "  • event_outbox Table: $([ "$TABLE_EXISTS" == "1" ] && echo 'Exists' || echo 'Missing')"
echo ""

if [ "$WAL_LEVEL" == "logical" ] && [ "$PUBLICATION_EXISTS" == "1" ] && [ "$TABLE_EXISTS" == "1" ]; then
    echo -e "${GREEN}✅ PostgreSQL is ready for Debezium CDC!${NC}"
    exit 0
else
    echo -e "${RED}❌ PostgreSQL configuration incomplete${NC}"
    echo "Please fix the issues above and re-run this script"
    exit 1
fi
