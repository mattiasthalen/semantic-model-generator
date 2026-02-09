---
phase: 03-schema-discovery-classification
plan: 02
subsystem: schema-io
tags: [connection, discovery, pyodbc, azure-identity, information-schema, tdd]
dependencies:
  requires:
    - domain/types (ColumnMetadata, TableMetadata)
  provides:
    - schema/connection (create_fabric_connection, encode_token_for_odbc)
    - schema/discovery (discover_tables)
  affects:
    - schema module exports (added connection and discovery functions)
tech-stack:
  added:
    - pyodbc (5.3.0) - ODBC database connectivity
    - azure-identity (1.25.1) - Azure authentication
    - tenacity (9.1.4) - retry logic with exponential backoff
    - unixodbc system libraries - ODBC driver manager
  patterns:
    - Token-based authentication via SQL_COPT_SS_ACCESS_TOKEN
    - UTF-16-LE encoding for ODBC token format
    - Dependency injection (pyodbc.Connection as parameter)
    - Mocked database tests (no real database required)
    - INFORMATION_SCHEMA queries with parameterized filtering
key-files:
  created:
    - src/semantic_model_generator/schema/connection.py
    - src/semantic_model_generator/schema/discovery.py
    - tests/schema/test_connection.py
    - tests/schema/test_discovery.py
  modified:
    - src/semantic_model_generator/schema/__init__.py (added connection and discovery exports)
    - pyproject.toml (dependencies already present from previous work)
decisions:
  - "Use DefaultAzureCredential for token acquisition (supports multiple auth methods)"
  - "Install unixodbc system libraries via apt-get (required for pyodbc native extension)"
  - "Use real pyodbc exception classes in retry test for tenacity decorator compatibility"
  - "Rely on SQL ORDER BY for column ordering (not Python-level sorting)"
  - "Empty schema list returns empty tuple without executing query (defensive check)"
metrics:
  duration: 336s
  tasks_completed: 2
  files_created: 4
  tests_added: 19
  completed: 2026-02-09
---

# Phase 03 Plan 02: Connection Factory and Schema Discovery Summary

**One-liner:** Fabric warehouse connection with DefaultAzureCredential token auth and INFORMATION_SCHEMA discovery returning immutable TableMetadata tuples

## What Was Built

Implemented the I/O boundary for schema discovery:

1. **Connection Factory** (`connection.py`):
   - `encode_token_for_odbc()`: UTF-16-LE encoding with 4-byte length prefix for pyodbc
   - `create_fabric_connection()`: Token-based pyodbc connection using DefaultAzureCredential
   - Retry logic: 3 attempts with exponential backoff (2-10s) on OperationalError/InterfaceError
   - Connection string: ODBC Driver 18, Encrypt=Yes, TrustServerCertificate=No
   - Excludes Authentication/UID/PWD parameters (token passed via attrs_before)

2. **Schema Discovery** (`discovery.py`):
   - `discover_tables()`: Reads INFORMATION_SCHEMA.TABLES + COLUMNS
   - Filters TABLE_TYPE = 'BASE TABLE' (excludes views per REQ-29)
   - Parameterized schema filtering (IN clause with placeholders)
   - Returns `tuple[TableMetadata, ...]` with correctly populated ColumnMetadata
   - Handles nullable mapping (YES/NO → bool)
   - Handles NULL values in max_length, numeric_precision, numeric_scale
   - SQL ORDER BY ensures columns in ordinal position order

## Test Coverage

**Connection Tests (8 tests):**
- Token encoding (simple, empty, longer tokens)
- DefaultAzureCredential invocation with correct scope
- Connection string format validation
- Token passed via attrs_before (1256 = SQL_COPT_SS_ACCESS_TOKEN)
- Retry on transient errors (3 attempts)
- Connection object return

**Discovery Tests (11 tests):**
- Single table with multiple columns
- Multiple tables in same schema
- Tables across multiple schemas
- Query contains BASE TABLE filter
- Parameterized schema filtering
- Column ordinal ordering (via SQL ORDER BY)
- Empty result set handling
- Nullable mapping (YES/NO)
- NULL value handling (optional fields)
- Immutable return types (tuple)
- Empty schema list short-circuit

All tests use mocks (no actual database required).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing unixodbc system libraries**
- **Found during:** Task 1 test execution
- **Issue:** pyodbc import failed with "libodbc.so.2: cannot open shared object file"
- **Fix:** Installed unixodbc and unixodbc-dev via apt-get
- **Files modified:** System packages (not tracked in git)
- **Commit:** Part of 099c270 (feat commit includes note about system library installation)

