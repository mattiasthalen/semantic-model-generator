---
created: 2026-02-10T23:24:29.097Z
title: Remove catalog_name parameter redundancy
area: api
files:
  - src/semantic_model_generator/pipeline.py:63
  - src/semantic_model_generator/tmdl/generate.py
---

## Problem

`PipelineConfig` requires both `database` (line 55) and `catalog_name` (line 63) parameters, but in Fabric warehouses these are always the same value. Users must redundantly specify:

```python
config = PipelineConfig(
    database="WH_Gold",
    catalog_name="WH_Gold",  # Same as database!
    ...
)
```

This creates unnecessary confusion and violates DRY principle. The catalog name in TMDL generation should simply use the database name since they're identical in Fabric.

## Solution

1. Remove `catalog_name` from `PipelineConfig` dataclass
2. Update `generate_all_tmdl()` to accept `database` instead of `catalog_name`
3. Update all call sites in `pipeline.py` to pass `config.database`
4. Update all tests to remove `catalog_name` parameter
5. Add migration note in next version's release notes

Breaking change for v0.3.0.
