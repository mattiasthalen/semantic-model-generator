---
phase: 07-fabric-rest-api-integration
plan: 02
subsystem: fabric-deployment
tags: [fabric-api, deployment, lro-polling, dev-prod-modes, tdd]
dependency-graph:
  requires: [07-01, auth, resolution, packaging]
  provides: [semantic-model-deployment, lro-polling, dev-prod-orchestration]
  affects: [fabric-integration]
tech-stack:
  added: [tenacity]
  patterns: [exponential-backoff, lro-polling, dev-prod-deployment]
key-files:
  created:
    - src/semantic_model_generator/fabric/deployment.py
    - src/semantic_model_generator/fabric/polling.py
    - tests/fabric/test_deployment.py
    - tests/fabric/test_polling.py
  modified:
    - src/semantic_model_generator/fabric/__init__.py
decisions:
  - Tenacity exponential backoff for LRO polling (2-30s wait, max 60 attempts)
  - Dev mode appends UTC timestamp in YYYYMMDDTHHMMSSz format (aligned with Phase 6)
  - Prod mode requires explicit confirm_overwrite=True for existing models
  - Failed LRO operations raise RuntimeError with error code and message details
  - Create and update functions handle both immediate (200/201) and async (202) responses
metrics:
  duration: 332s
  tasks: 2
  tests: 27
  files: 5
  completed: 2026-02-10
---

# Phase 7 Plan 2: Fabric Semantic Model Deployment Summary

**One-liner:** Deployment and LRO polling for Fabric semantic models with exponential backoff, dev/prod modes, and overwrite protection.

## Overview

Implemented complete deployment and long-running operation (LRO) polling for Fabric semantic models. The implementation includes find-by-name lookup, create/update operations with both immediate and async response handling, exponential backoff polling with tenacity, and dev/prod deployment orchestrators with naming conventions aligned to Phase 6 patterns.

## Execution Flow

### Task 1: RED - Write Failing Tests (Commit: 1bae856)

Created comprehensive test coverage for deployment and polling:

**Stub Modules:**
- `fabric/polling.py`: `poll_operation` and `get_operation_result` stubs
- `fabric/deployment.py`: `find_semantic_model_by_name`, `create_semantic_model`, `update_semantic_model_definition`, `deploy_semantic_model_dev`, `deploy_semantic_model_prod` stubs
- Updated `fabric/__init__.py` to export 7 new functions

**Test Coverage:**

`test_polling.py` (7 tests):
- Poll operation succeeds immediately
- Poll operation retries until success (3 attempts)
- Poll operation raises RuntimeError on failure with error details
- Correct endpoint usage (`/operations/{id}`)
- Bearer token in Authorization header
- Get operation result returns JSON
- Get operation result uses correct endpoint (`/operations/{id}/result`)

`test_deployment.py` (20 tests):
- Find existing model by name returns ID
- Find nonexistent model returns None
- Find uses correct endpoint
- Create returns model ID on 201 (immediate)
- Create returns operation ID on 202 (LRO)
- Create sends correct payload (displayName + definition)
- Create uses correct endpoint
- Update returns None on 200 (immediate)
- Update returns operation ID on 202 (LRO)
- Update uses correct endpoint with updateMetadata=True
- Update sends definition payload
- Dev deploy creates model with timestamp name (YYYYMMDDTHHMMSSz format)
- Dev deploy resolves workspace name to GUID
- Dev deploy returns model ID on 201
- Dev deploy polls LRO on 202 and returns result
- Prod deploy raises ValueError without confirmation when model exists
- Prod deploy updates existing model with confirmation
- Prod deploy creates new model if not exists
- Prod deploy uses base name (no timestamp)
- Prod deploy error message includes model name and mentions confirm_overwrite

All 27 new tests failed with NotImplementedError. Existing tests (327 tests) continued to pass.

**Key Decisions:**
- Imported dependencies in stubs for test mocking (requests, auth, resolution, packaging, polling)
- Used proper type annotations (`dict[str, Any]`) to satisfy mypy
- Aligned timestamp format with Phase 6 (`YYYYMMDDTHHMMSSz`)

### Task 2: GREEN - Implement Modules (Commit: 52c2208)

**`fabric/polling.py` Implementation:**

