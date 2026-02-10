# Semantic Model Generator

## What This Is

A Python package (distributed via PyPI) that generates TMDL semantic models for Microsoft Fabric. Users import it in Fabric notebooks, point it at a warehouse's INFORMATION_SCHEMA, and it automatically classifies tables as dimensions or facts based on key column prefixes, infers star-schema relationships, and outputs a complete TMDL semantic model — either written to a folder (dry run) or pushed to Fabric via REST API.

## Core Value

Given a Fabric warehouse and a key prefix, automatically produce a correct, deployable TMDL semantic model with proper dimension/fact classification and star-schema relationships.

## Requirements

### Validated

- ✓ Connect to Fabric warehouse via mssql-python with token auth — v0.1.0
- ✓ Read INFORMATION_SCHEMA.COLUMNS for user-specified schemas (no defaults) — v0.1.0
- ✓ Filter tables by include list and/or exclude list — v0.1.0
- ✓ Classify tables by key column count: 1 key = dimension, 2+ keys = fact — v0.1.0
- ✓ Key prefixes are user-supplied, no defaults — v0.1.0
- ✓ Infer star-schema relationships (fact *:1 dimension) via matching key columns — v0.1.0
- ✓ Support role-playing dimensions (same dim referenced multiple times with different roles) — v0.1.0
- ✓ First role-playing relationship active, subsequent ones inactive — v0.1.0
- ✓ Support exact-match prefixes that bypass role-playing pattern — v0.1.0
- ✓ Generate complete TMDL folder structure (database, model, expressions, relationships, per-table files) — v0.1.0
- ✓ Generate DirectLake partition definitions — v0.1.0
- ✓ Generate deterministic UUIDs for stable IDs across regenerations — v0.1.0
- ✓ Preserve manually-maintained tables/relationships (watermark-based detection) — v0.1.0
- ✓ Output mode: write TMDL to folder (dry run) at /lakehouse/default/Files/[MODEL_NAME] — v0.1.0
- ✓ Output mode: push to Fabric via REST API with LRO polling — v0.1.0
- ✓ Discover Direct Lake URL programmatically: user supplies workspace (name or GUID) + warehouse/lakehouse (name or GUID), library resolves full GUID-based URL — v0.1.0
- ✓ Generate diagram layout JSON — v0.1.0
- ✓ Generate .platform and definition.pbism metadata files — v0.1.0
- ✓ Distributed as PyPI package — v0.1.0
- ✓ Dynamic versioning based on git tags — v0.1.0
- ✓ Functional programming style throughout — v0.1.0
- ✓ TDD — tests written before implementation — v0.1.0
- ✓ Linting via make lint — v0.1.0
- ✓ Type checking via make typecheck — v0.1.0
- ✓ Testing via make test — v0.1.0
- ✓ make check runs lint + typecheck + test — v0.1.0
- ✓ Pre-commit hook runs make check and validates commit message format — v0.1.0
- ✓ Dev deployment mode: always creates a new semantic model, suffixed with current UTC timestamp — v0.1.0
- ✓ Prod deployment mode: overwrites existing model, requires explicit confirmation parameter (notebook-friendly, no interactive prompts) — v0.1.0

### Active

(None — ready for v0.2.0 planning)

### Out of Scope

- Auto-generated DAX measures from column prefixes (measure__ convention dropped)
- CLI interface — this is a library used in Fabric notebooks, not a command-line tool
- GUI or web interface
- Support for non-Fabric data sources
- Import mode (only DirectLake)

## Context

**Shipped v0.1.0 MVP (2026-02-10):**
- 8 phases complete (15 plans executed)
- 2,528 lines of Python code
- 398 tests passing (100% quality gates)
- Tech stack: hatchling, mssql-python, tenacity, ruff, mypy strict, pytest
- Reference notebook converted to production library

**Current capabilities:**
- Warehouse schema discovery with token auth (mssql-python)
- Fact/dimension classification by key column count
- Star-schema relationship inference with role-playing dimension support
- Complete TMDL generation (8 file types + metadata)
- Dual output: folder writer (dev/prod modes) + Fabric REST API deployment
- Watermark-based preservation of manual edits
- End-to-end pipeline with single entry point

**Known limitations addressed:**
- ✓ Swedish locale hardcoding — now uses en-US in expressions.tmdl
- ✓ Hardcoded workspace/lakehouse GUIDs — now resolves names via Fabric API
- ✓ No view filtering — views excluded from discovery
- ✓ Manual relationship creation — fully automated with role-playing detection

## Constraints

- **Runtime**: Python 3.11+ (Fabric notebook environment)
- **Distribution**: PyPI package via `uv` tooling
- **Dependencies**: Must work in Fabric notebook environment (mssql-python, requests, pandas available)
- **Auth**: Must use Fabric token auth (notebookutils) — no stored credentials
- **Style**: Functional programming, no classes unless strictly necessary
- **Quality**: TDD mandatory, linting + type checking enforced via pre-commit
- **Versioning**: Dynamic from git tags (e.g., setuptools-scm or similar)
- **Branching**: Per-phase branches (`gsd/phase-{N}-{slug}`). ALL phase work — including research, plans, and code — must be committed on the phase branch, never on main. The phase branch is created from main before any phase work begins and merged back upon phase completion.
- **Tagging**: Version tags (e.g., `v0.1.0`) are created only upon milestone completion, not on individual phase merges. The initial `v0.0.1` tag exists solely for hatchling VCS version derivation.

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
| Dev/prod deployment modes | Dev = new model + UTC suffix (safe iteration), Prod = overwrite with explicit confirm (no interactive prompts in notebooks) | — Pending |
| Per-phase branching | All phase work (research, plans, code) on `gsd/phase-{N}-{slug}`, merged to main on completion | Enforced |
| Tags on milestone completion only | Version tags created at milestone completion, not per-phase; v0.0.1 exists for hatchling VCS bootstrap only | Enforced |

---
*Last updated: 2026-02-10 after v0.1.0 milestone completion*
