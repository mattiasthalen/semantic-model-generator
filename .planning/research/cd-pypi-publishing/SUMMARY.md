# Project Research Summary: CD Pipeline to PyPI

**Project:** Automated CD Pipeline for PyPI Publishing
**Domain:** Continuous Deployment / Python Package Distribution
**Researched:** 2026-02-10
**Confidence:** HIGH

## Executive Summary

Building a CD pipeline for Python package publishing is a well-established pattern with minimal complexity. The key finding: **this project already has all the necessary infrastructure** — hatchling for builds, hatch-vcs for git tag-based versioning, and `make check` for quality gates. The CD pipeline simply orchestrates these existing tools through GitHub Actions, adding only PyPI Trusted Publishing (OIDC authentication without stored secrets) and automated release creation with changelog generation.

The recommended approach uses a tag-triggered workflow that runs on semver tags (v*): execute quality gates → build wheel and sdist → verify package installation → publish to PyPI via Trusted Publishing → create GitHub release with auto-generated changelog linking to PyPI and MILESTONES.md. This is the industry standard pattern, officially documented by the Python Packaging Authority (PyPA), and requires zero new Python dependencies. The workflow uses a 3-job structure separating build (no publish permissions) from publish (scoped permissions) for security.

Critical success factors: (1) configure PyPI Trusted Publishing before first automated release, (2) use GitHub environment protection for manual approval gates, (3) preserve full git history during checkout (`fetch-depth: 0`) so hatch-vcs can determine version from tags, and (4) generate release notes automatically from conventional commits to ensure every release is documented. The main risk is attempting first publish without Trusted Publishing configured on PyPI, which will fail with authentication errors. Mitigation is straightforward documentation of the one-time PyPI configuration steps.

## Key Findings

### Recommended Stack

Stack research reveals the CD pipeline needs **zero new Python packages**. The existing build system handles everything; the pipeline adds only GitHub Actions orchestration.

**Core technologies:**
- **GitHub Actions** (platform): Native integration, free for public repos, built-in secrets management via OIDC
- **PyPI Trusted Publishing** (OIDC): Eliminates API tokens entirely, automatic credential rotation, modern security standard required by PyPI
- **pypa/gh-action-pypi-publish v1.13.0**: Official PyPA action supporting trusted publishing + PEP 740 attestations (supply chain provenance)
- **actions/checkout v6**, **actions/setup-python v6**, **actions/upload-artifact v4**: Latest GitHub Actions with node24 runtime, 90% faster artifact uploads
- **mikepenz/release-changelog-builder-action v6**: Generates changelogs from conventional commits without additional dependencies
- **TestPyPI** (service): Separate PyPI instance for pre-production validation

**Existing tools (keep unchanged):**
- **hatchling** (build backend): Already configured, PEP 517 compliant, 7.5x faster than setuptools
- **hatch-vcs** (versioning): Reads git tags to set package version dynamically
- **make check** (quality gates): Orchestrates lint + typecheck + test in single command

**What NOT to add:**
- setuptools_scm (conflicts with hatch-vcs)
- pypa/build package (hatchling is already PEP 517 backend)
- API tokens in GitHub secrets (Trusted Publishing eliminates need)
- Hatch CLI tool (python -m build works without it)
- tox (existing make check + matrix strategy sufficient)

**Version requirements:**
- Python 3.11+ (already project requirement)
- GitHub Actions runner ubuntu-latest (for node24 support)
- Git 2.0+ with full history (`fetch-depth: 0`)

### Expected Features

Features research identifies clear tiers with all P1 features achievable in initial implementation.

**Must have (table stakes):**
- Tag-triggered workflow on v* pattern — industry standard
- Full test suite via `make check` — prevents broken releases
- Build wheel + sdist — PyPI best practice
- Multi-version testing (Python 3.11, 3.12) — reuse existing CI matrix
- Trusted Publisher authentication — no API tokens, OIDC only
- Package installation verification — test pip install from built wheel
- Publish to PyPI — core purpose
- GitHub release creation — users expect release notes
- Auto-generated changelog — user requirement from git history
- PyPI link in release notes — direct navigation
- MILESTONES.md link — user-specific requirement
- Workflow failure notifications — GitHub Actions default behavior

**Should have (differentiators):**
- Package attestations — enabled by default with trusted publishing
- Manual approval gate — GitHub environment protection
- TestPyPI preview — validate before production
- Version consistency checks — verify tag matches hatch-vcs version