```python
FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"

@retry(
    retry=retry_if_result(_is_still_running),
    stop=stop_after_attempt(60),
    wait=wait_exponential(multiplier=1, min=2, max=30),
)
def poll_operation(operation_id: str, token: str) -> dict[str, Any]:
    # GET /operations/{operation_id}
    # Returns operation dict when status is "Succeeded"
    # Retries when status is "Running"
    # Raises RuntimeError when status is "Failed" with error details

def get_operation_result(operation_id: str, token: str) -> dict[str, Any]:
    # GET /operations/{operation_id}/result
    # Returns result JSON (e.g., created model object)
```

**Polling Strategy:**
- Tenacity `@retry` with `retry_if_result` checks for `status == "Running"`
- Exponential backoff: min 2s, max 30s, multiplier 1
- Max 60 attempts (up to 30 minutes total)
- Failed operations raise RuntimeError with `[{errorCode}] {message}` format

**`fabric/deployment.py` Implementation:**

**Core Functions:**

`find_semantic_model_by_name(workspace_id, model_name, token)`:
- GET `/workspaces/{workspace_id}/semanticModels`
- Filter by `displayName == model_name`
- Returns model ID if found, None otherwise

`create_semantic_model(workspace_id, display_name, definition, token)`:
- POST `/workspaces/{workspace_id}/semanticModels`
- Body: `{displayName, definition}`
- Returns `(model_id, None)` on 201
- Returns `(None, operation_id)` on 202

`update_semantic_model_definition(workspace_id, semantic_model_id, definition, token)`:
- POST `/workspaces/{workspace_id}/semanticModels/{semantic_model_id}/updateDefinition?updateMetadata=True`
- Body: `{definition}`
- Returns `None` on 200
- Returns `operation_id` on 202

**Deployment Orchestrators:**

`deploy_semantic_model_dev(tmdl_files, workspace, model_name)`:
1. Acquire token via `get_fabric_token()`
2. Resolve workspace name to GUID (if not already GUID)
3. Generate timestamped name: `{model_name}_{YYYYMMDDTHHMMSSz}`
4. Package TMDL files via `package_tmdl_for_fabric()`
5. Create semantic model
6. If 202, poll operation and get result
7. Return model ID

`deploy_semantic_model_prod(tmdl_files, workspace, model_name, confirm_overwrite=False)`:
1. Acquire token and resolve workspace
2. Find existing model by name
3. If exists and not `confirm_overwrite`: raise `ValueError` with clear message
4. Package TMDL files
5. If exists: update definition (poll if 202), return existing ID
6. Else: create new model (poll if 202), return new ID

**Type Safety:**
- Explicit type annotations on intermediate variables to satisfy mypy
- Proper handling of `str | None` return types from headers

## Verification Results

**All Quality Gates Passed:**

1. ✅ **Lint (ruff):** All checks passed
2. ✅ **Type check (mypy):** Success, no issues found in 27 source files
3. ✅ **All Tests:** 354 tests passed in 9.02s
   - 27 new deployment/polling tests
   - 327 existing tests (all still passing)

**Fabric Test Suite (55 tests):**
- Auth: 3 tests
- Packaging: 8 tests
- Resolution: 17 tests
- **Deployment: 20 tests** ✅
- **Polling: 7 tests** ✅

**Export Verification:**
```python
from semantic_model_generator.fabric import (
    deploy_semantic_model_dev,
    deploy_semantic_model_prod,
    poll_operation,
    get_operation_result,
    find_semantic_model_by_name,
    create_semantic_model,
    update_semantic_model_definition,
)
# All exports OK
```

**Success Criteria Verification:**

✅ Semantic model creation handles both 201 (immediate) and 202 (LRO) responses
✅ Semantic model update handles both 200 (immediate) and 202 (LRO) responses
✅ LRO polling uses tenacity with exponential backoff (min=2s, max=30s, max 60 attempts)
✅ Failed operations raise RuntimeError with error code and message
✅ Dev mode appends UTC timestamp to model name (format aligned with Phase 6: YYYYMMDDTHHMMSSz)
✅ Prod mode requires explicit confirm_overwrite=True for existing models
✅ Prod mode raises ValueError with clear message including model name and "confirm_overwrite=True"
✅ Find-by-name returns None for nonexistent models, model ID for existing ones
✅ All functions have correct type annotations and docstrings
✅ `make check` clean (lint + typecheck + tests)

