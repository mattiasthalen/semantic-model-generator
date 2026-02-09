---
phase: 02-domain-types-core-utilities
plan: 02
subsystem: utils
tags: [tdd, pure-functions, utilities, uuid, identifiers, whitespace]
dependency_graph:
  requires: []
  provides:
    - deterministic-uuid-generation
    - tmdl-identifier-quoting
    - tmdl-whitespace-validation
  affects: [phase-03, phase-04, phase-05, phase-06, phase-07]
tech_stack:
  added: []
  patterns: [tdd, pure-functions, stdlib-only, named-tuple-errors]
key_files:
  created:
    - src/semantic_model_generator/utils/uuid_gen.py
    - src/semantic_model_generator/utils/identifiers.py
    - src/semantic_model_generator/utils/whitespace.py
    - tests/utils/test_uuid_gen.py
    - tests/utils/test_identifiers.py
    - tests/utils/test_whitespace.py
  modified:
    - src/semantic_model_generator/utils/__init__.py
decisions:
  - decision: "Use NamedTuple TmdlIndentationError instead of exception for composability"
    rationale: "Validation returns list of errors for batch processing, not exceptions"
    alternatives: ["Custom exception class", "Simple dict"]
    impact: "Enables composable validation pipelines"
  - decision: "Preserve object_name case in UUID generation"
    rationale: "Source systems may be case-sensitive, must preserve exact casing"
    alternatives: ["Lowercase all names"]
    impact: "Different case names produce different UUIDs (expected behavior)"
  - decision: "Tab-only indentation validation (no mixed tab/space detection)"
    rationale: "TMDL spec requires tabs, spaces are always wrong"
    alternatives: ["Detect mixed indentation", "Allow configurable indentation"]
    impact: "Simple binary validation: tabs = good, spaces = bad"
metrics:
  duration: 409
  tasks_completed: 2
  tests_written: 60
  files_created: 6
  commits: 3
  completed_date: 2026-02-09
---

# Phase 02 Plan 02: Core Utility Functions Summary

**One-liner:** Pure-function utilities for deterministic UUID generation (uuid5), TMDL identifier quoting (special char handling with quote escaping), and tab-only whitespace validation (structured error reporting).

## What Was Built

Three independent utility modules following TDD methodology:

1. **uuid_gen.py** - Deterministic UUID generation via uuid5
   - Project-specific namespace constant for stable IDs across regenerations
   - Input normalization: strip whitespace, lowercase object_type
   - Case preservation for object_name (source systems may be case-sensitive)
   - Collision avoidance: different types/names produce different UUIDs
   - Satisfies REQ-12 (stable regeneration)

2. **identifiers.py** - TMDL identifier quoting and unquoting
   - Detects special characters: spaces, dots, equals, colons, quotes, tabs
   - Wraps in single quotes when needed, escapes internal quotes by doubling
   - Unquoting reverses process, unescapes doubled quotes
   - Round-trip guarantee: unquote(quote(x)) == x
   - Satisfies REQ-30 (valid TMDL output)

3. **whitespace.py** - TMDL whitespace validation
   - Detects space indentation (TMDL requires tabs)
   - Returns structured TmdlIndentationError list (not exceptions)
   - indent_tmdl(N) helper generates N tabs
   - Composable validation for batch processing
   - Satisfies REQ-30 (valid TMDL output)

## TDD Execution Evidence

All features implemented using strict RED → GREEN → REFACTOR:

| Feature | RED Commit | GREEN Commit | Tests |
|---------|------------|--------------|-------|
| UUID generation | 25447c6 (plan 01) | fe0fd9a | 16 |
| Identifier quoting | 3a38235 | 06755e8 | 24 |
| Whitespace validation | 3a38235 | 06755e8 | 20 |

Total: 60 tests, all passing.

## Deviations from Plan

**None** - Plan executed exactly as written. No bugs found, no missing functionality, no blocking issues.

## Verification Results

All success criteria satisfied:

- ✓ `generate_deterministic_uuid("table", "X") == generate_deterministic_uuid("table", "X")` for any X
- ✓ Different types/names produce different UUIDs
- ✓ `quote_tmdl_identifier` handles all 5 special character types (space, dot, equals, colon, quote, tab)
- ✓ `unquote_tmdl_identifier(quote_tmdl_identifier(name)) == name` for all valid names
- ✓ `validate_tmdl_indentation` returns empty list for tab-indented content
- ✓ `validate_tmdl_indentation` returns non-empty list for space-indented content
- ✓ `indent_tmdl(N)` returns exactly N tab characters
- ✓ `make check` passes (lint, typecheck, 92 tests)
- ✓ All functions are pure (no side effects, no mutable state)
- ✓ Zero external dependencies (stdlib only: uuid, re, typing)

## Impact Assessment

**Immediate impact:**
- Phase 03 (domain models) can use UUID generation for object IDs
- Phase 05 (TMDL generators) can use identifier quoting and whitespace helpers
- All downstream phases benefit from stable, predictable IDs

**Future phases affected:**
- Phase 03: Table/Column models will use generate_deterministic_uuid
- Phase 04: Relationship models will use generate_deterministic_uuid
- Phase 05: TMDL generators will use all three modules heavily
- Phase 06: Warehouse metadata will use quote_tmdl_identifier for schema/table names
- Phase 07: End-to-end generation will use all utilities

## Performance Notes

- UUID generation: O(1), < 1µs per call (SHA-1 hash)
- Identifier quoting: O(n) where n = identifier length
- Whitespace validation: O(n) where n = content length
- All functions suitable for high-throughput batch processing

## Self-Check: PASSED

Verified all claimed artifacts exist:

```bash
✓ src/semantic_model_generator/utils/uuid_gen.py
✓ src/semantic_model_generator/utils/identifiers.py
✓ src/semantic_model_generator/utils/whitespace.py
✓ tests/utils/test_uuid_gen.py
✓ tests/utils/test_identifiers.py
✓ tests/utils/test_whitespace.py
```

Verified all commits exist:

```bash
✓ fe0fd9a: feat(02-02): implement deterministic UUID generation
✓ 3a38235: test(02-02): add failing tests for identifier quoting and whitespace validation
✓ 06755e8: feat(02-02): implement identifier quoting and whitespace validation
```

All imports work:

```bash
✓ from semantic_model_generator.utils import generate_deterministic_uuid
✓ from semantic_model_generator.utils import quote_tmdl_identifier
✓ from semantic_model_generator.utils import validate_tmdl_indentation
```

All tests pass: 92/92 (60 from this plan + 32 from previous plans).
