.PHONY: install test lint format binary example icons clean help

# Repo root is the parent of .iblai/
ROOT_DIR := $(shell cd .. && pwd)

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

install: ## Install in editable mode with dev dependencies
	pip install -e ".[dev]"

test: ## Run the test suite
	pytest tests/ -v --tb=short

lint: ## Run linters (black check + flake8)
	black --check iblai/ tests/
	flake8 iblai/ tests/

format: ## Auto-format code with black
	black iblai/ tests/

# ---------------------------------------------------------------------------
# Binary build (current platform)
# ---------------------------------------------------------------------------

binary: ## Build standalone binary for the current platform
	bash scripts/build-binary.sh

# ---------------------------------------------------------------------------
# Example app
# ---------------------------------------------------------------------------

example: ## Regenerate the example app at examples/iblai-agent-app
	bash scripts/refresh-example.sh

# ---------------------------------------------------------------------------
# Icons
# ---------------------------------------------------------------------------

icons: ## Regenerate template icons from docs/iblai-logo.png
	bash scripts/generate-icons.sh

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Remove build artifacts
	rm -rf dist/ build/ *.spec .venv-build/
	rm -rf htmlcov/ .pytest_cache/ .mypy_cache/
	cd $(ROOT_DIR) && rm -rf dist/ build/ *.spec
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
