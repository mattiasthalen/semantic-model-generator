.DEFAULT_GOAL := help

.PHONY: help
help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

.PHONY: claude
claude:  ## Run Claude with full permissions
	claude --dangerously-skip-permissions