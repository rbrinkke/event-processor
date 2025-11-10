#!/bin/bash
# Load Test: 10 Events (Warm-up)
# Quick test to verify the pipeline works

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║  LOAD TEST: 10 EVENTS (WARM-UP)         ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Purpose: Verify pipeline functionality"
echo "Expected duration: ~5 seconds"
echo ""

$SCRIPT_DIR/run_load_test.sh 10 10 100

echo ""
echo "✓ Warm-up complete!"
echo "  Wait 5-10 seconds for processing to complete"
echo "  Then run: ./scripts/demo/verify.sh"
echo ""
