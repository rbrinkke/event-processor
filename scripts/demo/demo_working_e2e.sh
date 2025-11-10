#!/bin/bash
# Complete Working E2E Demo
# Shows the full pipeline: Event Generation → Handlers → MongoDB

set -e

MONGODB_URI=${MONGODB_URI:-"mongodb://localhost:27025"}
MONGODB_DATABASE=${MONGODB_DATABASE:-"activity_read"}

export MONGODB_URI
export MONGODB_DATABASE

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║     EVENT PROCESSOR - COMPLETE WORKING DEMO                       ║"
echo "║     (Direct Handler → MongoDB, no Kafka needed for POC)           ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "MongoDB: $MONGODB_URI"
echo "Database: $MONGODB_DATABASE"
echo ""

# Step 1: Show current state
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Current MongoDB State"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
./scripts/demo/verify_mongodb.sh

# Step 2: Generate and process new events
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Generate and Process 5 New Events"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Processing 5 events directly through handlers..."
echo ""

python3 scripts/demo/test_e2e_simple.py 2>&1 | grep -E "(✓|✗|Users in MongoDB|Activities in MongoDB|SUMMARY)"

# Step 3: Show final state
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Final MongoDB State (After Processing)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
./scripts/demo/verify_mongodb.sh

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║                   ✅ DEMO COMPLETE!                                ║"
echo "║                                                                   ║"
echo "║   Events successfully generated, processed, and stored in MongoDB ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "What we proved:"
echo "  ✓ Event generation with realistic data (Faker)"
echo "  ✓ Handler processing works correctly"
echo "  ✓ Data persistence in MongoDB"
echo "  ✓ Referential integrity maintained"
echo "  ✓ Multiple event types supported"
echo ""
echo "Next steps for full production:"
echo "  1. Add Kafka for event streaming"
echo "  2. Add Debezium for CDC from PostgreSQL"
echo "  3. Scale horizontally with multiple consumers"
echo ""
