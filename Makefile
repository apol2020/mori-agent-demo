.PHONY: help setup install install-dev run test test-unit test-integration test-ui lint format clean check-all

# Default target
help:
	@echo "Available commands:"
	@echo "  setup           - Setup development environment"
	@echo "  install         - Install production dependencies"
	@echo "  install-dev     - Install development dependencies"
	@echo "  run             - Run Streamlit application"
	@echo "  test            - Run all tests"
	@echo "  test-unit       - Run unit tests only"
	@echo "  test-integration- Run integration tests only"
	@echo "  test-ui         - Run UI tests only"
	@echo "  lint            - Run linting (Ruff)"
	@echo "  format          - Format code (Black + isort)"
	@echo "  type-check      - Run type checking (mypy)"
	@echo "  check-all       - Run all quality checks"
	@echo "  clean           - Clean cache and temporary files"

# Environment setup
setup: install-dev
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	@echo "Development environment setup complete!"

install:
	pip install -e .

install-dev:
	pip install -e .[dev]

# Application
run:
	@echo "Starting Streamlit application..."
	PYTHONPATH=. streamlit run src/app.py --server.headless=true

# Testing
test:
	@echo "Running all tests..."
	PYTHONPATH=. pytest -v

test-unit:
	@echo "Running unit tests..."
	PYTHONPATH=. pytest tests/unit/ -v -m unit

test-integration:
	@echo "Running integration tests..."
	PYTHONPATH=. pytest tests/integration/ -v -m integration

test-ui:
	@echo "Running UI tests..."
	PYTHONPATH=. pytest tests/ui/ -v -m ui

# Code quality
lint:
	@echo "Running Ruff linting..."
	ruff check src/ tests/ --line-length=120

format:
	@echo "Running Ruff auto-fixes (includes import sorting)..."
	ruff check src/ tests/ --fix --unsafe-fixes --line-length=120
	@echo "Formatting code with Black..."
	black src/ tests/

type-check:
	@echo "Running type checking with mypy..."
	PYTHONPATH=. mypy src/

check-all: lint type-check test
	@echo "All quality checks completed!"

# Cleanup
clean:
	@echo "Cleaning up cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Cleanup completed!"

# 単一ファイル用（環境変数 FILE を渡す）
.PHONY: format-one format-one-generic format-one-python format-one-yaml format-one-toml

# 汎用フォーマット（全ファイル対象）
format-one-generic:
	@if [ -z "$(FILE)" ]; then echo "Usage: make format-one-generic FILE=path/to/file"; exit 1; fi
	@echo "Applying generic formatting to $(FILE)..."
	@# trailing-whitespace
	@sed -i 's/[[:space:]]*$$//' "$(FILE)" 2>/dev/null || true
	@# end-of-file-fixer
	@if [ -s "$(FILE)" ]; then \
		tail -c1 "$(FILE)" | read -r _ || echo >> "$(FILE)"; \
	fi

# Pythonファイル用フォーマット
format-one-python:
	@if [ -z "$(FILE)" ]; then echo "Usage: make format-one-python FILE=path/to/file.py"; exit 1; fi
	@echo "Formatting Python file $(FILE)..."
	@ruff check "$(FILE)" --fix --unsafe-fixes --line-length=120 2>/dev/null || true
	@black "$(FILE)" 2>/dev/null || true

# YAMLファイル用チェック
format-one-yaml:
	@if [ -z "$(FILE)" ]; then echo "Usage: make format-one-yaml FILE=path/to/file.yaml"; exit 1; fi
	@echo "Checking YAML file $(FILE)..."
	@python -c "import yaml; yaml.safe_load(open('$(FILE)'))" 2>/dev/null || echo "Warning: YAML validation failed for $(FILE)"

# TOMLファイル用チェック
format-one-toml:
	@if [ -z "$(FILE)" ]; then echo "Usage: make format-one-toml FILE=path/to/file.toml"; exit 1; fi
	@echo "Checking TOML file $(FILE)..."
	@python -c "import tomli; tomli.load(open('$(FILE)', 'rb'))" 2>/dev/null || \
	 python -c "import tomllib; tomllib.load(open('$(FILE)', 'rb'))" 2>/dev/null || \
	 echo "Warning: TOML validation failed for $(FILE)"

# 後方互換性のため、format-oneはformat-one-pythonと同じ動作
format-one: format-one-python


# Development helpers
dev-server:
	@echo "Starting development server with auto-reload..."
	PYTHONPATH=. streamlit run src/app.py \
		--server.runOnSave=true \
		--server.fileWatcherType=poll \
		--server.headless=true

init-db:
	@echo "Initializing database..."
	PYTHONPATH=. python scripts/init_db.py
