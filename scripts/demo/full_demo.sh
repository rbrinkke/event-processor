#!/bin/bash
# Full Demo - Complete Demonstration Sequence
# Runs all load tests in sequence with verification

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

clear

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║       EVENT PROCESSOR - COMPLETE DEMO SEQUENCE             ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "This demo will:"
echo "  1. Setup environment"
echo "  2. Run warm-up (10 events)"
echo "  3. Run moderate load (100 events)"
echo "  4. Run stress test (1,000 events)"
echo "  5. Run extreme load (10,000 events)"
echo "  6. Verify all results"
echo ""
echo "Total estimated time: ~2.5 minutes"
echo ""
echo -n "Press Enter to start..."
read

# Step 1: Setup
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  STEP 1/6: Environment Setup${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
$SCRIPT_DIR/setup.sh

echo ""
echo -n "Press Enter to continue to warm-up test..."
read

# Step 2: Warm-up
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  STEP 2/6: Warm-up Test (10 events)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
$SCRIPT_DIR/load_10.sh

echo ""
echo "Waiting 10 seconds for processing..."
sleep 10

# Step 3: Moderate load
echo ""
echo -n "Press Enter to continue to moderate load test..."
read

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  STEP 3/6: Moderate Load (100 events)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
$SCRIPT_DIR/load_100.sh

echo ""
echo "Waiting 15 seconds for processing..."
sleep 15

# Step 4: Stress test
echo ""
echo -n "Press Enter to continue to stress test..."
read

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  STEP 4/6: Stress Test (1,000 events)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
$SCRIPT_DIR/load_1000.sh

echo ""
echo "Waiting 30 seconds for processing..."
sleep 30

# Step 5: Extreme load
echo ""
echo -n "Press Enter to continue to extreme load test..."
read

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  STEP 5/6: Extreme Load (10,000 events)${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
$SCRIPT_DIR/load_10000.sh

echo ""
echo "Waiting 60 seconds for processing..."
sleep 60

# Step 6: Verification
echo ""
echo -n "Press Enter to run final verification..."
read

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  STEP 6/6: Final Verification${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
$SCRIPT_DIR/verify.sh

VERIFICATION_RESULT=$?

echo ""
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
if [ $VERIFICATION_RESULT -eq 0 ]; then
    echo -e "║       ${GREEN}✓ DEMO COMPLETE - ALL CHECKS PASSED${NC}              ║"
else
    echo -e "║       ${YELLOW}⚠ DEMO COMPLETE - SOME CHECKS FAILED${NC}            ║"
fi
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Results saved to:"
echo "  - demo_verification.json"
echo "  - demo_metrics.json (if exported)"
echo ""
echo "Total events processed: 11,110"
echo "  - Warm-up: 10"
echo "  - Moderate: 100"
echo "  - Stress: 1,000"
echo "  - Extreme: 10,000"
echo ""
echo "Thank you for watching the demo!"
echo ""
