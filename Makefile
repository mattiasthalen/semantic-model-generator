.DEFAULT_GOAL := help

.PHONY: help
help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.PHONY: claude
claude:  ## Run Claude with full permissions
	claude --dangerously-skip-permissions

.PHONY: install
install:  ## Install package in editable mode and development tools
	pip install -e .
	pip install ruff mypy pytest pytest-cov pre-commit
	pre-commit install --install-hooks

.PHONY: lint
lint:  ## Run ruff linting on source and tests
	ruff check src tests

.PHONY: format
format:  ## Run ruff formatting on source and tests
	ruff format src tests

.PHONY: typecheck
typecheck:  ## Run mypy type checking on source
	mypy src

.PHONY: test
test:  ## Run pytest test suite
	pytest

.PHONY: check
check: lint typecheck test  ## Run all quality checks (lint, typecheck, test)
	@echo "All checks passed!"

.PHONY: clean
clean:  ## Remove build artifacts and cache directories
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
