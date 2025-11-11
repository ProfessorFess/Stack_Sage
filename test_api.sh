#!/bin/bash
# API Testing Script for Stack Sage
# Tests all API endpoints

API_URL="http://localhost:8000"

echo "========================================"
echo "Stack Sage API Test Suite"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo "Testing: $name"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
        ((FAILED++))
    fi
    
    # Show response preview
    echo "$body" | head -c 150
    echo "..."
    echo ""
}

# Check if server is running
echo "Checking if API server is running..."
if curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Server is running${NC}"
else
    echo -e "${RED}❌ Server is not running${NC}"
    echo "Please start the server first:"
    echo "  python backend/api/server.py"
    exit 1
fi
echo ""

# Test 1: Health check
test_endpoint "Health Check" "GET" "/health" ""

# Test 2: Root endpoint
test_endpoint "Root Endpoint" "GET" "/" ""

# Test 3: Examples
test_endpoint "Get Examples" "GET" "/examples" ""

# Test 4: Formats
test_endpoint "Get Formats" "GET" "/formats" ""

# Test 5: Ask simple question
test_endpoint "Ask Simple Question" "POST" "/ask" \
    '{"question": "What is Lightning Bolt?"}'

# Test 6: Ask complex question
test_endpoint "Ask Complex Question" "POST" "/ask" \
    '{"question": "How does Dockside Extortionist work with Spark Double?"}'

# Test 7: Ask controller logic question
test_endpoint "Ask Controller Logic Question" "POST" "/ask" \
    '{"question": "If my opponent controls Blood Artist and a creature dies, what happens?"}'

# Test 8: Validate valid deck
test_endpoint "Validate Valid Deck" "POST" "/validate_deck" \
    '{"decklist": "4 Lightning Bolt\n4 Counterspell\n52 Island", "format": "modern"}'

# Test 9: Validate invalid deck (too many copies)
test_endpoint "Validate Invalid Deck" "POST" "/validate_deck" \
    '{"decklist": "5 Lightning Bolt\n55 Island", "format": "modern"}'

# Test 10: Validate Commander deck
test_endpoint "Validate Commander Deck" "POST" "/validate_deck" \
    '{"decklist": "1 Sol Ring\n99 Island", "format": "commander"}'

# Test 11: Get meta (may not have cached data)
echo "Testing: Get Meta Data"
response=$(curl -s -w "\n%{http_code}" "$API_URL/meta/standard")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    echo -e "${YELLOW}⚠️  PASS${NC} (HTTP $http_code) - May not have cached data"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
    ((FAILED++))
fi
echo "$body" | head -c 150
echo "..."
echo ""

# Summary
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "Total: $((PASSED + FAILED))"
echo "========================================"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

