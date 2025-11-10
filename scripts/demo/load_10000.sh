#!/bin/bash
# Load Test: 10,000 Events (Extreme Load)
# Find system limits

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║  LOAD TEST: 10,000 EVENTS (EXTREME)     ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Purpose: Maximum throughput testing"
echo "Expected duration: ~60 seconds"
echo ""

$SCRIPT_DIR/run_load_test.sh 10000 200 0

echo ""
echo "✓ Extreme load test complete!"
echo "  Wait 1-2 minutes for processing to complete"
echo "  Then run: ./scripts/demo/verify.sh"
echo ""
