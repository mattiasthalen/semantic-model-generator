# Milestones

## v0.1.0 MVP (Shipped: 2026-02-10)

**Phases completed:** 8 phases, 15 plans, 6 tasks

**Key accomplishments:**
- Complete build system with hatchling, git-tag versioning, ruff linting, mypy strict type checking, pytest, and pre-commit hooks
- Frozen dataclasses for domain types with SQL-to-TMDL type mapping for all 15 Fabric warehouse data types
- Warehouse schema discovery with mssql-python, token auth, table filtering, and fact/dimension classification
- Star-schema relationship inference with role-playing dimension support and active/inactive marking
- Complete TMDL generation for all 8 file types with deterministic output and metadata files
- Dual output modes: folder writer (dev/prod) with watermark preservation and Fabric REST API deployment with LRO polling
- End-to-end pipeline orchestration with single `generate_semantic_model()` entry point and 398 passing tests

---

