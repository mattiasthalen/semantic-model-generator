---
created: 2026-02-10T23:37:12.000Z
title: Remove unused lakehouse_or_warehouse parameter
area: api
files:
  - src/semantic_model_generator/pipeline.py:75
  - src/semantic_model_generator/pipeline.py:113-114
---

## Problem

`PipelineConfig` requires `lakehouse_or_warehouse` parameter when `output_mode="fabric"`, but this parameter is **never actually used** in the deployment logic.

```python
# Line 75: Parameter defined and validated
lakehouse_or_warehouse: str | None = None

# Lines 113-114: Validation requires it
if self.lakehouse_or_warehouse is None:
    raise ValueError("lakehouse_or_warehouse required when output_mode='fabric'")

# Lines 215-224: Deployment functions DON'T use it!
model_id = deploy_semantic_model_dev(
    tmdl_files, config.workspace, config.model_name  # No lakehouse_or_warehouse!
)
```

**Why it's not needed:**
- Semantic models are deployed to **workspaces**, not lakehouses/warehouses
- The SQL endpoint is only used for schema discovery (not deployment)
- Fabric REST API creates semantic models at workspace level

This creates confusion for users who must provide a meaningless parameter.

## Solution

1. Remove `lakehouse_or_warehouse` parameter from `PipelineConfig`
2. Remove validation logic in `__post_init__` (lines 113-114)
3. Update all tests to remove the parameter
4. Update documentation examples
5. Add migration note in release notes

Breaking change for v0.3.0 (can combine with catalog_name removal).

**Alternative (non-breaking):** Mark as deprecated with warning, remove in v0.3.0.
