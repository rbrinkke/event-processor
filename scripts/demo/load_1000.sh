#!/bin/bash
# Load Test: 1,000 Events (Stress Test)
# System under load

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║  LOAD TEST: 1,000 EVENTS (STRESS)       ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Purpose: System performance under load"
echo "Expected duration: ~30 seconds"
echo ""

$SCRIPT_DIR/run_load_test.sh 1000 100 0

echo ""
echo "✓ Stress test complete!"
echo "  Wait 20-30 seconds for processing to complete"
echo "  Then run: ./scripts/demo/verify.sh"
echo ""
