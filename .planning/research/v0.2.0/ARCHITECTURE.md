# Architecture Research: CD Pipeline Integration

**Domain:** GitHub Actions CD for Python package publishing
**Researched:** 2026-02-10
**Confidence:** HIGH

## System Overview

The CD pipeline integrates with existing build tooling through a tag-triggered GitHub Actions workflow that orchestrates quality gates, package building, and multi-destination publishing.

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXISTING COMPONENTS                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   Make   │  │Hatchling │  │hatch-vcs │  │   Git    │        │
│  │ (quality │  │ (build)  │  │(version) │  │  (tags)  │        │
│  │  gates)  │  └──────────┘  └──────────┘  └──────────┘        │
│  └──────────┘                                                    │
├─────────────────────────────────────────────────────────────────┤
│                     NEW COMPONENTS                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │         GitHub Actions Workflow (.github/workflows/)    │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │    │
│  │  │  Build   │  │  Publish │  │ Release  │              │    │
│  │  │   Job    │  │   Job    │  │   Job    │              │    │
│  │  └──────────┘  └──────────┘  └──────────┘              │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                  EXTERNAL SERVICES                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │TestPyPI  │  │   PyPI   │  │  GitHub  │                      │
│  │(staging) │  │(prod)    │  │ Releases │                      │
│  └──────────┘  └──────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Integration Point |
|-----------|----------------|-------------------|
| **Make (check)** | Execute quality gates (lint, typecheck, test) | Called by Build Job before build |
| **Hatchling** | Build wheel and sdist from pyproject.toml | Invoked via `python -m build` in Build Job |
| **hatch-vcs** | Extract version from git tag and inject into package | Auto-invoked by hatchling during build (requires `fetch-depth: 0`) |
| **Git tags** | Trigger workflow and provide version number | Workflow trigger `on: push: tags: 'v*'` |
| **Build Job** | Run checks, build distributions, upload artifacts | New component (GitHub Actions job) |
| **Publish Job** | Download artifacts, publish to PyPI/TestPyPI | New component (uses trusted publishing) |
| **Release Job** | Generate changelog, create GitHub release | New component (uses release actions) |
| **PyPI Trusted Publisher** | OIDC authentication without API tokens | Configured on PyPI website, used by Publish Job |

## Data Flow: Tag Push to PyPI Publish

### Complete Flow Diagram

```
Developer                      GitHub Actions                    External Services
    |                               |                                    |
    | git tag v0.2.0                |                                    |
    | git push origin v0.2.0        |                                    |
    |------------------------------>|                                    |
    |                               |                                    |
    |                      [TRIGGER: Tag Push]                           |
    |                               |                                    |
    |                      ┌─────────────────┐                           |
    |                      │   BUILD JOB     │                           |
    |                      └─────────────────┘                           |
    |                               |                                    |
    |                    1. Checkout (fetch-depth: 0)                    |
    |                               |                                    |
    |                    2. Setup Python 3.11/3.12                       |
    |                               |                                    |
    |                    3. Install package + dev tools                  |
    |                       (pip install -e . ruff mypy pytest)          |
    |                               |                                    |
    |                    4. Run make check                               |
    |                       - make lint (ruff check)                     |
    |                       - make typecheck (mypy)                      |
    |                       - make test (pytest)                         |
    |                               |                                    |
    |                       [GATE: All checks pass?]                     |
    |                               |                                    |
    |                    5. Install build tool                           |
    |                       (pip install build)                          |
    |                               |                                    |
    |                    6. Build distributions                          |
    |                       python -m build                              |
    |                       └─> hatchling.build                          |
    |                           └─> hatch-vcs.version                    |
    |                               (reads git tag v0.2.0)               |
    |                               |                                    |
    |                       Generated: dist/                             |
    |                       - semantic_model_generator-0.2.0.tar.gz      |
    |                       - semantic_model_generator-0.2.0-py3-none-any.whl
    |                               |                                    |
    |                    7. Upload artifacts                             |
    |                       (actions/upload-artifact@v5)                 |
    |                               |                                    |
    |                      ┌─────────────────┐                           |
    |                      │  TESTPYPI JOB   │                           |
    |                      └─────────────────┘                           |
    |                               |                                    |
    |                    8. Download artifacts                           |
    |                               |                                    |
    |                    9. Publish to TestPyPI                          |
    |                       (pypa/gh-action-pypi-publish)                |
    |                       - OIDC token exchange                        |
    |                       - Attestation generation              ----->| TestPyPI
    |                       - Upload wheel + sdist                      |
    |                               |<-----------------------------------|
    |                               |                                    |
    |                      ┌─────────────────┐                           |
    |                      │    PYPI JOB     │                           |
    |                      │ (environment:   │                           |
    |                      │     pypi)       │                           |
    |                      └─────────────────┘                           |
    |                               |                                    |
    |                   [GATE: Manual approval?]                         |
    |<----------- Review request ---|                                    |
    | Approve                       |                                    |
    |------------------------------>|                                    |
    |                               |                                    |
    |                   10. Download artifacts                           |
    |                               |                                    |
    |                   11. Publish to PyPI                              |
    |                       (pypa/gh-action-pypi-publish)                |
    |                       - OIDC token exchange                        |
    |                       - Attestation generation              ----->| PyPI
    |                       - Upload wheel + sdist                      |
    |                               |<-----------------------------------|
    |                               |                                    |
    |                      ┌─────────────────┐                           |
    |                      │  RELEASE JOB    │                           |
    |                      └─────────────────┘                           |
    |                               |                                    |
    |                   12. Generate changelog                           |
    |                       (mikepenz/release-changelog-builder)         |
    |                       - Fetch PRs/commits since last tag           |
    |                       - Categorize by labels                       |
    |                       - Format markdown                            |
    |                               |                                    |
    |                   13. Create GitHub Release              --------->| GitHub Releases
    |                       (softprops/action-gh-release)                |
    |                       - Tag: v0.2.0                                |
    |                       - Changelog as body                          |
    |                       - Attach wheel + sdist                       |
    |                               |<-----------------------------------|
    |                               |                                    |
    |<---------- Release published -|                                    |
```

