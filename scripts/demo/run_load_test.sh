#!/bin/bash
# Run Load Test - Generate and Insert Events
# Usage: ./run_load_test.sh <num_events> [batch_size] [delay_ms]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# Parameters
NUM_EVENTS=${1:-100}
BATCH_SIZE=${2:-100}
DELAY_MS=${3:-0}

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "LOAD TEST: $NUM_EVENTS events"
echo "=========================================="
echo "Batch size: $BATCH_SIZE"
echo "Delay between batches: ${DELAY_MS}ms"
echo ""

# Generate and insert events
python3 <<EOF
import sys
sys.path.insert(0, "$LIB_DIR")

from event_generator import EventGenerator
from postgres_inserter import PostgresInserter
import time

print("Generating $NUM_EVENTS events...")
generator = EventGenerator()
events = generator.generate_batch($NUM_EVENTS)
print(f"✓ Generated {len(events)} events\n")

print("Connecting to PostgreSQL...")
inserter = PostgresInserter()
inserter.connect()

if not inserter.verify_connection():
    print("✗ Cannot connect to PostgreSQL")
    sys.exit(1)

print("\nInserting events into event_outbox...")
start_time = time.time()

stats = inserter.insert_events_batch(
    events,
    batch_size=$BATCH_SIZE,
    delay_ms=$DELAY_MS
)

elapsed = time.time() - start_time

print(f"\n✓ Load test complete!")
print(f"  Inserted: {stats['inserted']} events")
print(f"  Time: {elapsed:.2f}s")
print(f"  Rate: {stats['events_per_second']:.2f} events/sec")

# Show event breakdown
print(f"\nEvent breakdown:")
breakdown = inserter.count_events_by_type()
for event_type, count in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / stats['inserted']) * 100
    print(f"  {event_type}: {count} ({percentage:.1f}%)")

inserter.disconnect()
EOF

echo ""
echo -e "${GREEN}✓ Events inserted into PostgreSQL${NC}"
echo ""
echo "Next steps:"
echo "  1. Wait for Debezium to capture changes (~5 seconds)"
echo "  2. Check Kafka topic: postgres.activity.event_outbox"
echo "  3. Monitor event processor logs"
echo "  4. Run verification: ./scripts/demo/verify.sh"
echo ""
