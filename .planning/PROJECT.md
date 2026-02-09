# Semantic Model Generator

## What This Is

A Python package (distributed via PyPI) that generates TMDL semantic models for Microsoft Fabric. Users import it in Fabric notebooks, point it at a warehouse's INFORMATION_SCHEMA, and it automatically classifies tables as dimensions or facts based on key column prefixes, infers star-schema relationships, and outputs a complete TMDL semantic model — either written to a folder (dry run) or pushed to Fabric via REST API.

## Core Value

Given a Fabric warehouse and a key prefix, automatically produce a correct, deployable TMDL semantic model with proper dimension/fact classification and star-schema relationships.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Connect to Fabric warehouse via mssql-python with token auth
- [ ] Read INFORMATION_SCHEMA.COLUMNS for user-specified schemas (no defaults)
- [ ] Filter tables by include list and/or exclude list
- [ ] Classify tables by key column count: 1 key = dimension, 2+ keys = fact
- [ ] Key prefixes are user-supplied, no defaults
- [ ] Infer star-schema relationships (fact *:1 dimension) via matching key columns
- [ ] Support role-playing dimensions (same dim referenced multiple times with different roles)
- [ ] First role-playing relationship active, subsequent ones inactive
- [ ] Support exact-match prefixes that bypass role-playing pattern
- [ ] Generate complete TMDL folder structure (database, model, expressions, relationships, per-table files)
- [ ] Generate DirectLake partition definitions
- [ ] Generate deterministic UUIDs for stable IDs across regenerations
- [ ] Preserve manually-maintained tables/relationships (watermark-based detection)
- [ ] Output mode: write TMDL to folder (dry run) at /lakehouse/default/Files/[MODEL_NAME]
- [ ] Output mode: push to Fabric via REST API with LRO polling
- [ ] Discover Direct Lake URL programmatically: user supplies workspace (name or GUID) + warehouse/lakehouse (name or GUID), library resolves full GUID-based URL
- [ ] Generate diagram layout JSON
- [ ] Generate .platform and definition.pbism metadata files
- [ ] Distributed as PyPI package
- [ ] Dynamic versioning based on git tags
- [ ] Functional programming style throughout
- [ ] TDD — tests written before implementation
- [ ] Linting via make lint
- [ ] Type checking via make typecheck
- [ ] Testing via make test
- [ ] make check runs lint + typecheck + test
- [ ] Pre-commit hook runs make check and validates commit message format

### Out of Scope

- Auto-generated DAX measures from column prefixes (measure__ convention dropped)
- CLI interface — this is a library used in Fabric notebooks, not a command-line tool
- GUI or web interface
- Support for non-Fabric data sources
- Import mode (only DirectLake)

## Context

- Reference notebook: `.references/Semantic Model Generator.ipynb` — working prototype with all core logic
- Target environment: Microsoft Fabric notebooks (PySpark runtime with notebookutils available)
- Auth: Token-based via `notebookutils.credentials.getToken` (Fabric-specific)
- Connection: `mssql-python` library for warehouse connectivity
- The notebook uses Swedish locale in expressions (`Källa`, `sv-SE`) — this should be configurable or use English defaults
- Current Direct Lake URL requires hardcoded workspace/lakehouse GUIDs — library should accept name or GUID for workspace and warehouse/lakehouse, then resolve to full GUID-based Direct Lake URL via Fabric REST API
- The existing notebook works against a production warehouse (WH_Gold) with 45 tables and 72 relationships
- Role-playing dimension support is a key differentiator (e.g., bill-to vs sell-to customer)

## Constraints

- **Runtime**: Python 3.11+ (Fabric notebook environment)
- **Distribution**: PyPI package via `uv` tooling
- **Dependencies**: Must work in Fabric notebook environment (mssql-python, requests, pandas available)
- **Auth**: Must use Fabric token auth (notebookutils) — no stored credentials
- **Style**: Functional programming, no classes unless strictly necessary
- **Quality**: TDD mandatory, linting + type checking enforced via pre-commit
- **Versioning**: Dynamic from git tags (e.g., setuptools-scm or similar)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Library, not CLI | Used inside Fabric notebooks via import | — Pending |
| Functional programming | User mandate — pure functions, no classes unless necessary | — Pending |
| TDD | User mandate — tests first, implementation second | — Pending |
| Dynamic versioning from git tags | Standard PyPI practice, user mandate | — Pending |
| Drop measure__ convention | User decision — no auto-generated DAX measures | — Pending |
| Schemas user-supplied, no defaults | Different warehouses use different schema naming | — Pending |
| Key prefixes user-supplied, no defaults | Different warehouses use different key conventions | — Pending |
| Include/exclude table filtering | Both whitelist and blacklist supported | — Pending |

---
*Last updated: 2026-02-09 after research phase*
