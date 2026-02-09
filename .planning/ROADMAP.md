# Roadmap: Semantic Model Generator

## Overview

Build a Python library (PyPI package) that generates TMDL semantic models from Microsoft Fabric warehouse metadata. The journey starts with build tooling and domain primitives, progresses through schema discovery, relationship inference, and TMDL generation, then adds output modes (folder and REST API), and culminates in a unified pipeline with a single public entry point. Every phase delivers testable, working code following TDD and functional programming conventions.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Project Foundation & Build System** - Toolchain, package structure, quality gates
- [ ] **Phase 2: Domain Types & Core Utilities** - Immutable data types, deterministic UUIDs, type mapping, validation helpers
- [ ] **Phase 3: Schema Discovery & Classification** - Warehouse connectivity, INFORMATION_SCHEMA reading, table filtering, fact/dimension classification
- [ ] **Phase 4: Relationship Inference** - Key matching, role-playing dimensions, active/inactive marking
- [ ] **Phase 5: TMDL Generation** - Template functions for all TMDL file types, deterministic sorted output
- [ ] **Phase 6: Output Layer** - Filesystem writer, watermark-based preservation of manual edits
- [ ] **Phase 7: Fabric REST API Integration** - Workspace/lakehouse GUID resolution, semantic model deployment, LRO polling
- [ ] **Phase 8: Pipeline Orchestration & Public API** - Main entry point, end-to-end pipeline, integration tests

## Phase Details

### Phase 1: Project Foundation & Build System
**Goal**: Developer can clone the repo, run `make check`, and get a passing lint + typecheck + test pipeline with pre-commit hooks enforcing quality on every commit
**Depends on**: Nothing (first phase)
**Requirements**: REQ-20, REQ-21, REQ-22, REQ-23, REQ-24, REQ-25, REQ-26, REQ-27, REQ-28
**Success Criteria** (what must be TRUE):
  1. `pip install -e .` succeeds and the package is importable as `semantic_model_generator`
  2. `make lint` runs ruff and reports clean on the initial codebase
  3. `make typecheck` runs mypy in strict mode and passes
  4. `make test` runs pytest and executes at least one passing test
  5. `make check` runs lint + typecheck + test in sequence, all green
  6. Pre-commit hook blocks commits that fail `make check` or have malformed commit messages
  7. Package version is dynamically derived from git tags (no hardcoded version string)
**Plans**: TBD

Plans:
- [ ] 01-01: pyproject.toml, src layout, hatchling + setuptools-scm, Makefile, ruff, mypy, pytest, pre-commit

### Phase 2: Domain Types & Core Utilities
**Goal**: Pure utility functions and immutable data types exist for deterministic UUID generation, SQL-to-TMDL type mapping, identifier quoting, and TMDL whitespace validation -- the building blocks every downstream phase depends on
**Depends on**: Phase 1
**Requirements**: REQ-12, REQ-30, REQ-31
**Success Criteria** (what must be TRUE):
  1. Calling the UUID generator twice with the same inputs produces identical UUIDs (deterministic via uuid5)
  2. Every SQL Server data type used in Fabric warehouses maps to a valid TMDL data type
  3. Identifiers containing special characters (spaces, dots, quotes) are correctly single-quoted with escaped internal quotes
  4. TMDL output uses tabs for indentation (not spaces) and passes whitespace validation
**Plans**: TBD

Plans:
- [ ] 02-01: Domain types (frozen dataclasses), UUID generation, type mapping, identifier quoting, whitespace validation

### Phase 3: Schema Discovery & Classification
**Goal**: Library can connect to a Fabric warehouse, read its schema metadata, filter to the requested tables, and classify each as dimension or fact based on key column count
**Depends on**: Phase 2
**Requirements**: REQ-01, REQ-02, REQ-03, REQ-04, REQ-05, REQ-29
**Success Criteria** (what must be TRUE):
  1. Library connects to a Fabric warehouse using mssql-python with token authentication
  2. Schema reader retrieves columns from INFORMATION_SCHEMA.COLUMNS for user-specified schemas only
  3. Views are excluded from discovery (only BASE TABLE rows from INFORMATION_SCHEMA.TABLES)
  4. Tables can be filtered by include list, exclude list, or both
  5. Tables with exactly 1 key column (matching user-supplied prefixes) are classified as dimensions; tables with 2+ key columns are classified as facts
**Plans**: TBD

Plans:
- [ ] 03-01: Warehouse connection, INFORMATION_SCHEMA reader, view filtering, table filtering, fact/dimension classifier