**Defer (v0.2.x or later):**
- Release announcement automation (Slack/Discord)
- Changelog improvements (better categorization)
- Rollback documentation (PyPI yanking process)
- Performance benchmarking in CD

**Anti-features (explicitly avoid):**
- Automatic version bumping — tag is source of truth
- Publishing on every commit — pollutes PyPI
- Bypassing quality gates for hotfixes — always run full tests
- Building on multiple OS — pure Python doesn't need it
- Automatic retries on failure — masks issues needing investigation
- Embedding secrets in workflow — Trusted Publishing eliminates need

### Architecture Approach

The CD workflow architecture uses a 3-job pattern with clear separation of concerns and scoped permissions.

**Job 1: Build & Validate (runs on all pushes)**
- Checkout with full history (`fetch-depth: 0` for hatch-vcs)
- Matrix testing across Python 3.11, 3.12
- Install package and run `make check`
- Build artifacts with `python -m build`
- Upload artifacts for downstream jobs
- **Permissions:** read-only, no publish capability

**Job 2: TestPyPI (runs on main branch, optional)**
- Download build artifacts
- Publish to test.pypi.org via Trusted Publishing
- No environment protection (automatic)
- **Purpose:** Early detection of publishing issues

**Job 3: PyPI + Release (runs on tag pushes only)**
- Download build artifacts
- Generate changelog from conventional commits
- Publish to PyPI via Trusted Publishing
- Create GitHub release with changelog, PyPI link, MILESTONES.md link
- **Permissions:** `id-token: write` (for Trusted Publishing), `contents: write` (for release creation)
- **Protection:** Requires manual approval via GitHub environment `pypi`

**Separation rationale:**
- Build job cannot accidentally publish (no permissions)
- Publish permissions scoped to specific job only
- Environment protection adds manual gate
- TestPyPI on main merges catches auth issues early
- Artifacts built once, reused across jobs (consistency)

**Workflow trigger strategy:**
```yaml
on:
  push:
    branches: [main]    # Build + TestPyPI
    tags: ['v*']        # Build + PyPI + Release
  pull_request:         # Build only
```

### Critical Pitfalls

CD pipeline has fewer pitfalls than typical projects due to mature tooling and well-documented patterns. Main risks are configuration and workflow design mistakes.

**Critical pitfalls:**

1. **Publishing before tests complete** — Workflow publishes even if tests fail. **Prevention:** Use job dependencies `needs: [build, verify]` so publish only runs after success. **Phase:** Initial workflow design.

2. **Trusted Publisher not configured on PyPI** — First publish attempt fails with auth error because PyPI doesn't trust the GitHub repo. **Prevention:** Document one-time PyPI configuration with screenshots, test on TestPyPI first. **Phase:** Documentation and setup.

3. **Version mismatch between tag and package** — Git tag is v1.2.3 but hatch-vcs generates 1.2.4 due to incomplete history. **Prevention:** Always use `fetch-depth: 0` in checkout action so hatch-vcs sees full history. **Phase:** Initial workflow design.

4. **Forgotten release notes** — GitHub release created with empty body. **Prevention:** Auto-generate changelog from git history using conventional commits, always have content. **Phase:** Release automation.

5. **No quality gate bypass mechanism** — Critical fix needed but tests failing for unrelated reason. **Prevention:** Don't create bypass. Document manual publish process if truly needed. **Phase:** Documentation.

**Moderate pitfalls:**

- **Secrets in environment variables** — Developer adds PyPI token "just in case." **Prevention:** Document that Trusted Publishing requires NO secrets, avoid token configuration entirely.
- **Failed publish with no rollback** — Publish fails mid-operation, unclear how to recover. **Prevention:** Document that PyPI allows re-publishing if publish failed (not if it succeeded), releases can be manually created.
- **Single token acquisition** — Token acquired once, expires during long build. **Note:** Not applicable to this project (builds complete in <5 minutes), but document token expiration if builds become complex.

**Pitfall-to-phase mapping:**
- Pitfalls 1-4: Address in initial workflow implementation
- Pitfall 5: Address in documentation
- Moderate pitfalls: Address in setup documentation

## Implications for Roadmap

The CD pipeline is **atomic and should be implemented as a single deliverable**. The components are tightly coupled — tag trigger, quality gates, build, publish, and release creation form an indivisible workflow. Partial implementation creates non-functional states that can't be validated.

### Single Phase Implementation (1-2 days)

