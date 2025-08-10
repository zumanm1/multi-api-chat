#!/bin/bash

echo "🚀 Enhanced Multi-API Chat Test Suite"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    
    echo -n "Checking $service_name (port $port)... "
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not running${NC}"
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    echo "Waiting for $service_name to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name is ready${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    echo -e "${RED}✗ $service_name failed to start within ${max_attempts}s${NC}"
    return 1
}

# Pre-flight checks
echo -e "${BLUE}Pre-flight Checks${NC}"
echo "=================="

# Check if Python 3 is installed  
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Python 3 installed: $(python3 --version)${NC}"
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Node.js installed: $(node --version)${NC}"
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null && ! python3 -c "import pytest" &> /dev/null; then
    echo -e "${YELLOW}⚠ Installing pytest...${NC}"
    pip install pytest
fi

echo

# Install dependencies if needed
echo -e "${BLUE}Installing Dependencies${NC}"
echo "======================"

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to install Python dependencies${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Python virtual environment exists${NC}"
    source .venv/bin/activate
fi

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to install Node.js dependencies${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Node.js dependencies already installed${NC}"
fi

echo

# Service startup
echo -e "${BLUE}Starting Services${NC}"
echo "=================="

# Start backend server
echo "Starting backend server..."
source .venv/bin/activate
python3 backend_server.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Start frontend server (simple HTTP server)
echo "Starting frontend server..."
python3 -m http.server 8001 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo

# Wait for services to be ready
echo -e "${BLUE}Waiting for Services${NC}"
echo "==================="

if ! wait_for_service "Backend" "http://localhost:8002/api/health"; then
    echo -e "${RED}Backend server failed to start${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

if ! wait_for_service "Frontend" "http://localhost:8001"; then
    echo -e "${RED}Frontend server failed to start${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

echo

# Run Backend Tests
echo -e "${PURPLE}Running Backend Tests (.env.private & Provider Testing)${NC}"
echo "========================================================="

echo "Executing Python backend tests..."
source .venv/bin/activate

# Run the enhanced backend tests
python -m pytest test_env_private_backend.py -v --tb=short
BACKEND_TEST_EXIT_CODE=$?

if [ $BACKEND_TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Backend tests passed${NC}"
else
    echo -e "${RED}❌ Backend tests failed${NC}"
fi

echo

# Run Enhanced Frontend Tests  
echo -e "${PURPLE}Running Enhanced Frontend Tests (Puppeteer)${NC}"
echo "============================================="

echo "Executing enhanced Puppeteer integration tests..."

# Run the enhanced Puppeteer tests
node enhanced_puppeteer_tests_fixed.js
FRONTEND_TEST_EXIT_CODE=$?

if [ $FRONTEND_TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend tests passed${NC}"
else
    echo -e "${RED}❌ Frontend tests failed${NC}"
fi

echo

# Optional: Run Original Integration Tests for Comparison
echo -e "${PURPLE}Running Original Integration Tests (Comparison)${NC}"
echo "================================================"

if [ -f "final_integration_test.js" ]; then
    echo "Executing original integration tests for comparison..."
    node final_integration_test.js
    COMPARISON_TEST_EXIT_CODE=$?
    
    if [ $COMPARISON_TEST_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ Comparison tests passed${NC}"
    else
        echo -e "${RED}❌ Comparison tests failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Original integration test file not found, skipping comparison${NC}"
    COMPARISON_TEST_EXIT_CODE=0
fi

echo

# Cleanup
echo -e "${BLUE}Cleaning Up${NC}"
echo "==========="

echo "Stopping services..."
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
sleep 2

# Force kill if still running
pkill -f "backend_server.py" 2>/dev/null
pkill -f "python3 -m http.server 8001" 2>/dev/null

echo -e "${GREEN}✓ Services stopped${NC}"

echo

# Final results summary
echo -e "${BLUE}📊 Test Results Summary${NC}"
echo "======================"

echo "Backend Tests (.env.private & Provider Testing):"
if [ $BACKEND_TEST_EXIT_CODE -eq 0 ]; then
    echo -e "  ${GREEN}✅ PASSED${NC}"
else
    echo -e "  ${RED}❌ FAILED${NC}"
fi

echo "Enhanced Frontend Tests (Puppeteer):"
if [ $FRONTEND_TEST_EXIT_CODE -eq 0 ]; then
    echo -e "  ${GREEN}✅ PASSED${NC}"
else
    echo -e "  ${RED}❌ FAILED${NC}"
fi

echo "Original Integration Tests (Comparison):"
if [ $COMPARISON_TEST_EXIT_CODE -eq 0 ]; then
    echo -e "  ${GREEN}✅ PASSED${NC}"
else
    echo -e "  ${RED}❌ FAILED${NC}"
fi

echo

# Show report locations
echo -e "${BLUE}📋 Generated Reports${NC}"
echo "==================="

echo "Enhanced Test Reports:"
if [ -f "enhanced_test_reports/enhanced_test_report.html" ]; then
    echo -e "  ${GREEN}📄 HTML Report: enhanced_test_reports/enhanced_test_report.html${NC}"
fi
if [ -f "enhanced_test_reports/enhanced_test_report.json" ]; then
    echo -e "  ${GREEN}📄 JSON Report: enhanced_test_reports/enhanced_test_report.json${NC}"
fi

echo "Backend Test Output:"
echo -e "  ${GREEN}📄 Check console output above for pytest results${NC}"

if [ -f "test_reports/final_integration_report.html" ]; then
    echo "Comparison Test Reports:"
    echo -e "  ${GREEN}📄 HTML Report: test_reports/final_integration_report.html${NC}"
fi

echo

# Overall result
TOTAL_FAILURES=$((BACKEND_TEST_EXIT_CODE + FRONTEND_TEST_EXIT_CODE + COMPARISON_TEST_EXIT_CODE))

if [ $TOTAL_FAILURES -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL ENHANCED TESTS PASSED!${NC}"
    echo -e "${GREEN}✨ Your Multi-API Chat application with .env.private support is working perfectly!${NC}"
    echo
    echo -e "${BLUE}✅ Key Features Validated:${NC}"
    echo "   • Enhanced provider testing with raw input/output data"
    echo "   • Secure .env.private file management for API keys"
    echo "   • Provider configuration save/edit/remove functionality"
    echo "   • Test button shows success/failure with detailed results"
    echo "   • Support for Cerebras, OpenRouter, Groq, and Ollama providers"
    echo "   • Frontend-backend integration for provider management"
    
    EXIT_CODE=0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "${YELLOW}⚠ Check the reports above for detailed failure information${NC}"
    echo -e "${YELLOW}📋 Review enhanced_test_reports/ for comprehensive analysis${NC}"
    
    EXIT_CODE=1
fi

echo
echo -e "${BLUE}Enhanced Test Runner Complete${NC}"
echo "============================"

exit $EXIT_CODE
