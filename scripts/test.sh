#!/bin/bash

# Test runner script with different configurations

set -e

echo "Running code quality checks..."

# Format check
echo "Checking code formatting with black..."
python3 -m black --check --diff jafgen/

# Import sorting check
echo "Checking import sorting with isort..."
python3 -m isort --check-only --diff jafgen/

# Type checking
echo "Running type checking with mypy..."
python3 -m mypy jafgen/ --config-file pyproject.toml || echo "Type checking completed with issues"

# Linting
echo "Running linting with ruff..."
python3 -m ruff check jafgen/

echo "Running tests..."

# Fast tests only (exclude slow tests)
echo "Running fast tests..."
python3 -m pytest -m "not slow" --cov=jafgen --cov-report=term-missing

# All tests (including slow ones)
if [ "$1" = "--all" ]; then
    echo "Running all tests including slow ones..."
    python3 -m pytest --cov=jafgen --cov-report=term-missing --cov-report=html --cov-report=xml
fi

echo "Test run completed!"