**Rationale:** CD pipeline components must work together as a unit. Cannot test publishing without build, cannot create release without publish success, cannot validate workflow without end-to-end execution. Breaking into phases creates incomplete states with no validation path.

**Deliverables:**

1. **PyPI Configuration (manual, one-time)**
   - Configure Trusted Publishing on test.pypi.org
   - Configure Trusted Publishing on pypi.org
   - Create GitHub environment `pypi` with required reviewers

2. **GitHub Actions Workflow (`.github/workflows/cd.yml`)**
   - Job 1: Build with matrix testing, artifact upload
   - Job 2: TestPyPI publish (conditional on main branch)
   - Job 3: PyPI publish + release (conditional on tag, requires approval)
   - Job dependencies ensuring correct execution order

3. **Changelog Generation**
   - Configure `mikepenz/release-changelog-builder-action@v6`
   - Parse conventional commits from existing pre-commit setup
   - Categorize by type (feat, fix, docs, etc.)

4. **Release Automation**
   - Generate release notes from changelog
   - Add PyPI link: `https://pypi.org/project/semantic-model-generator/{version}/`
   - Add MILESTONES.md link to project documentation
   - Attach build artifacts (optional)

5. **Documentation**
   - README section on releasing
   - Document tagging convention (vX.Y.Z)
   - Document PyPI Trusted Publishing setup steps
   - Document manual publish procedure for emergencies

**Implementation sequence:**
1. Configure PyPI Trusted Publishing (test + prod)
2. Create GitHub environment with protection
3. Write workflow file with 3-job structure
4. Configure changelog action with categories
5. Test on TestPyPI with test tag
6. Document release process
7. Execute first real release (v0.2.0)

**Addresses all P1 features:**
- Tag-triggered workflow ✓
- Quality gates (make check) ✓
- Multi-version testing ✓
- Build wheel + sdist ✓
- Package verification ✓
- Trusted Publishing ✓
- PyPI publishing ✓
- GitHub release ✓
- Auto changelog ✓
- PyPI link ✓
- MILESTONES.md link ✓

**Avoids all critical pitfalls:**
- Job dependencies prevent premature publish ✓
- Documentation ensures PyPI configured ✓
- fetch-depth: 0 prevents version mismatch ✓
- Changelog automation prevents empty releases ✓
- No bypass mechanism, manual process documented ✓

**Validation:**
- Test workflow on feature branch (build job only)
- Test TestPyPI publish on main branch
- Test production publish on test tag (v0.2.0-rc1)
- Verify release notes format and links
- Test manual approval flow

### Integration with Existing Milestones

The CD pipeline enables the v0.2.0 milestone by automating PyPI publishing. Current state: v0.1.0 complete with manual distribution. CD pipeline bridges to automated distribution.

**Current (v0.1.0):**
- Manual package building
- Manual PyPI upload
- Manual release creation
- Users install from Git or local build

**After CD Pipeline (v0.2.0):**
- Automated package building on tag
- Automated PyPI publishing via Trusted Publishing
- Automated GitHub release with changelog
- Users install via `pip install semantic-model-generator`

**Future milestones benefit:**
- v0.2.x patches: tag → automatic release
- v0.3.0 features: same CD workflow, no changes needed
- Confidence in release process enables faster iteration

### Research Flags

**No additional research needed:** CD pipeline patterns are well-documented and mature.

**Phases with standard patterns:**
- Tag-triggered workflows — GitHub Actions documentation complete
- Trusted Publishing setup — PyPI documentation with examples
- Changelog generation — Conventional commit parsers documented
- Release automation — GitHub CLI and actions well-documented
- Quality gate integration — Existing `make check` already tested

**No complex or niche patterns:** All components use official, supported tools with comprehensive documentation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Official PyPA tools, GitHub Actions platform features, existing build system tested in production |
| Features | HIGH | Industry standard patterns, clear user requirements, anti-features identified from best practices |
| Architecture | HIGH | 3-job pattern documented in Python Packaging Guide, proven at scale across thousands of projects |
| Pitfalls | HIGH | Common mistakes well-documented in PyPA guides and community experience |

**Overall confidence:** HIGH

CD pipeline implementation is low-risk with mature tooling and clear patterns. The existing project infrastructure (hatchling, hatch-vcs, make check, conventional commits) provides complete foundation. GitHub Actions workflows are deterministic and testable. PyPI Trusted Publishing is officially supported and widely adopted. Changelog generation tools are proven. Only unknowns are minor: exact workflow trigger timing, GitHub environment UI changes, or PyPI API edge cases — all low-impact with documented workarounds.