### Phase 4: Relationship Inference
**Goal**: Given classified schema metadata and key prefixes, the library infers star-schema relationships between facts and dimensions, correctly handling role-playing dimensions and exact-match bypass
**Depends on**: Phase 3
**Requirements**: REQ-06, REQ-07, REQ-08, REQ-09
**Success Criteria** (what must be TRUE):
  1. Fact-to-dimension relationships are inferred by matching key columns across tables (fact many-to-one dimension)
  2. Role-playing dimensions are detected when the same dimension is referenced multiple times from a single fact with different key column prefixes
  3. The first role-playing relationship is marked active; subsequent relationships to the same dimension are marked inactive
  4. Exact-match prefixes bypass role-playing detection (the key column name matches a prefix exactly, no suffix stripping)
**Plans**: TBD

Plans:
- [ ] 04-01: Key matching, relationship inference, role-playing dimension detection, active/inactive marking, exact-match bypass

### Phase 5: TMDL Generation
**Goal**: Library generates a complete, syntactically correct TMDL folder structure from schema metadata and inferred relationships, with deterministic output suitable for Git version control
**Depends on**: Phase 2, Phase 4
**Requirements**: REQ-10, REQ-11, REQ-17, REQ-18, REQ-32, REQ-33
**Success Criteria** (what must be TRUE):
  1. All required TMDL files are generated: database.tmdl, model.tmdl, expressions.tmdl, relationships.tmdl, and one .tmdl file per table
  2. Each table file includes a DirectLake partition definition referencing the source warehouse table
  3. The .platform file and definition.pbism metadata file are generated with correct structure
  4. Diagram layout JSON is generated positioning tables visually
  5. Regenerating from the same input produces byte-identical output (deterministic sorting of all collections)
  6. Expression locale is configurable (defaults to English, not hardcoded Swedish)
**Plans**: TBD

Plans:
- [ ] 05-01: Template functions for database.tmdl, model.tmdl, expressions.tmdl
- [ ] 05-02: Table TMDL generation with DirectLake partitions, relationships.tmdl, metadata files, diagram layout

### Phase 6: Output Layer
**Goal**: Generated TMDL can be written to a folder on disk, with watermark-based detection that preserves manually-maintained files from being overwritten
**Depends on**: Phase 5
**Requirements**: REQ-13, REQ-14
**Success Criteria** (what must be TRUE):
  1. TMDL folder structure is written to /lakehouse/default/Files/[MODEL_NAME] (or user-specified path)
  2. Files containing the generator watermark are overwritten on regeneration; files without the watermark are preserved untouched
  3. Dry-run mode writes to folder without any API calls (pure filesystem output)
**Plans**: TBD

Plans:
- [ ] 06-01: Filesystem writer, watermark generation, watermark detection, preservation logic

### Phase 7: Fabric REST API Integration
**Goal**: Library can resolve workspace and lakehouse identifiers, package TMDL output, and deploy a semantic model to Fabric via REST API with long-running operation polling
**Depends on**: Phase 5
**Requirements**: REQ-15, REQ-16
**Success Criteria** (what must be TRUE):
  1. User can supply workspace and warehouse/lakehouse as either name or GUID; the library resolves to full GUID-based Direct Lake URL via Fabric REST API
  2. TMDL parts are base64-encoded and assembled into the Fabric semantic model definition payload
  3. Semantic model is created or updated via Fabric REST API POST
  4. Long-running operations are polled until completion with appropriate status reporting
**Plans**: TBD

Plans:
- [ ] 07-01: Workspace/lakehouse GUID resolution, definition payload assembly, REST API create/update, LRO polling

### Phase 8: Pipeline Orchestration & Public API
**Goal**: A single `generate_semantic_model()` function orchestrates the full pipeline from connection through output, with comprehensive error handling and integration tests proving end-to-end correctness
**Depends on**: Phase 6, Phase 7
**Requirements**: (Integrates all prior requirements into cohesive pipeline)
**Success Criteria** (what must be TRUE):
  1. Calling `generate_semantic_model()` with valid configuration executes the full pipeline: connect, read schema, classify, infer relationships, generate TMDL, write output
  2. The function supports both output modes (folder and REST API) via configuration
  3. Errors at any pipeline stage produce clear, actionable error messages identifying the failing stage and cause
  4. End-to-end integration tests pass covering the folder output path with representative warehouse schemas
**Plans**: TBD

Plans:
- [ ] 08-01: Pipeline orchestrator, public API function, error handling, integration tests

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8

| Phase | Plans Complete | Status | Completed |
|-------|---------------|--------|-----------|
| 1. Project Foundation & Build System | 0/1 | Not started | - |
| 2. Domain Types & Core Utilities | 0/1 | Not started | - |
| 3. Schema Discovery & Classification | 0/1 | Not started | - |
| 4. Relationship Inference | 0/1 | Not started | - |
| 5. TMDL Generation | 0/2 | Not started | - |
| 6. Output Layer | 0/1 | Not started | - |
| 7. Fabric REST API Integration | 0/1 | Not started | - |
| 8. Pipeline Orchestration & Public API | 0/1 | Not started | - |
