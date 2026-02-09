---
phase: 05-tmdl-generation
plan: 01
subsystem: tmdl
tags:
  - tmdl-generation
  - directlake
  - semantic-model
  - tdd
dependency_graph:
  requires:
    - phase-02/utils (whitespace, identifiers, uuid_gen, type_mapping)
    - phase-02/domain (types)
  provides:
    - tmdl/generate module with 6 core generation functions
  affects:
    - None (new module, no existing dependencies)
tech_stack:
  added:
    - Python f-strings for TMDL template generation
    - Composition pattern for section generation
  patterns:
    - TDD (red-green cycle)
    - Composed helper functions for testability
    - Validation before return pattern
key_files:
  created:
    - src/semantic_model_generator/tmdl/__init__.py
    - src/semantic_model_generator/tmdl/generate.py
    - tests/tmdl/__init__.py
    - tests/tmdl/test_generate.py
  modified:
    - None
decisions:
  - Use Python f-strings only, no Jinja2 dependency
  - Hardcode en-US locale in expressions (not configurable)
  - Key columns sorted first, then alphabetically by name
  - Dimensions sorted before facts in model.tmdl ref table list
  - Validate all generated TMDL with whitespace validator before returning
  - DirectLake expression URL is empty string (runtime resolution in Phase 7/8)
  - All generation functions compose from existing Phase 2 utilities
metrics:
  duration_seconds: 311
  completed_date: 2026-02-09
  tasks_completed: 2
  tests_added: 41
  tests_total: 220
  commits: 2
---

# Phase 05 Plan 01: Core TMDL Generation Functions Summary

**One-liner:** Implement 6 core TMDL generation functions (database, model, expressions, columns, partitions, tables) using f-strings, composition, and Phase 2 utilities with comprehensive TDD coverage.

## What Was Built

Created the `tmdl` package with 6 tested generation functions that produce valid TMDL content:

1. **`generate_database_tmdl()`** - Generates database.tmdl with compatibilityLevel 1604
2. **`generate_model_tmdl()`** - Generates model.tmdl with dimension-first table sorting and en-US culture
3. **`generate_expressions_tmdl()`** - Generates DirectLake expression with en-US locale and placeholder URL
4. **`generate_column_tmdl()`** - Generates column definitions with type mapping, UUIDs, and summarizeBy:none
5. **`generate_partition_tmdl()`** - Generates DirectLake partition with entityName, schemaName, expressionSource
6. **`generate_table_tmdl()`** - Composes column and partition sections with key-first column ordering

All functions:
- Use existing Phase 2 utilities (indent_tmdl, quote_tmdl_identifier, validate_tmdl_indentation, generate_deterministic_uuid, map_sql_type_to_tmdl)
- Validate output before returning (whitespace validation)
- Are deterministic (same inputs produce identical output)
- Follow composition pattern (table composes columns + partition)

## Deviations from Plan

None - plan executed exactly as written. All functions implemented with expected signatures, all tests passing, all validation working.

## Test Coverage

**Added 41 new tests** covering all 6 generation functions:

- **database.tmdl tests (3):** Header, compatibilityLevel, whitespace validation
- **model.tmdl tests (8):** Header, properties, ref table lines, dimension-first sorting, alphabetical within classification, special character quoting, whitespace validation, determinism
- **expressions.tmdl tests (6):** DirectLake expression, AzureStorage.DataLake, lineageTag, PBI annotation, en-US locale (Source not Kalla), whitespace validation
- **column tests (8):** Header, dataType, lineageTag, summarizeBy:none, sourceColumn, name quoting, whitespace validation
- **partition tests (6):** Header, mode:directLake, entityName, schemaName, expressionSource, whitespace validation
- **table tests (8):** Header, lineageTag, all columns present, partition section, key columns first, non-key alphabetical, whitespace validation, determinism
- **Determinism tests (2):** Table and model generation produce identical output on repeated calls

**Total test count:** 220 (179 existing + 41 new)
**All tests pass:** Yes (GREEN phase successful)

## Implementation Notes

### TDD Execution