### Gaps to Address

**Configuration validation:**
- **Gap:** First-time Trusted Publishing configuration may have unclear error messages
- **Mitigation:** Test on TestPyPI first, document exact steps with screenshots, verify configuration before first production publish

**Changelog customization:**
- **Gap:** Default changelog categories may not match project commit patterns
- **Mitigation:** Review existing commit history, customize categories in workflow config, test with historical commits

**Manual approval workflow:**
- **Gap:** GitHub environment protection UI may change, reviewers need clear instructions
- **Mitigation:** Document approval process with screenshots, test manual approval flow before production use

**Emergency publish procedure:**
- **Gap:** If automation fails, team needs manual publish instructions
- **Mitigation:** Document manual process using `python -m build` + `twine upload` as fallback, include troubleshooting section

**Version tag format:**
- **Gap:** Team may use inconsistent tag formats (v1.0.0 vs 1.0.0 vs v1.0.0-beta)
- **Mitigation:** Document exact format (v{major}.{minor}.{patch}), use pre-commit hook to validate, provide examples

## Sources

### Primary (HIGH confidence)

**Official Documentation:**
- [Publishing Python packages with GitHub Actions - Python Packaging User Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) — Complete workflow pattern
- [PyPI Trusted Publishers Documentation](https://docs.pypi.org/trusted-publishers/using-a-publisher/) — OIDC setup and configuration
- [pypa/gh-action-pypi-publish](https://github.com/marketplace/actions/pypi-publish) — v1.13.0 features, permissions, attestations
- [GitHub Actions: Managing environments](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment) — Environment protection configuration
- [actions/setup-python Releases](https://github.com/actions/setup-python/releases) — v6 features and compatibility
- [actions/upload-artifact v4](https://github.com/actions/upload-artifact) — Performance improvements and breaking changes

**Build Tools:**
- [build · PyPI](https://pypi.org/project/build/) — Version 1.4.0 usage
- [Hatchling documentation](https://hatch.pypa.io/latest/config/build/) — Build backend configuration

**Changelog Generation:**
- [Release Changelog Builder](https://github.com/marketplace/actions/release-changelog-builder) — v6 configuration options
- [Conventional Commits](https://www.conventionalcommits.org/) — Commit message format specification
- [gh CLI - release create](https://cli.github.com/manual/gh_release_create) — GitHub release creation

### Secondary (MEDIUM confidence)

**Best Practices:**
- [Publishing Python Packages to PyPI: Complete Guide (2026)](https://inventivehq.com/blog/python-pypi-publishing-guide) — Modern patterns and examples
- [How to Automate Releases with GitHub Actions (2026)](https://oneuptime.com/blog/post/2026-01-25-automate-releases-github-actions/view) — Release automation strategies
- [Hatchling Build Backend 2026](https://johal.in/hatchling-build-backend-pep-517-compliant-python-packaging-2026-2/) — Performance benchmarks and comparison

**CI/CD Patterns:**
- [Tag-Based Python CI/CD Pipeline Guide](https://dhruv-ahuja.github.io/posts/tag-based-ci-cd-pipeline/) — Tag trigger patterns
- [Python CI/CD Pipeline Mastery 2025](https://atmosly.com/blog/python-ci-cd-pipeline-mastery-a-complete-guide-for-2025) — Comprehensive pipeline examples
- [Python Packages CI/CD Guide](https://py-pkgs.org/08-ci-cd.html) — Academic perspective on package CI/CD

**Security:**
- [PyPI Attestations Documentation](https://docs.pypi.org/attestations/) — PEP 740 attestation details
- [GitHub Artifact Attestations](https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds) — Supply chain provenance

**Anti-Patterns:**
- [CI/CD Anti-Patterns Book](https://leanpub.com/ci-cd-anti-patterns) — Common mistakes to avoid
- [What's Slowing Down Your Pipeline](https://em360tech.com/tech-articles/cicd-anti-patterns-whats-slowing-down-your-pipeline) — Performance anti-patterns

### Tertiary (LOW confidence, validation recommended)

- Community forum discussions on TestPyPI usage patterns
- Blog posts on changelog generation strategies (not official guidance)
- GitHub issue threads on environment protection edge cases

---
*Research completed: 2026-02-10*
*Ready for implementation: Yes*
*Estimated effort: 1-2 days*
