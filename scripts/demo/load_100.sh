#!/bin/bash
# Load Test: 100 Events (Moderate Load)
# Standard operational test

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║  LOAD TEST: 100 EVENTS (MODERATE)       ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Purpose: Typical operation simulation"
echo "Expected duration: ~15 seconds"
echo ""

$SCRIPT_DIR/run_load_test.sh 100 50 50

echo ""
echo "✓ Moderate load test complete!"
echo "  Wait 10-15 seconds for processing to complete"
echo "  Then run: ./scripts/demo/verify.sh"
echo ""