**RED Phase (Task 1):**
- Created stub implementations with NotImplementedError
- Wrote 41 comprehensive tests covering all functions
- All new tests failed (expected)
- All 179 existing tests passed (verified no breakage)
- Commit: e6354e2

**GREEN Phase (Task 2):**
- Implemented all 6 functions using f-strings and Phase 2 utilities
- Fixed Python 3.11 f-string escape sequence issues (backslash not supported)
- All 220 tests pass
- Commit: b623e8a

### Key Technical Decisions

1. **Column ordering:** Key columns first (matching key_prefixes), then remaining columns alphabetically. This matches user decision from CONTEXT.md for predictable, readable output.

2. **Table sorting in model.tmdl:** Dimensions before facts (classification-based primary sort), then alphabetical by (schema_name, table_name) within each group. Ensures dimensions appear first in Power BI.

3. **en-US locale hardcoded:** DirectLake expression uses English "Source" variable name, not Swedish "Kalla". User decision to use en-US for all generated content.

4. **DirectLake URL is empty string:** Actual URL resolved at runtime in Phase 7/8 when deploying to Fabric. Empty string is valid placeholder per research.

5. **Validation before return:** All functions call validate_tmdl_indentation before returning. Catches composition errors early with clear error messages.

6. **Python 3.11 compatibility:** Avoided f-string escape sequences (backslash in f-strings requires Python 3.12). Used intermediate variables for string joins instead.

## Verification

**Linting:** ✅ All ruff checks passed
**Type checking:** ✅ mypy success (17 source files)
**Tests:** ✅ 220/220 passed
**Import verification:** ✅ `from semantic_model_generator.tmdl.generate import ...` successful

### Sample Output Validation

Generated TMDL content verified to:
- Use tab-only indentation (no spaces)
- Include all required properties per TMDL spec
- Quote identifiers with special characters
- Generate deterministic UUIDs
- Map SQL types correctly to TMDL types
- Sort tables by classification (dimension before fact)
- Sort columns by key status (key first, then alphabetical)

## Dependencies

**Imports from Phase 2:**
- `semantic_model_generator.utils.whitespace` - indent_tmdl, validate_tmdl_indentation
- `semantic_model_generator.utils.identifiers` - quote_tmdl_identifier
- `semantic_model_generator.utils.uuid_gen` - generate_deterministic_uuid
- `semantic_model_generator.utils.type_mapping` - map_sql_type_to_tmdl

**Imports from domain:**
- `semantic_model_generator.domain.types` - ColumnMetadata, TableMetadata, TableClassification

**Standard library:**
- `collections.abc.Sequence` - Type hints for list parameters

## Files Changed

**Created (4 files):**
- `src/semantic_model_generator/tmdl/__init__.py` - Package exports
- `src/semantic_model_generator/tmdl/generate.py` - 6 generation functions (279 lines)
- `tests/tmdl/__init__.py` - Test package
- `tests/tmdl/test_generate.py` - 41 comprehensive tests (445 lines)

**Modified:** None

## Commits

1. **e6354e2** - test(05-01): add failing tests for TMDL generation functions (RED)
2. **b623e8a** - feat(05-01): implement TMDL generation functions (GREEN)

## Next Steps

This plan provides the core building blocks for TMDL generation. Future plans in Phase 5 will:
- Implement relationships.tmdl generation (plan 05-02)
- Implement metadata file generation (.platform, definition.pbism) (plan 05-03)
- Implement complete folder structure generation (plan 05-04)
- Add diagram layout generation (plan 05-05)

All 6 functions are ready to be composed into higher-level orchestration functions.

## Self-Check: PASSED

**Created files verification:**
```bash
✅ src/semantic_model_generator/tmdl/__init__.py exists
✅ src/semantic_model_generator/tmdl/generate.py exists
✅ tests/tmdl/__init__.py exists
✅ tests/tmdl/test_generate.py exists
```

**Commits verification:**
```bash
✅ e6354e2 exists - test(05-01): add failing tests for TMDL generation functions
✅ b623e8a exists - feat(05-01): implement TMDL generation functions
```

**Test results verification:**
```bash
✅ 220 tests passed (179 existing + 41 new)
✅ make check passed (lint + typecheck + test)
```

All verification checks passed. Plan 05-01 complete.
