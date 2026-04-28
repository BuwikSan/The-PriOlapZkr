#!/bin/bash
# Master Test Runner for OLAP System
# Runs all tests in sequence and generates final report

set -e

echo "🚀 OLAP System - Master Test Runner"
echo "===================================="
echo "Test Suite: Complete OLAP Validation"
echo "Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Change to test directory
cd "$(dirname "$0")"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0

# Function to run a test
run_test() {
    local test_name=$1
    local test_file=$2

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Test: ${test_name}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [ -f "$test_file" ]; then
        if python3 "$test_file"; then
            echo -e "${GREEN}✅ $test_name - PASSED${NC}"
            ((PASSED++))
        else
            echo -e "${RED}❌ $test_name - FAILED${NC}"
            ((FAILED++))
        fi
    else
        echo -e "${YELLOW}⚠️  $test_file not found${NC}"
        ((FAILED++))
    fi
}

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Run tests
echo ""
echo -e "${YELLOW}Running test suite...${NC}"
echo ""

run_test "OLAP Query Test Suite" "test_queries.py"
run_test "ROLAP Operations Verification" "test_rolap_operations.py"
run_test "OLAP System Report" "test_olap_report.py"

# Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

TOTAL=$((PASSED + FAILED))

echo "Tests Passed: $PASSED"
echo "Tests Failed: $FAILED"
echo "Total Tests:  $TOTAL"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}OLAP System is ready for production.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  Some tests failed - see output above${NC}"
    exit 1
fi
