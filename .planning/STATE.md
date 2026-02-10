# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-09)

**Core value:** Given a Fabric warehouse and a key prefix, automatically produce a correct, deployable TMDL semantic model with proper dimension/fact classification and star-schema relationships.
**Current focus:** Phase 6 - Output Layer

## Current Position

Phase: 6 of 8 (Output Layer)
Plan: 1 of 2 complete
Status: In Progress
Branch: gsd/phase-06-output-layer
Last activity: 2026-02-10 -- Completed 06-01: Watermark generation, detection, atomic file writing, and WriteSummary

Progress: [████████░░] 50.0% (5 of 8 phases complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 10
- Average duration: 4.9 min
- Total execution time: 1.19 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 1 | 268s | 268s |
| 02 | 2 | 670s | 335s |
| 03 | 3 | 879s | 293s |
| 04 | 1 | 250s | 250s |
| 05 | 2 | 712s | 356s |
| 06 | 1 | 219s | 219s |

**Recent Trend:**
- Last 5 plans: 04-01 (250s), 05-01 (311s), 05-02 (401s), 06-01 (219s)
- Trend: Phase 6 started with efficient TDD execution (3.7 min), watermark and atomic write foundation

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
- [04-01]: **CRITICAL FIX**: Relationship matching uses startswith() on full column names (no prefix stripping)
- [04-01]: Both fact and dimension use same prefix (e.g., ID_Customer in both; role-playing: ID_Customer_BillTo)
- [04-01]: Role-playing requires underscore boundary validation (prevents CustomerRegion matching Customer)
- [04-01]: Exact-match columns (name equals prefix) produce no relationships and are excluded from grouping
- [04-01]: Role-playing match requires underscore boundary after dimension base name (prevents false positives)
- [04-01]: Exact-match columns (name equals prefix) produce no relationships and are excluded from role-playing grouping
- [04-01]: First relationship by sorted from_column is active, rest inactive for role-playing dimensions
- [04-01]: Relationship IDs use composite pattern: relationship:{from_qualified}.{from_col}->{to_qualified}.{to_col}
- [05-01]: Use Python f-strings for TMDL generation, no Jinja2 dependency
- [05-01]: Hardcode en-US locale in expressions.tmdl (not configurable)
- [05-01]: Column sorting: key columns first, then alphabetically by name
- [05-01]: Table sorting in model.tmdl: dimensions first, then facts, alphabetical within classification
- [05-01]: Validate all generated TMDL with whitespace validator before returning
- [05-01]: DirectLake expression URL is empty string (runtime resolution in Phase 7/8)
- [05-01]: All TMDL generation functions compose from existing Phase 2 utilities
- [05-02]: Relationship fromColumn/toColumn: table names always single-quoted, columns unquoted ('TableName'.ColumnName)
- [05-02]: Active relationships omit isActive property (default true), inactive include isActive: false
- [05-02]: Relationships sorted: active first, then by (from_table, from_column, to_table, to_column)
- [05-02]: definition.pbism includes model name, description, version, author, timestamps per user requirement
- [05-02]: Diagram layout: facts vertical column, dimensions horizontal row(s), deterministic positioning
- [05-02]: generate_all_tmdl uses fixed timestamp for deterministic output (production uses actual time)
- [06-01]: Use datetime.UTC instead of timezone.utc (Python 3.11+ modern API)
- [06-01]: Simple string containment for watermark detection (not regex) for predictability
- [06-01]: TMDL-style watermark as safe default for unknown file extensions
- [06-01]: JSON watermark uses _comment field inserted as first key
- [06-01]: Atomic writes use tempfile.mkstemp + os.replace pattern for crash safety

### Pending Todos

None yet.

### Blockers/Concerns

- [Research]: TMDL Python examples are sparse (most tooling is .NET-based); may need extra validation in Phase 5
- [Research - RESOLVED]: Role-playing dimension automation implemented successfully with underscore boundary pattern
- [Research]: Fabric REST API connection binding for cross-environment deployment needs practical validation in Phase 7

## Session Continuity

Last session: 2026-02-10
Stopped at: Completed 06-01-PLAN.md - Watermark generation, detection, atomic file writing, and WriteSummary
Resume file: .planning/phases/06-output-layer/06-01-SUMMARY.md