### Key Integration Points

| From | To | Data | Mechanism |
|------|-----|------|-----------|
| Git tag | Workflow | Tag name (v0.2.0) | GitHub event trigger |
| Git tag | hatch-vcs | Version string (0.2.0) | hatch-vcs reads git history during build |
| Make check | Build Job | Exit code (pass/fail) | Shell command execution |
| Hatchling | Build Job | dist/ artifacts (wheel, sdist) | File system output |
| Build Job | Publish Jobs | dist/ artifacts | GitHub Actions artifacts (upload/download) |
| GitHub Actions | PyPI | OIDC identity token | Trusted publishing token exchange |
| Git history | Changelog | Commits/PRs between tags | GitHub API query |
| Release Job | GitHub Releases | Changelog + artifacts | GitHub API call |

## Recommended Workflow Structure

### File: `.github/workflows/publish.yml`

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # CRITICAL: hatch-vcs needs full git history

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install package and dev tools
        run: |
          pip install -e .
          pip install ruff mypy pytest pytest-cov

      - name: Run quality gates
        run: make check

      - name: Install build tool
        run: pip install build

      - name: Build distributions
        run: python -m build

      - name: Upload distributions
        uses: actions/upload-artifact@v5
        with:
          name: python-package-distributions
          path: dist/

  publish-to-testpypi:
    name: Publish to TestPyPI
    needs: [build]
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # MANDATORY for trusted publishing

    steps:
      - name: Download distributions
        uses: actions/download-artifact@v6
        with:
          name: python-package-distributions
          path: dist/

      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/

  publish-to-pypi:
    name: Publish to PyPI
    needs: [build]
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/semantic-model-generator
    permissions:
      id-token: write  # MANDATORY for trusted publishing

    steps:
      - name: Download distributions
        uses: actions/download-artifact@v6
        with:
          name: python-package-distributions
          path: dist/

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1

  github-release:
    name: Create GitHub Release
    needs: [publish-to-pypi]
    runs-on: ubuntu-latest
    permissions:
      contents: write  # Required for creating releases
      pull-requests: read  # Required for changelog builder

    steps:
      - name: Download distributions
        uses: actions/download-artifact@v6
        with:
          name: python-package-distributions
          path: dist/

      - name: Generate changelog
        id: changelog
        uses: mikepenz/release-changelog-builder-action@v4
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          body: ${{ steps.changelog.outputs.changelog }}
          files: dist/*
```

### Structure Rationale

- **Tag trigger only:** Prevents accidental publishes from branches
- **Build job runs first:** Quality gates fail fast before building
- **Matrix testing:** Validates on Python 3.11 and 3.12 per existing CI
- **Separate publish jobs:** TestPyPI publishes automatically, PyPI requires environment approval
- **Artifact passing:** Ensures same artifacts tested in build are published (not rebuilt)
- **GitHub release last:** Only creates release after successful PyPI publish

## Architectural Patterns

### Pattern 1: Trusted Publishing (OIDC Authentication)

**What:** Use OpenID Connect tokens instead of long-lived API tokens for PyPI authentication. GitHub Actions exchanges short-lived identity tokens with PyPI.

**When to use:** Always, for any PyPI publishing workflow (official best practice as of 2024+).

**Trade-offs:**
- Pros: No secrets to manage, leak-proof, automatic attestation signing, scoped permissions
- Cons: Requires PyPI configuration step, GitHub Actions only (not usable locally)

**Implementation:**
1. Configure trusted publisher on PyPI with: repository owner, repository name, workflow filename, environment name (optional)
2. Add `permissions: id-token: write` to publish job
3. Use `pypa/gh-action-pypi-publish@release/v1` without username/password inputs

**Sources:**
- [PyPI Trusted Publishers Documentation](https://docs.pypi.org/trusted-publishers/)
- [Official Python Packaging Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

### Pattern 2: Build Artifact Passing

**What:** Build distributions once in a dedicated build job, upload as artifacts, download in dependent jobs for publishing.

**When to use:** Always in CD pipelines. Ensures identical artifacts are tested and published.

**Trade-offs:**
- Pros: Build once, test once, publish identical artifacts; reduces non-determinism
- Cons: Slight complexity increase (upload/download steps), artifact storage usage

**Implementation:**
```yaml
# Build job
- uses: actions/upload-artifact@v5
  with:
    name: python-package-distributions
    path: dist/

# Publish job
needs: [build]
steps:
  - uses: actions/download-artifact@v6
    with:
      name: python-package-distributions
      path: dist/
```

**Sources:**
- [Python Packaging Guide: Build/Publish Separation](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

### Pattern 3: Environment Protection Rules

**What:** GitHub Actions environments with required reviewers for manual approval gates before production deployment.

**When to use:** For production PyPI publishing to prevent accidental releases. Recommended for TestPyPI auto-publish, PyPI manual approval.

**Trade-offs:**
- Pros: Human-in-loop safety gate, audit trail, prevents automation errors
- Cons: Slower releases (requires human), not suitable for fully automated pipelines
- Note: Free/Pro plans only get this on public repos; private repos require Teams/Enterprise

**Implementation:**
```yaml
publish-to-pypi:
  environment:
    name: pypi
    url: https://pypi.org/p/<package-name>
  permissions:
    id-token: write
```

Then configure environment protection rules in GitHub repo settings:
- Settings → Environments → pypi → Required reviewers (up to 6 users/teams)
- Optional: Prevent self-reviews for additional safety

**Sources:**
- [GitHub Docs: Managing Environments](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Environment Protection Rules Guide](https://oneuptime.com/blog/post/2026-01-25-github-actions-environment-protection-rules/view)

### Pattern 4: VCS Versioning with fetch-depth: 0

**What:** Checkout full git history (not shallow clone) so hatch-vcs can read tags and derive version.

**When to use:** Always when using hatch-vcs or setuptools-scm for version management.

**Trade-offs:**
- Pros: Automatic version from tags, no manual version bumping
- Cons: Slightly slower checkout (full history vs shallow), requires annotated or lightweight tags

**Implementation:**
```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Full history for hatch-vcs
```

Without this, hatch-vcs cannot find tags and version resolution fails.

**Sources:**
- Existing CI workflow (already uses this pattern)
- [hatch-vcs PyPI documentation](https://pypi.org/project/hatch-vcs/)

### Pattern 5: TestPyPI Staging Pipeline

**What:** Publish to TestPyPI automatically for all tagged releases, use as staging environment before production PyPI.

**When to use:** For testing installation workflows and verifying package metadata before production publish.

**Trade-offs:**
- Pros: Catch upload errors before production, test pip install flow, verify metadata
- Cons: TestPyPI is not a mirror (different packages exist), not suitable for dependency testing

**Implementation:**
```yaml
publish-to-testpypi:
  needs: [build]
  permissions:
    id-token: write
  steps:
    - uses: pypa/gh-action-pypi-publish@release/v1
      with:
        repository-url: https://test.pypi.org/legacy/
```

Requires separate trusted publisher configuration on test.pypi.org.

**Sources:**
- [Python Packaging Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

## Integration with Existing Tooling

### Make Integration

**Existing command:** `make check` (runs lint, typecheck, test)

**CD integration point:** Build job step before building distributions

```yaml
- name: Run quality gates
  run: make check
```

**Why this works:** Make is already installed on GitHub Actions ubuntu-latest runners. No additional setup required.

**Design decision:** Reuse existing quality gates rather than duplicating ruff/mypy/pytest commands in workflow. Single source of truth for "what checks must pass."

### Hatchling Integration

**Existing config:** `pyproject.toml` declares `hatchling` as build backend with `hatch-vcs` plugin

**CD integration point:** Build job invokes via standard build frontend

```yaml
- name: Install build tool
  run: pip install build

- name: Build distributions
  run: python -m build
```

**Why this approach:** `python -m build` is PEP 517 standard build frontend. Works with any backend (hatchling, setuptools, flit, poetry). Generates both wheel (.whl) and source distribution (.tar.gz).

**Design decision:** Use `build` package (official PyPA tool) rather than `hatch build` command. More portable if build backend changes.

**Sources:**
- [Python Packaging Best Practices 2026](https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/)
- [Hatchling PEP 517 Compliance](https://johal.in/hatchling-build-backend-pep-517-compliant-python-packaging-2026-2/)

### hatch-vcs Integration

**Existing config:** `pyproject.toml` declares `source = "vcs"` with version-file generation

**CD integration point:** Automatic during build if git history available

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # CRITICAL: hatch-vcs reads tags from git history
```

**How it works:**
1. Workflow triggered by tag push (e.g., `v0.2.0`)
2. Checkout fetches full git history including tags
3. `python -m build` invokes hatchling
4. Hatchling calls hatch-vcs hook
5. hatch-vcs scans git history for tags matching pattern `v*`
6. Extracts version `0.2.0` from tag `v0.2.0`
7. Generates `src/semantic_model_generator/_version.py` with `__version__ = "0.2.0"`
8. Hatchling builds package with version `0.2.0`

**Critical requirement:** `fetch-depth: 0` in checkout action. Default shallow clone (depth=1) doesn't include tags.

**Sources:**
- Existing CI workflow comment
- [hatch-vcs documentation](https://github.com/ofek/hatch-vcs)

### Git Tag Integration

**Existing workflow:** Milestone-based tags (v0.1.0, v0.2.0) created manually

**CD integration point:** Workflow trigger

```yaml
on:
  push:
    tags:
      - 'v*'
```

**Developer workflow:**
```bash
git tag v0.2.0
git push origin v0.2.0
```

**What happens:**
1. Developer creates annotated or lightweight tag
2. `git push origin v0.2.0` triggers GitHub webhook
3. GitHub Actions workflow starts
4. Tag name becomes `${{ github.ref }}` (refs/tags/v0.2.0)
5. Tag name used for version extraction and release creation

**Design decision:** Match existing tag naming convention (`v*` prefix). No changes to developer workflow.

## New Components Needed

### Component 1: Workflow File

**File:** `.github/workflows/publish.yml`

**Purpose:** Define CD pipeline orchestration

**Content:** 4 jobs (build, publish-to-testpypi, publish-to-pypi, github-release)

**Dependencies:** None (new file)

**When to create:** First phase of milestone

### Component 2: PyPI Trusted Publisher Configuration

**Location:** PyPI.org website (project settings)

**Purpose:** Enable OIDC authentication without API tokens

**Configuration values:**
- Owner: `<github-username-or-org>`
- Repository: `semantic-model-generator`
- Workflow filename: `publish.yml`
- Environment name: `pypi` (recommended for manual approval)

**Dependencies:** Requires PyPI project to exist (already exists from v0.1.0)

**When to configure:** Before workflow first runs, or workflow will fail with authentication error

**Sources:**
- [Adding Trusted Publisher Guide](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)

### Component 3: TestPyPI Trusted Publisher Configuration

**Location:** test.pypi.org website

**Purpose:** Enable TestPyPI staging publishes

**Configuration values:** Same as PyPI but no environment (auto-publish)

**Dependencies:** Requires TestPyPI project (must create separately, different from PyPI)

**When to configure:** Before workflow first runs

### Component 4: GitHub Environment

**Location:** GitHub repo settings → Environments → pypi

**Purpose:** Manual approval gate for production publishes

**Configuration:**
- Environment name: `pypi`
- Protection rules: Required reviewers (select maintainers)
- Optional: Prevent self-reviews

**Dependencies:** None

**When to configure:** After workflow file created, before first tag push

**Note:** Only available on public repos for Free/Pro plans. Private repos require Teams/Enterprise.

**Sources:**
- [GitHub Environment Protection Rules](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)

### Component 5: Changelog Generation Configuration (Optional)

**File:** `.github/release-changelog-config.json` (optional)

**Purpose:** Customize changelog categorization

**Default behavior:** mikepenz/release-changelog-builder works without config

**Advanced config:** Can categorize PRs by labels, customize sections, filter changes

**Dependencies:** None (optional enhancement)

**When to create:** Later phase if default changelog format insufficient

**Sources:**
- [Release Changelog Builder](https://github.com/marketplace/actions/release-changelog-builder)

## Anti-Patterns

### Anti-Pattern 1: Storing PyPI API Tokens as Secrets

**What people do:** Create API token on PyPI, store as `PYPI_API_TOKEN` secret in GitHub, use in workflow

**Why it's wrong:** Long-lived secrets can leak, require rotation, no audit trail, manually managed, can't scope to specific workflows

**Do this instead:** Use trusted publishing with OIDC. No secrets to manage, automatic attestation signing, scoped to specific repo/workflow.

**Migration path:** If existing token in use, delete from secrets after trusted publisher configured and verified working.

**Sources:**
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions PyPI Publish Best Practices](https://blog.pecar.me/automate-hatch-publish)

### Anti-Pattern 2: Rebuilding in Publish Job

**What people do:** Checkout code and run `python -m build` in publish job

**Why it's wrong:** Publishes different artifacts than tested in build job. Non-deterministic builds can cause subtle differences. Wastes compute rebuilding identical artifacts.

**Do this instead:** Build once in build job, upload as artifacts, download in publish jobs. Guarantees tested artifacts are published.

**Sources:**
- [Python Packaging Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

### Anti-Pattern 3: Shallow Clone with hatch-vcs

**What people do:** Use default checkout action (depth=1) or forget `fetch-depth: 0`

**Why it's wrong:** hatch-vcs cannot find tags in shallow clone. Version resolution fails or produces incorrect version (0.0.0 or commit-based dev version).

**Do this instead:** Always use `fetch-depth: 0` when using hatch-vcs or setuptools-scm.

**Detection:**
- Build logs show version 0.0.0 or long commit hash
- hatch-vcs warnings about "no tags found"

**Sources:**
- Existing CI workflow comment
- [hatch-vcs documentation](https://github.com/ofek/hatch-vcs)

### Anti-Pattern 4: Running CD on All Commits

**What people do:** Trigger publish workflow on push to main or all branches

**Why it's wrong:** Accidentally publishes development snapshots, no semantic versioning, requires version bumping in every commit.

**Do this instead:** Trigger only on tag pushes (`on: push: tags: 'v*'`). Developer explicitly creates version tag when ready to release.

**Sources:**
- [Python Packaging Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

### Anti-Pattern 5: Skipping TestPyPI

**What people do:** Only configure PyPI publishing, no staging environment

**Why it's wrong:** First deployment error appears in production. Metadata errors, upload failures, or package structure issues caught too late.

**Do this instead:** Always publish to TestPyPI first (can be automatic), verify with `pip install --index-url`, then publish to PyPI.

**Sources:**
- [Python Packaging Guide: TestPyPI Usage](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single maintainer | Manual approval on PyPI environment, auto-publish TestPyPI, build on Python 3.11 only |
| Small team (2-5) | Add team as required reviewers, prevent self-reviews, matrix test Python 3.11/3.12 |
| Large team (5+) | Remove manual approval (rely on branch protection + code review), add automated smoke tests after publish |

### Scaling Priorities

1. **First bottleneck:** Manual approval slows releases
   - **Fix:** Remove environment protection rules, rely on PR review + branch protection for main
   - **When:** When team has established release discipline and automated testing coverage

2. **Second bottleneck:** Sequential job execution (build → testpypi → pypi → release)
   - **Fix:** Run TestPyPI and PyPI publishes in parallel (requires separate build job for each or shared artifacts)
   - **When:** When release latency matters (currently ~5-10 minutes total is acceptable)

3. **Third bottleneck:** Matrix testing on multiple Python versions increases build time
   - **Fix:** Test on single version (3.11) in CD, rely on CI for multi-version testing
   - **When:** When build time matters more than runtime validation on multiple versions

## Build Order for Phases

Based on dependencies and risk:

### Phase 1: Infrastructure Setup (No Code)
1. **Create GitHub environment** (`pypi`) with protection rules
2. **Configure PyPI trusted publisher** with workflow filename, environment name
3. **Configure TestPyPI trusted publisher** (no environment)

**Why first:** Prerequisites for workflow execution. Can be done before code changes. Lowest risk.

**Verification:** Check GitHub settings show environment, PyPI shows trusted publisher.

### Phase 2: Workflow Implementation
4. **Create workflow file** `.github/workflows/publish.yml` with all 4 jobs
5. **Test with branch push** (temporarily change trigger to test)
6. **Revert to tag trigger** after validation

**Why second:** Core component. Depends on Phase 1 configuration. Medium risk (can test on branch before tag).

**Verification:** Workflow appears in Actions tab, dry-run succeeds on test branch.

### Phase 3: End-to-End Validation
7. **Create test tag** (e.g., `v0.1.1` or `v0.2.0-alpha.1`)
8. **Push tag** to trigger workflow
9. **Approve PyPI publish** if manual approval configured
10. **Verify installations** from TestPyPI and PyPI

**Why third:** Integration test. Depends on Phases 1-2. Highest risk (produces real releases).

**Verification:** Package appears on PyPI with correct version, pip install works, GitHub release created.

### Phase 4: Documentation & Monitoring (Post-Launch)
11. **Document release process** in CONTRIBUTING.md or RELEASING.md
12. **Set up workflow failure alerts** (GitHub notifications or Slack)

**Why last:** Operational concerns after pipeline proven working.

## Sources

### Official Documentation (HIGH confidence)
- [Python Packaging Guide: GitHub Actions CD](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [PyPI Trusted Publishers Documentation](https://docs.pypi.org/trusted-publishers/)
- [PyPA gh-action-pypi-publish](https://github.com/marketplace/actions/pypi-publish)
- [GitHub Docs: Managing Environments](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)

### Current Best Practices (MEDIUM confidence)
- [Python Packaging Best Practices: Hatch in 2026](https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/)
- [Hatchling PEP 517 Compliant Packaging 2026](https://johal.in/hatchling-build-backend-pep-517-compliant-python-packaging-2026-2/)
- [Automate Hatch Publish with GitHub Actions](https://blog.pecar.me/automate-hatch-publish)
- [Environment Protection Rules Guide (2026-01-25)](https://oneuptime.com/blog/post/2026-01-25-github-actions-environment-protection-rules/view)

### Tools & Actions (HIGH confidence)
- [hatch-vcs GitHub Repository](https://github.com/ofek/hatch-vcs)
- [Release Changelog Builder Action](https://github.com/marketplace/actions/release-changelog-builder)
- [actions/checkout@v4](https://github.com/actions/checkout)
- [actions/setup-python@v5](https://github.com/actions/setup-python)
- [actions/upload-artifact@v5](https://github.com/actions/upload-artifact)
- [actions/download-artifact@v6](https://github.com/actions/download-artifact)

### Existing Project Context (HIGH confidence)
- Project pyproject.toml
- Project Makefile
- Existing CI workflow
- v0.1.0 Milestone Audit

---
*Architecture research for: GitHub Actions CD Pipeline Integration with Hatchling + Make + Git*
*Researched: 2026-02-10*
*Confidence: HIGH (official docs + verified existing patterns)*
