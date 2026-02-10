# Requirements: Semantic Model Generator

**Defined:** 2026-02-10
**Core Value:** Given a Fabric warehouse and a key prefix, automatically produce a correct, deployable TMDL semantic model with proper dimension/fact classification and star-schema relationships.

## v0.2.0 Requirements

Requirements for automated CD pipeline to PyPI. Each maps to roadmap phases.

### CI/CD Infrastructure

- [ ] **CICD-01**: Workflow triggers on git tag push matching pattern v*
- [ ] **CICD-02**: Workflow runs on tag push to main branch only

### Quality & Build

- [ ] **BUILD-01**: Full quality gates run via `make check` before any publishing
- [ ] **BUILD-02**: Tests execute on Python 3.11
- [ ] **BUILD-03**: Tests execute on Python 3.12
- [ ] **BUILD-04**: Build generates wheel distribution (.whl)
- [ ] **BUILD-05**: Build generates source distribution (.tar.gz)
- [ ] **BUILD-06**: Built package installs successfully before publishing

### Publishing

- [ ] **PUB-01**: PyPI Trusted Publishing configured for repository
- [ ] **PUB-02**: Workflow authenticates to PyPI via OIDC (no API tokens)
- [ ] **PUB-03**: Package publishes to pypi.org after quality gates pass

### Release Automation

- [ ] **REL-01**: GitHub release created automatically on tag push
- [ ] **REL-02**: Release notes extracted from .planning/MILESTONES.md matching tag version
- [ ] **REL-03**: Release notes include direct link to PyPI package page
- [ ] **REL-04**: Release notes include link to .planning/MILESTONES.md

## v0.2.x Requirements

Deferred to future releases. Tracked but not in current roadmap.

### CI/CD Infrastructure

- **CICD-03**: GitHub environment with manual approval gate before PyPI publish
- **CICD-04**: TestPyPI preview publishes on main branch merges

### Quality & Build

- **BUILD-07**: Version consistency check validates tag matches hatch-vcs version

### Publishing

- **PUB-04**: Package attestations included for supply chain provenance

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Automatic version bumping | Git tag is source of truth for versioning via hatch-vcs |
| Publishing on every commit | Pollutes PyPI namespace, tags control releases |
| Bypassing quality gates for hotfixes | All releases must pass full test suite |
| Multi-OS builds | Pure Python package doesn't require OS-specific builds |
| Automatic publish retries on failure | Failures need investigation, not automatic retry |
| Slack/Discord release notifications | Can add later if team needs it |
| Rollback automation | PyPI yanking is manual and rare, document process instead |
| Changelog improvements | Basic generation sufficient for v0.2.0, can enhance later |
| Performance benchmarking in CD | Not needed for library package |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CICD-01 | Phase 9 | Pending |
| CICD-02 | Phase 9 | Pending |
| BUILD-01 | Phase 9 | Pending |
| BUILD-02 | Phase 9 | Pending |
| BUILD-03 | Phase 9 | Pending |
| BUILD-04 | Phase 9 | Pending |
| BUILD-05 | Phase 9 | Pending |
| BUILD-06 | Phase 9 | Pending |
| PUB-01 | Phase 9 | Pending |
| PUB-02 | Phase 9 | Pending |
| PUB-03 | Phase 9 | Pending |
| REL-01 | Phase 9 | Pending |
| REL-02 | Phase 9 | Pending |
| REL-03 | Phase 9 | Pending |
| REL-04 | Phase 9 | Pending |

**Coverage:**
- v0.2.0 requirements: 14 total
- Mapped to phases: 14 (100% coverage)
- Unmapped: 0

---
*Requirements defined: 2026-02-10*
*Last updated: 2026-02-10 after roadmap creation*
