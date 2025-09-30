.PHONY: help install test test-all lint format type-check clean coverage

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r dev-requirements.txt

test: ## Run fast tests
	python3 -m pytest -m "not slow" --cov=jafgen --cov-report=term-missing

test-all: ## Run all tests including slow ones
	python3 -m pytest --cov=jafgen --cov-report=term-missing --cov-report=html --cov-report=xml

lint: ## Run linting
	python3 -m ruff check jafgen/

format: ## Format code
	python3 -m black jafgen/
	python3 -m isort jafgen/ --profile black

format-check: ## Check code formatting
	python3 -m black --check --diff jafgen/
	python3 -m isort --check-only --diff jafgen/ --profile black

type-check: ## Run type checking
	python3 -m mypy jafgen/ --config-file pyproject.toml

quality: format-check type-check lint ## Run all code quality checks

clean: ## Clean up generated files
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

coverage: ## Generate coverage report
	python3 -m pytest --cov=jafgen --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"