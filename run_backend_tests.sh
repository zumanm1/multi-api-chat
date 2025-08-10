#!/bin/bash

# Simple Backend Test Runner for Multi-API Chat Platform
# This script runs pytest tests with coverage reporting

set -e

PROJECT_DIR="$(pwd)"
VENV_PATH="${PROJECT_DIR}/.venv"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}[INFO]${NC} Running backend pytest tests..."

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${BLUE}[INFO]${NC} Creating virtual environment..."
    python3.11 -m venv "$VENV_PATH"
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Install/upgrade dependencies
echo -e "${BLUE}[INFO]${NC} Installing/upgrading Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -r requirements-testing.txt

# Create test reports directory
mkdir -p test-reports/backend

# Run comprehensive backend tests
echo -e "${BLUE}[INFO]${NC} Running pytest tests..."
pytest tests/test_comprehensive_backend.py \
    -v \
    --tb=short \
    --maxfail=10 \
    --durations=10 \
    --cov=backend_server \
    --cov-report=html:test-reports/backend/coverage \
    --cov-report=term-missing \
    --junit-xml=test-reports/backend/junit.xml

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}[SUCCESS]${NC} All backend tests passed!"
    echo -e "${BLUE}[INFO]${NC} Coverage report: test-reports/backend/coverage/index.html"
    echo -e "${BLUE}[INFO]${NC} JUnit XML: test-reports/backend/junit.xml"
else
    echo -e "${RED}[ERROR]${NC} Backend tests failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
