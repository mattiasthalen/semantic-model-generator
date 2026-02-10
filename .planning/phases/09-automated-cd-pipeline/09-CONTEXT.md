# Phase 9: Automated CD Pipeline - Context

**Gathered:** 2026-02-10
**Status:** Ready for planning

<domain>
## Phase Boundary

GitHub Actions workflow for automated PyPI publishing triggered by git tags. This phase delivers CI/CD automation that turns a version tag into a published PyPI package and GitHub release. Not adding package features — automating the release process.

</domain>

<decisions>
## Implementation Decisions

### Trigger conditions
- Accept `v*` pattern including pre-releases (v0.2.0, v0.2.0-rc1, v0.2.0-beta1)
- Trigger only from main branch (no feature branch publishes)
- Include manual `workflow_dispatch` option for testing/republishing
- Extract changelog from MILESTONES.md (not auto-generated from commits)
- On any failure: just fail the workflow (no notifications, no draft releases)

### Quality gate execution
- No dependency caching (always fresh install, more reliable)
- Run Python 3.11 and 3.12 checks in parallel (faster)
- Let all jobs finish even if one fails (better debugging information)

### Build verification
- Test wheel only (not sdist) for installation verification
- Run installation test on Linux only (assumes cross-platform compatibility)

### Release artifacts
- Release title: Just the tag (e.g., "v0.2.0")
- Attach both wheel and sdist files to GitHub release
- Release notes structure: Changelog section followed by links section (PyPI, MILESTONES.md)
- Mark pre-release tags (rc, beta, alpha) as pre-releases in GitHub UI

### Claude's Discretion
- Extra validation beyond make check (e.g., version number validation)
- Verification method details (import vs smoke test)
- Package inspection approach (whether to list contents before upload)

</decisions>

<specifics>
## Specific Ideas

- Use OIDC Trusted Publishing (no API tokens) — already specified in success criteria
- Full quality gates (make check) on Python 3.11 and 3.12 — already specified
- Build both wheel and sdist — already specified

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-automated-cd-pipeline*
*Context gathered: 2026-02-10*
