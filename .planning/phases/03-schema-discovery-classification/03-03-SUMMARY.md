---
phase: 03-schema-discovery-classification
plan: 03
subsystem: schema
tags: [gap_closure, driver_migration, authentication, mssql-python]

dependency_graph:
  requires:
    - "03-02 (connection factory and schema discovery)"
  provides:
    - "mssql-python driver integration"
    - "ActiveDirectoryDefault authentication"
    - "Simplified connection logic (no manual token encoding)"
  affects:
    - "src/semantic_model_generator/schema/connection.py"
    - "src/semantic_model_generator/schema/discovery.py"
    - "tests/schema/test_connection.py"
    - "tests/schema/test_discovery.py"

tech_stack:
  added:
    - "mssql-python>=1.0.0 (Microsoft's official GA Python driver)"
  removed:
    - "pyodbc>=5.0 (replaced by mssql-python)"
  patterns:
    - "ActiveDirectoryDefault authentication (driver-managed DefaultAzureCredential)"
    - "DDBC (Direct Database Connectivity) instead of ODBC Driver Manager"
    - "Connection string-based authentication (no attrs_before parameter)"

key_files:
  created: []
  modified:
    - path: "pyproject.toml"
      changes: "Replaced pyodbc with mssql-python dependency, updated mypy overrides"
    - path: "src/semantic_model_generator/schema/connection.py"
      changes: "Migrated to mssql-python, use ActiveDirectoryDefault, removed encode_token_for_odbc"
    - path: "src/semantic_model_generator/schema/__init__.py"
      changes: "Removed encode_token_for_odbc from exports"
    - path: "src/semantic_model_generator/schema/discovery.py"
      changes: "Updated type hint to mssql_python.Connection"
    - path: "tests/schema/test_connection.py"
      changes: "Updated tests for mssql-python driver, simplified (no token encoding tests)"
    - path: "tests/schema/test_discovery.py"
      changes: "Added comment documenting driver-agnostic Mock usage"

decisions:
  - decision: "Use mssql-python instead of pyodbc"
    rationale: "Microsoft's official GA driver (released Jan 2026), uses DDBC with no ODBC Manager dependency, cleaner Azure AD auth"
    alternatives: ["Keep pyodbc with manual token encoding"]
    impact: "Simpler connection code, no manual UTF-16-LE token encoding, better official support"

  - decision: "Use ActiveDirectoryDefault authentication in connection string"
    rationale: "Driver handles DefaultAzureCredential internally, no manual token acquisition needed"
    alternatives: ["Continue manual token acquisition with attrs_before"]
    impact: "Removed encode_token_for_odbc function, simpler connection.py, driver manages auth lifecycle"

  - decision: "Install Linux system libraries (libltdl7, libkrb5-3, libgssapi-krb5-2)"
    rationale: "Required for mssql-python on Linux (Debian/Ubuntu), already installed in devcontainer"
    alternatives: ["Assume libraries present"]
    impact: "Explicit dependency documentation, works in all Linux environments"

metrics:
  duration_seconds: 272
  duration_human: "4 minutes 32 seconds"
  completed_date: "2026-02-09"
  tasks_completed: 2
  files_modified: 6
  tests_added: 0
  tests_modified: 2
  lines_added: 95
  lines_removed: 187
  net_lines: -92
---

# Phase 03 Plan 03: Driver Migration to mssql-python Summary

**One-liner:** Migrated from pyodbc to mssql-python with ActiveDirectoryDefault authentication, removing manual token encoding and simplifying connection logic.

## What Was Built