**2. [Rule 1 - Bug] Retry test exception class incompatibility**
- **Found during:** Task 1 test execution
- **Issue:** Mock exception class wasn't caught by tenacity retry decorator
- **Fix:** Used real pyodbc.OperationalError/InterfaceError classes in test mocks
- **Files modified:** tests/schema/test_connection.py
- **Commit:** 099c270

**3. [Rule 1 - Bug] Test ordinal ordering assumption**
- **Found during:** Task 2 test execution
- **Issue:** Test mocked rows in non-ordinal order but SQL ORDER BY guarantees order
- **Fix:** Updated test to provide rows in correct order (as SQL would return)
- **Files modified:** tests/schema/test_discovery.py
- **Commit:** 17b6344

## Success Criteria Met

- [x] create_fabric_connection uses DefaultAzureCredential + token encoding + pyodbc.connect with attrs_before
- [x] encode_token_for_odbc produces correct UTF-16-LE bytes with struct.pack length prefix
- [x] Connection string uses ODBC Driver 18, excludes auth params (UID/PWD/Authentication)
- [x] Retry logic: 3 attempts with exponential backoff on OperationalError/InterfaceError
- [x] discover_tables joins INFORMATION_SCHEMA.TABLES + COLUMNS with TABLE_TYPE='BASE TABLE'
- [x] Schema filtering via parameterized IN clause
- [x] Returns tuple[TableMetadata, ...] with correctly populated ColumnMetadata
- [x] All tests written BEFORE implementation (TDD commits prove RED then GREEN)
- [x] make check passes (lint + typecheck + test)
- [x] pyodbc, azure-identity, tenacity added to dependencies

## Integration Points

**Upstream dependencies:**
- `domain.types.TableMetadata` and `ColumnMetadata` (immutable dataclasses)
- pyodbc, azure-identity, tenacity (external libraries)

**Downstream consumers (future plans):**
- Phase 3 remaining plans will use `discover_tables()` as data source
- Phase 4 relationship detection will use discovered TableMetadata
- Phase 5+ will use connection factory for database access

**Module exports:**
```python
from semantic_model_generator.schema import (
    create_fabric_connection,
    encode_token_for_odbc,
    discover_tables,
)
```

## Technical Notes

**Token Auth Pattern:**
The pyodbc token auth requires a specific encoding:
1. Get OAuth token from DefaultAzureCredential
2. Encode as UTF-8 bytes
3. Convert to UTF-16-LE (each byte interleaved with 0x00)
4. Prefix with 4-byte little-endian integer of length
5. Pass via attrs_before dict with key 1256

**Discovery Query:**
```sql
SELECT t.TABLE_SCHEMA, t.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, ...
FROM INFORMATION_SCHEMA.TABLES t
INNER JOIN INFORMATION_SCHEMA.COLUMNS c
  ON t.TABLE_SCHEMA = c.TABLE_SCHEMA AND t.TABLE_NAME = c.TABLE_NAME
WHERE t.TABLE_TYPE = 'BASE TABLE'
  AND t.TABLE_SCHEMA IN (?, ?, ...)
ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION
```

**Testing Strategy:**
All tests use `unittest.mock` to avoid requiring actual database:
- Mock pyodbc.connect and DefaultAzureCredential for connection tests
- Mock cursor.fetchall() return values for discovery tests
- Verify query structure by inspecting cursor.execute() call args

## Commits

1. `8f43884` - test(03-02): add failing tests for connection factory (RED - previous session)
2. `099c270` - feat(03-02): implement connection factory with token auth (GREEN Task 1)
3. `f7a3a0e` - test(03-02): add failing tests for schema discovery (RED Task 2)
4. `17b6344` - feat(03-02): implement schema discovery with view filtering (GREEN Task 2)

## Next Steps

Plan 03-02 complete. Ready for Phase 3 Plan 3 (if any) or Phase 3 integration/wrap-up.

The schema discovery pipeline now has:
- ✅ Connection factory (03-02)
- ✅ Discovery reader (03-02)
- ✅ Table filtering (03-01)
- ✅ Table classification (03-01)

All core schema discovery components are implemented and tested.

## Self-Check: PASSED

**Files verified:**
- ✓ src/semantic_model_generator/schema/connection.py
- ✓ src/semantic_model_generator/schema/discovery.py
- ✓ tests/schema/test_connection.py
- ✓ tests/schema/test_discovery.py

**Commits verified:**
- ✓ 099c270 (feat connection factory)
- ✓ f7a3a0e (test discovery)
- ✓ 17b6344 (feat discovery)

**Dependencies verified:**
- ✓ pyodbc 5.3.0
- ✓ azure-identity 1.25.1
- ✓ tenacity 9.1.4
- ✓ unixodbc system libraries

All claims in summary verified successfully.
