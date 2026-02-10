# Roadmap: Semantic Model Generator

## Milestones

- ✅ **v0.1.0 MVP** - Phases 1-8 (shipped 2026-02-10)
- 🚧 **v0.2.0 CD to PyPI** - Phase 9 (in progress)

## Phases

<details>
<summary>✅ v0.1.0 MVP (Phases 1-8) - SHIPPED 2026-02-10</summary>

- [x] Phase 1: Project Foundation & Build System (1/1 plans) - completed 2026-02-09
- [x] Phase 2: Domain Types & Core Utilities (2/2 plans) - completed 2026-02-09
- [x] Phase 3: Schema Discovery & Classification (3/3 plans) - completed 2026-02-09
- [x] Phase 4: Relationship Inference (1/1 plan) - completed 2026-02-09
- [x] Phase 5: TMDL Generation (2/2 plans) - completed 2026-02-10
- [x] Phase 6: Output Layer (2/2 plans) - completed 2026-02-10
- [x] Phase 7: Fabric REST API Integration (2/2 plans) - completed 2026-02-10
- [x] Phase 8: Pipeline Orchestration & Public API (2/2 plans) - completed 2026-02-10

**Delivered:**
- Complete build system with quality gates
- Star-schema relationship inference with role-playing dimensions
- Full TMDL generation (8 file types + metadata)
- Dual output modes (folder + REST API)
- End-to-end pipeline with 398 passing tests

See: `.planning/milestones/v0.1.0-ROADMAP.md` for full phase details

</details>

### 🚧 v0.2.0 CD to PyPI (In Progress)

**Milestone Goal:** Automate PyPI publishing with tag-based GitHub Actions CD pipeline.

#### Phase 9: Automated CD Pipeline
**Goal**: Tag-based GitHub Actions workflow that validates, builds, publishes to PyPI, and creates releases
**Depends on**: Nothing (extends existing infrastructure)
**Requirements**: CICD-01, CICD-02, BUILD-01, BUILD-02, BUILD-03, BUILD-04, BUILD-05, BUILD-06, PUB-01, PUB-02, PUB-03, REL-01, REL-02, REL-03, REL-04
**Success Criteria** (what must be TRUE):
  1. Developer pushes git tag matching v* pattern and workflow triggers automatically
  2. Full quality gates (make check) run on Python 3.11 and 3.12 before any publish step
  3. Workflow builds both wheel (.whl) and source distribution (.tar.gz) and verifies installation
  4. Package publishes to pypi.org via OIDC Trusted Publishing without API tokens
  5. GitHub release appears automatically with changelog, PyPI link, and MILESTONES.md link
**Plans**: 1 plan

Plans:
- [x] 09-01-PLAN.md — Create publish.yml CD workflow + configure PyPI Trusted Publishing

## Progress

**Execution Order:**
Phases execute in numeric order.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Project Foundation & Build System | v0.1.0 | 1/1 | Complete | 2026-02-09 |
| 2. Domain Types & Core Utilities | v0.1.0 | 2/2 | Complete | 2026-02-09 |
| 3. Schema Discovery & Classification | v0.1.0 | 3/3 | Complete | 2026-02-09 |
| 4. Relationship Inference | v0.1.0 | 1/1 | Complete | 2026-02-09 |
| 5. TMDL Generation | v0.1.0 | 2/2 | Complete | 2026-02-10 |
| 6. Output Layer | v0.1.0 | 2/2 | Complete | 2026-02-10 |
| 7. Fabric REST API Integration | v0.1.0 | 2/2 | Complete | 2026-02-10 |
| 8. Pipeline Orchestration & Public API | v0.1.0 | 2/2 | Complete | 2026-02-10 |
| 9. Automated CD Pipeline | v0.2.0 | 1/1 | Complete | 2026-02-10 |
