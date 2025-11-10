#!/bin/bash
# Verify Demo Results - Check MongoDB Data Integrity

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "DEMO VERIFICATION"
echo "=========================================="

python3 <<EOF
import sys
sys.path.insert(0, "$LIB_DIR")

from mongodb_verifier import MongoDBVerifier
import json

print("Connecting to MongoDB...")
verifier = MongoDBVerifier()

print("Running verification checks...\n")

# Run full verification (without expected counts for now)
results = verifier.run_full_verification()

# Print report
verifier.print_verification_report(results)

# Export to JSON
output_file = "demo_verification.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n✓ Verification results exported to {output_file}")

verifier.cleanup()

# Exit with appropriate code
sys.exit(0 if results["passed"] else 1)
EOF

VERIFICATION_RESULT=$?

if [ $VERIFICATION_RESULT -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ VERIFICATION PASSED${NC}"
else
    echo ""
    echo -e "${RED}✗ VERIFICATION FAILED - Check results above${NC}"
fi

exit $VERIFICATION_RESULT
