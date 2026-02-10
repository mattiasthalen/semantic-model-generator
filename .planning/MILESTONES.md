# Milestones

## v0.2.0 CD to PyPI (Shipped: 2026-02-10)

**Phases completed:** Phase 9 (Automated CD Pipeline) — 1 plan, 2 tasks

**Key accomplishments:**
- Complete GitHub Actions CD workflow with 5-job pipeline (validate → build → verify → publish → release)
- OIDC Trusted Publishing to PyPI configured (no API tokens required)
- Automated GitHub release creation with changelog extraction from MILESTONES.md
- Quality gates run on Python 3.11 and 3.12 with fail-fast: false for debugging
- Pre-release detection for alpha/beta/rc versions with automatic pre-release marking
- Tag-based versioning workflow with manual workflow_dispatch fallback

**Delivered:**
Tag-based CD pipeline that validates via make check, builds wheel and sdist distributions, verifies installation, publishes to pypi.org via OIDC, and creates GitHub releases with curated changelogs.

---

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

