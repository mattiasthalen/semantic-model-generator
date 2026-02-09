# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-09)

**Core value:** Given a Fabric warehouse and a key prefix, automatically produce a correct, deployable TMDL semantic model with proper dimension/fact classification and star-schema relationships.
**Current focus:** Phase 4 - Relationship Inference

## Current Position

Phase: 4 of 8 (Relationship Inference)
Plan: 1 of 1 in current phase
Status: Complete
Branch: gsd/phase-04-relationship-inference
Last activity: 2026-02-09 -- Phase 4 Plan 1 complete (relationship inference)

Progress: [████░░░░░░] 100.0% (Phase 4 complete - all 1 plans executed)

## Performance Metrics

**Velocity:**
- Total plans completed: 7
- Average duration: 4.8 min
- Total execution time: 0.92 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 1 | 268s | 268s |
| 02 | 2 | 670s | 335s |
| 03 | 3 | 879s | 293s |
| 04 | 1 | 250s | 250s |

**Recent Trend:**
- Last 5 plans: 03-01 (271s), 03-02 (336s), 03-03 (272s), 04-01 (250s)
- Trend: Phase 4 plan at 4.2 min, maintaining efficiency from Phase 3

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 8 phases derived from 32 requirements; depth=quick but project complexity warrants 8 phases (natural delivery boundaries)
- [Roadmap]: Phase 1 is build system first (greenfield project, no source code yet)
- [Roadmap]: Phases 6 and 7 can execute in parallel (both depend on Phase 5, independent of each other)
- [Settings]: Git branching strategy set to per-phase (gsd/phase-{N}-{slug})
- [01-01]: Use hatchling instead of setuptools for modern build backend with native VCS versioning
- [01-01]: Install dev tools separately rather than as optional-dependencies to keep build-system.requires minimal
- [01-01]: Ignore all ruff rules for auto-generated _version.py (uses deprecated typing syntax)
- [01-01]: Exclude .references, .claude, .planning from pre-commit hooks (reference materials, not source code)
- [02-plan]: All phase work (research, plans, code) must be committed on phase branch, never main
- [02-plan]: Version tags (v0.1.0 etc.) created only at milestone completion, not per-phase
- [02-01]: Use frozen=True, slots=True for all domain dataclasses (memory efficiency, immutability, hashability)
- [02-01]: TmdlDataType enum values match TMDL spec exactly (int64, double, boolean, string, dateTime, decimal, binary)
- [02-01]: Type mapping function normalizes input (lowercase, strip) for case-insensitive matching
- [02-01]: ValueError with helpful message listing all supported types for unsupported SQL types
- [02-02]: Use NamedTuple TmdlIndentationError instead of exception for composability in validation pipelines
- [02-02]: Preserve object_name case in UUID generation (source systems may be case-sensitive)
- [02-02]: Tab-only indentation validation (TMDL spec requires tabs, spaces are always wrong)
- [03-01]: Case-sensitive exact name matching for table filtering (not pattern/glob matching)
- [03-01]: Include filter applied first, then exclude filter
- [03-01]: Key prefix matching is case-sensitive using startswith() for consistency
- [03-01]: Batch classification returns (schema_name, table_name) tuple keys for multi-schema uniqueness
- [03-02]: Use DefaultAzureCredential for token acquisition (supports multiple auth methods)
- [03-02]: Rely on SQL ORDER BY for column ordering (not Python-level sorting)
- [03-02]: Empty schema list returns empty tuple without executing query (defensive check)
- [03-03]: Use mssql-python instead of pyodbc (Microsoft's official GA driver, DDBC with no ODBC Manager dependency)
- [03-03]: Use ActiveDirectoryDefault authentication in connection string (driver handles DefaultAzureCredential internally)
- [03-03]: Install Linux system libraries (libltdl7, libkrb5-3, libgssapi-krb5-2) for mssql-python support
- [04-01]: Role-playing match requires underscore boundary after dimension base name (prevents false positives)
- [04-01]: Exact-match columns (name equals prefix) produce no relationships and are excluded from role-playing grouping
- [04-01]: First relationship by sorted from_column is active, rest inactive for role-playing dimensions
- [04-01]: Relationship IDs use composite pattern: relationship:{from_qualified}.{from_col}->{to_qualified}.{to_col}

### Pending Todos

None yet.

### Blockers/Concerns

- [Research]: TMDL Python examples are sparse (most tooling is .NET-based); may need extra validation in Phase 5
- [Research - RESOLVED]: Role-playing dimension automation implemented successfully with underscore boundary pattern
- [Research]: Fabric REST API connection binding for cross-environment deployment needs practical validation in Phase 7

## Session Continuity

Last session: 2026-02-09
Stopped at: Completed 04-01-PLAN.md (relationship inference) - Phase 4 complete (all 1 plans executed)
Resume file: .planning/phases/04-relationship-inference/04-01-SUMMARY.md