## Deviations from Plan

None - plan executed exactly as written.

## Technical Decisions

1. **Tenacity Configuration:** Used `retry_if_result` instead of `retry_if_exception` for cleaner polling logic. The function returns successfully when status is "Succeeded" or raises when "Failed". Only retries when result indicates "Running".

2. **Type Annotations:** Added explicit type annotations on intermediate variables (e.g., `model_id: str`) to help mypy infer correct types from JSON response dictionaries.

3. **Error Message Format:** Used `[{errorCode}] {message}` format for failed LRO operations to provide structured error information from Fabric API.

4. **Timestamp Format:** Aligned dev mode timestamp format with Phase 6 decision (`YYYYMMDDTHHMMSSz`) for consistency across output and deployment layers.

5. **Overwrite Protection:** Clear error message in prod mode that explicitly mentions both the model name and the required parameter (`confirm_overwrite=True`) to guide users toward intentional overwrites.

## Architecture Impact

**Module Relationships:**
```
deployment.py → auth.py (get_fabric_token)
              → resolution.py (is_guid, resolve_workspace_id)
              → packaging.py (package_tmdl_for_fabric)
              → polling.py (poll_operation, get_operation_result)
              → requests (POST create/update)

polling.py → requests (GET status/result)
           → tenacity (exponential backoff retry)
```

**Fabric Module Completeness:**
- ✅ Auth (token acquisition)
- ✅ Resolution (workspace/lakehouse GUID lookup)
- ✅ Packaging (TMDL to base64 parts)
- ✅ Polling (LRO handling)
- ✅ Deployment (create/update/orchestrate)

Phase 7 Fabric REST API integration is now complete. The library can deploy semantic models to Fabric in both dev mode (safe iteration with timestamps) and prod mode (intentional overwrites with confirmation).

## Key Files

**Created:**
- `src/semantic_model_generator/fabric/deployment.py` (200 lines): Core deployment functions and dev/prod orchestrators
- `src/semantic_model_generator/fabric/polling.py` (66 lines): LRO polling with exponential backoff
- `tests/fabric/test_deployment.py` (466 lines): Comprehensive deployment tests
- `tests/fabric/test_polling.py` (96 lines): Comprehensive polling tests

**Modified:**
- `src/semantic_model_generator/fabric/__init__.py`: Added 7 new exports

## Performance Metrics

- **Duration:** 332s (5.5 minutes)
- **Tasks Completed:** 2/2 (100%)
- **Tests Added:** 27 tests
- **Files Modified:** 5 files
- **Test Pass Rate:** 354/354 (100%)
- **Quality Gates:** 3/3 passed (lint, typecheck, tests)

## Next Steps

Phase 7 is complete with both plans finished:
- ✅ Plan 01: Fabric REST API foundation (auth, resolution, packaging)
- ✅ Plan 02: Deployment and LRO polling

**Integration Readiness:**
The Fabric deployment layer can now be integrated with:
1. **Phase 4 (Relationships):** Deploy models with star-schema relationships
2. **Phase 5 (TMDL Generation):** Deploy generated TMDL to Fabric
3. **Phase 6 (Output Layer):** Local write + Fabric deploy in single workflow
4. **Phase 8 (CLI):** Command-line interface for end-to-end generation and deployment

**Recommended Phase 8 Focus:**
CLI commands should expose both dev and prod deployment modes with clear prompts for overwrite confirmation in prod mode.

## Self-Check: PASSED

✅ **Created files exist:**
- src/semantic_model_generator/fabric/deployment.py
- src/semantic_model_generator/fabric/polling.py
- tests/fabric/test_deployment.py
- tests/fabric/test_polling.py

✅ **Commits exist:**
- 1bae856: test(07-02): add failing tests for deployment and polling
- 52c2208: feat(07-02): implement deployment and polling modules

✅ **Tests pass:**
- All 354 tests pass (27 new + 327 existing)
- All quality gates pass (lint, typecheck, tests)

✅ **Exports work:**
- All 7 new functions importable from `semantic_model_generator.fabric`
