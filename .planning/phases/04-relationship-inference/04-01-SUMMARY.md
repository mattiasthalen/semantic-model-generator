---
phase: 04-relationship-inference
plan: 01
subsystem: relationship-inference
tags: [relationships, star-schema, role-playing-dimensions, fact-dimension-matching, deterministic-uuid]

# Dependency graph
requires:
  - phase: 03-schema-discovery-classification
    provides: TableMetadata, TableClassification, classify_tables function
  - phase: 02-domain-types-utilities
    provides: Domain types infrastructure, deterministic UUID generation
provides:
  - Relationship frozen dataclass for star-schema relationships
  - infer_relationships() function for fact-to-dimension matching
  - Role-playing dimension detection (same dimension multiple roles)
  - Active/inactive relationship marking for first vs subsequent role-playing references
  - Exact-match prefix bypass for edge cases
affects: [05-tmdl-generation, integration-testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Base name matching for fact-to-dimension relationships (exact match + role-playing prefix match)"
    - "Deterministic relationship IDs via uuid5 with composite name pattern"
    - "Role-playing detection via grouping by (from_table, to_table) with sorted column ordering"

key-files:
  created:
    - src/semantic_model_generator/schema/relationships.py
    - tests/schema/test_relationships.py
  modified:
    - src/semantic_model_generator/domain/types.py
    - src/semantic_model_generator/schema/__init__.py

key-decisions:
  - "Role-playing match requires underscore boundary (CustomerID_BillTo matches CustomerID, but CustomerIDRegion does not)"
  - "Exact-match columns (column name equals prefix exactly) produce no relationships and are excluded from role-playing grouping"
  - "First relationship by sorted from_column is active, rest are inactive when same fact references same dimension multiple times"
  - "Relationship IDs use composite pattern: relationship:{from_qualified}.{from_col}->{to_qualified}.{to_col}"

patterns-established:
  - "Helper functions (strip_prefix, is_exact_match) extracted for testability and reuse"
  - "Frozen dataclass pattern for relationships (immutable, requires recreation for is_active toggling)"
  - "Deterministic sorting by (from_table, from_column, to_table, to_column) for stable output"

# Metrics
duration: 4min
completed: 2026-02-09
---

# Phase 04 Plan 01: Relationship Inference Summary

**Star-schema relationship inference with role-playing dimension support, active/inactive marking, and deterministic UUID generation**

## Performance

- **Duration:** 4 min 10 sec (250s)
- **Started:** 2026-02-09T21:10:08Z
- **Completed:** 2026-02-09T21:14:18Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 4

## Accomplishments
- Relationship frozen dataclass with proper defaults for star-schema many-to-one joins
- strip_prefix() and is_exact_match() helper functions for key prefix handling
- infer_relationships() implements all 4 requirements (REQ-06, REQ-07, REQ-08, REQ-09)
- 27 comprehensive tests covering basic matching, role-playing, active/inactive, exact-match bypass, and deterministic output
- All 179 tests pass with full TDD discipline (RED → GREEN)

## Task Commits

Each task was committed atomically following TDD protocol:

1. **Task 1: RED - Write failing tests** - `9a86aef` (test)
   - Added Relationship dataclass to domain/types.py
   - Created stub relationships.py with NotImplementedError
   - Created 27 comprehensive tests
   - All new tests fail with NotImplementedError (RED)
   - All 152 existing tests still pass

2. **Task 2: GREEN - Implement relationship inference** - `2b15fc1` (feat)
   - Implemented strip_prefix() with first-matching-prefix logic
   - Implemented is_exact_match() with membership check
   - Implemented infer_relationships() with full algorithm:
     - Fact-to-dimension matching via base name equality
     - Role-playing via base name prefix matching with underscore boundary check
     - Active/inactive marking via grouping and sorted column ordering
     - Exact-match bypass (empty base name produces no relationships)
     - Deterministic UUID generation and output sorting
   - Updated schema/__init__.py exports
   - All 27 new tests pass (GREEN)
   - All 179 total tests pass

## Files Created/Modified
- `src/semantic_model_generator/domain/types.py` - Added Relationship frozen dataclass with uuid.UUID id, from/to table/column, is_active flag, and cardinality/filtering defaults
- `src/semantic_model_generator/schema/relationships.py` - Complete relationship inference module with strip_prefix, is_exact_match, and infer_relationships functions
- `src/semantic_model_generator/schema/__init__.py` - Exported Relationship and infer_relationships
- `tests/schema/test_relationships.py` - 27 comprehensive tests covering all requirements and edge cases

## Decisions Made

**1. Role-playing match boundary validation**
- **Decision:** Require underscore boundary after dim_base in fact_base for role-playing match
- **Rationale:** Prevents false positives like "CustomerRegion" matching dimension "Customer" when not actually role-playing
- **Pattern:** `fact_base.startswith(dim_base) and fact_base[len(dim_base)] == "_"`

**2. Exact-match columns bypass relationship inference**
- **Decision:** Columns named exactly as a prefix (e.g., "FK_") produce no relationships
- **Rationale:** Empty base name after stripping can't match any dimension, so skip entirely
- **Impact:** Also excluded from role-playing grouping to avoid counting as third relationship

**3. Active/inactive determination via sorted column names**
- **Decision:** When multiple fact columns reference same dimension, sort by from_column and mark first active, rest inactive
- **Rationale:** Ensures deterministic output and follows star-schema convention of one active relationship per dimension
- **Implementation:** Group by (from_table, to_table), sort each group, recreate inactive relationships (frozen dataclass)

**4. Relationship ID composite pattern**
- **Decision:** Use `generate_deterministic_uuid("relationship", f"{from_qualified}.{from_col}->{to_qualified}.{to_col}")`
- **Rationale:** Fully qualified pattern ensures global uniqueness even across schemas, enables relationship recreation with same UUID
- **Stability:** Same inputs always produce same UUID (REQ-12)

## Deviations from Plan

None - plan executed exactly as written. All tests designed in Task 1 passed in Task 2 without implementation changes.

## Issues Encountered

None - implementation followed test specification cleanly. Role-playing matching algorithm with underscore boundary check handled all edge cases correctly on first implementation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 5 (TMDL Generation):**
- Relationship dataclass is ready to serialize to TMDL relationship blocks
- infer_relationships() provides complete relationship graph for semantic model
- Deterministic UUIDs ensure stable TMDL output across regenerations
- All cardinality and cross-filtering defaults match TMDL spec expectations

**No blockers or concerns.** Relationship inference is complete and tested.

## Self-Check: PASSED

All claims verified:
- ✓ Created files exist: relationships.py, test_relationships.py
- ✓ Commits exist: 9a86aef (Task 1), 2b15fc1 (Task 2)
- ✓ Test count accurate: 27 tests in test_relationships.py
- ✓ All 179 total tests pass

---
*Phase: 04-relationship-inference*
*Completed: 2026-02-09*