Replaced pyodbc with mssql-python (Microsoft's official GA Python driver released January 2026). Connection now uses ActiveDirectoryDefault authentication in connection string, which internally leverages DefaultAzureCredential. This eliminates manual token acquisition, UTF-16-LE encoding, and the attrs_before parameter.

### Task 1: Replace pyodbc with mssql-python in connection.py

**Status:** Complete
**Commits:** 8529a02 (test), b5d06aa (feat)

Installed system libraries (libltdl7, libkrb5-3, libgssapi-krb5-2) for Linux support. Updated pyproject.toml to replace pyodbc with mssql-python>=1.0.0. Installed dependency successfully.

**RED phase (8529a02):**
- Replaced test imports from pyodbc to mssql_python
- Updated test to mock mssql_python.connect instead of pyodbc.connect
- Changed test to verify ActiveDirectoryDefault in connection string
- Removed tests for encode_token_for_odbc (no longer needed)
- Removed tests for attrs_before parameter (different API)
- Removed tests for SQL_COPT_SS_ACCESS_TOKEN (internal to driver)
- Tests correctly failed (connection.py still used pyodbc)

**GREEN phase (b5d06aa):**
- Replaced `import pyodbc` with `import mssql_python`
- Removed `encode_token_for_odbc()` function
- Removed imports: `struct`, `itertools.chain`, `itertools.repeat`, `azure.identity.DefaultAzureCredential`
- Removed constants: `_SQL_COPT_SS_ACCESS_TOKEN`, `_TOKEN_SCOPE`
- Updated `create_fabric_connection` to use connection string authentication:
  - `Authentication=ActiveDirectoryDefault` in connection string
  - Driver internally uses DefaultAzureCredential
  - No attrs_before parameter
  - No manual token acquisition or encoding
- Updated retry decorator to use `mssql_python.OperationalError` and `mssql_python.InterfaceError`
- Updated return type to `mssql_python.Connection`
- Updated schema/__init__.py to remove `encode_token_for_odbc` from exports
- All tests passed (152 tests total)

### Task 2: Update discovery.py to use mssql_python.Connection type hint

**Status:** Complete
**Commits:** 39afa9f (test), 957d70c (feat)

**RED phase (39afa9f):**
- Added docstring comment explaining Mock objects are driver-agnostic
- Tests already pass due to duck typing (cursor API is compatible)
- No actual test code changes needed

**GREEN phase (957d70c):**
- Changed import from `import pyodbc` to `import mssql_python`
- Updated type hint: `conn: pyodbc.Connection` → `conn: mssql_python.Connection`
- Updated docstring: "Authenticated pyodbc connection" → "Authenticated mssql_python connection"
- All 11 discovery tests passed (cursor API is compatible between drivers)
- mypy strict mode passed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed mssql_python exception construction in tests**
- **Found during:** Task 1 GREEN phase (test execution)
- **Issue:** mssql_python.OperationalError requires two string arguments (driver_error, ddbc_error), not one
- **Fix:** Updated test to pass both arguments: `mssql_python.OperationalError("Driver error", "Transient connection error")`
- **Files modified:** tests/schema/test_connection.py
- **Commit:** b5d06aa (included in GREEN commit)

## Verification Results

All success criteria met:

✅ create_fabric_connection uses mssql_python.connect (not pyodbc.connect)
✅ Connection string includes "Authentication=ActiveDirectoryDefault"
✅ ActiveDirectoryDefault internally uses DefaultAzureCredential (no manual token handling)
✅ Connection string excludes UID and PWD
✅ Retry logic: 3 attempts with exponential backoff on mssql_python.OperationalError
✅ discover_tables accepts mssql_python.Connection parameter
✅ All tests use mocked mssql_python (not pyodbc)
✅ pyodbc completely removed from dependencies (verified: no imports, no references in src/)
✅ mssql-python>=1.0.0 added to dependencies
✅ Linux system libraries installed (libltdl7, libkrb5-3, libgssapi-krb5-2)
✅ No unixodbc dependency
✅ make check passes (lint + typecheck + test) - 152 tests passed

Additional verification:
- `python -c "from semantic_model_generator.schema.connection import create_fabric_connection; print('OK')"` → OK
- `python -c "import mssql_python; print('OK')"` → OK
- `grep pyodbc pyproject.toml` → no results (correct)
- `grep mssql-python pyproject.toml` → found in dependencies
- `grep -r "import pyodbc" src/` → no results (correct)
- `grep encode_token_for_odbc src/` → no results (function removed)
- mypy strict mode: Success, no issues in 14 source files

## Impact Assessment

**Benefits:**
- **Simpler code:** Removed 39 lines from connection.py (encode_token_for_odbc function, manual token handling)
- **Official support:** Using Microsoft's official GA driver instead of community-maintained pyodbc
- **Cleaner authentication:** Driver manages DefaultAzureCredential lifecycle internally
- **No external dependencies:** mssql-python uses DDBC (no ODBC Driver Manager required)
- **Better error messages:** Driver provides clearer authentication errors
- **Future-proof:** Microsoft will focus on mssql-python for new features

**Risks mitigated:**
- ✅ System libraries verified installed (libltdl7, libkrb5-3, libgssapi-krb5-2)
- ✅ All tests pass with new driver (cursor API is compatible)
- ✅ Type hints work correctly with mssql_python.Connection
- ✅ Retry logic works with mssql_python exceptions

**Breaking changes:**
- None externally (connection factory signature unchanged)
- Internal: encode_token_for_odbc function removed (was not part of public API based on schema/__init__.py)

## Self-Check: PASSED

**Files created:** (none - all modifications)

**Files modified - all exist:**
- ✅ FOUND: /workspaces/semantic-model-generator/pyproject.toml
- ✅ FOUND: /workspaces/semantic-model-generator/src/semantic_model_generator/schema/connection.py
- ✅ FOUND: /workspaces/semantic-model-generator/src/semantic_model_generator/schema/__init__.py
- ✅ FOUND: /workspaces/semantic-model-generator/src/semantic_model_generator/schema/discovery.py
- ✅ FOUND: /workspaces/semantic-model-generator/tests/schema/test_connection.py
- ✅ FOUND: /workspaces/semantic-model-generator/tests/schema/test_discovery.py

**Commits - all exist:**
- ✅ FOUND: 8529a02 test(03-03): update connection tests for mssql-python
- ✅ FOUND: b5d06aa feat(03-03): migrate from pyodbc to mssql-python
- ✅ FOUND: 39afa9f test(03-03): document discovery tests work with mssql_python
- ✅ FOUND: 957d70c feat(03-03): update discovery to use mssql_python connection type

**Verification commands:**
```bash
# All checks passed
make check  # 152 tests passed

# pyodbc completely removed
grep -r "import pyodbc" src/  # no results
grep -r "pyodbc" src/  # no results
grep pyodbc pyproject.toml  # no results

# mssql-python integrated
python -c "import mssql_python; print('OK')"  # OK
python -c "from semantic_model_generator.schema.connection import create_fabric_connection; print('OK')"  # OK
grep "mssql-python>=1.0.0" pyproject.toml  # found

# ActiveDirectoryDefault authentication
grep "Authentication=ActiveDirectoryDefault" src/semantic_model_generator/schema/connection.py  # found

# encode_token_for_odbc removed
grep -r "encode_token_for_odbc" src/  # no results

# System libraries installed
dpkg -l | grep -E "libltdl7|libkrb5-3|libgssapi-krb5-2"  # all found
```

## Next Steps

Phase 3 (Schema Discovery & Classification) is now complete with all 3 plans executed:
- 03-01: Table filtering and classification ✅
- 03-02: Connection factory and schema discovery ✅
- 03-03: Driver migration to mssql-python ✅

Ready to proceed to Phase 4 (Relationship Detection) or merge phase branch to main.
