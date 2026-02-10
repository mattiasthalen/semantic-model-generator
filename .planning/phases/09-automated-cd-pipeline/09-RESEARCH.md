# Phase 9: Automated CD Pipeline - Research

**Researched:** 2026-02-10
**Domain:** GitHub Actions CI/CD for Python package publishing to PyPI
**Confidence:** HIGH

## Summary

This phase implements a GitHub Actions workflow that automates the complete release process: quality gates, package building, PyPI publishing via OIDC Trusted Publishing, and GitHub release creation. The workflow triggers on `v*` tags pushed to main, runs full quality checks on Python 3.11 and 3.12 in parallel, builds both wheel and sdist distributions, verifies installation, publishes to PyPI without API tokens using OIDC, and creates a GitHub release with changelog and links.

The standard stack is mature and well-documented: GitHub Actions for CI/CD orchestration, PyPA's `gh-action-pypi-publish` for publishing with Trusted Publishing, `python -m build` for creating distributions, and `softprops/action-gh-release` for release automation. PyPI Trusted Publishing is the current best practice, eliminating long-lived API tokens in favor of short-lived OIDC tokens issued by GitHub's identity provider. The project already uses hatchling with hatch-vcs for dynamic versioning from git tags, which requires `fetch-depth: 0` in checkout steps.

**Primary recommendation:** Use job-based workflow architecture (validate → build → publish → release) with artifact passing between jobs for separation of concerns. Set `fail-fast: false` for parallel quality checks to collect all failures. Configure PyPI Trusted Publishing with strongly-recommended environment protection requiring manual approval. Extract changelog sections from MILESTONES.md using shell tools, and detect pre-releases via tag pattern matching.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Trigger conditions:**
- Accept `v*` pattern including pre-releases (v0.2.0, v0.2.0-rc1, v0.2.0-beta1)
- Trigger only from main branch (no feature branch publishes)
- Include manual `workflow_dispatch` option for testing/republishing
- Extract changelog from MILESTONES.md (not auto-generated from commits)
- On any failure: just fail the workflow (no notifications, no draft releases)

**Quality gate execution:**
- No dependency caching (always fresh install, more reliable)
- Run Python 3.11 and 3.12 checks in parallel (faster)
- Let all jobs finish even if one fails (better debugging information)

**Build verification:**
- Test wheel only (not sdist) for installation verification
- Run installation test on Linux only (assumes cross-platform compatibility)

**Release artifacts:**
- Release title: Just the tag (e.g., "v0.2.0")
- Attach both wheel and sdist files to GitHub release
- Release notes structure: Changelog section followed by links section (PyPI, MILESTONES.md)
- Mark pre-release tags (rc, beta, alpha) as pre-releases in GitHub UI

### Claude's Discretion

- Extra validation beyond make check (e.g., version number validation)
- Verification method details (import vs smoke test)
- Package inspection approach (whether to list contents before upload)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| GitHub Actions | N/A | CI/CD orchestration | Native GitHub integration, free for public repos, extensive ecosystem |
| pypa/gh-action-pypi-publish | `release/v1` | PyPI publishing with Trusted Publishing | Official PyPA action, OIDC support, automatic attestations (PEP 740) |
| python -m build | 1.4.0+ | PEP 517 build frontend | PyPA-recommended, backend-agnostic, isolation support |
| softprops/action-gh-release | `v2` | GitHub release automation | Mature action, glob support for assets, pre-release detection |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| actions/checkout | `v4` | Repository checkout | Every workflow - required for code access |
| actions/setup-python | `v5` | Python installation | Python workflows - installs specified versions |
| actions/upload-artifact | `v4` | Inter-job artifact passing | Multi-job workflows - share build outputs |
| actions/download-artifact | `v4` | Artifact retrieval | Publishing jobs - retrieve built distributions |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Trusted Publishing | API tokens | Tokens are less secure (long-lived, leak risk) and require secret management |
| python -m build | hatch build directly | build is backend-agnostic, better for standardization |
| softprops/action-gh-release | actions/create-release | create-release is deprecated, softprops is maintained |
| Job-based workflow | Single job | Multiple jobs provide better separation, artifact preservation, easier debugging |

**Installation:**
```bash
# In workflow:
pip install build  # For building distributions

# No installation needed for GitHub Actions (uses: references)
```

## Architecture Patterns

### Recommended Workflow Structure

```yaml
.github/workflows/
└── publish.yml          # CD workflow (tag → quality → build → publish → release)
```

### Pattern 1: Multi-Job CD Pipeline with Artifact Passing

**What:** Separate jobs for quality gates, build, publish, and release with artifact passing
**When to use:** CD workflows requiring verification before publish, artifact preservation, auditability

**Example:**
```yaml
# Source: Official PyPA Publishing Guide
# https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/

name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'
    branches:
      - main  # Only allow tags from main branch
  workflow_dispatch:  # Manual trigger for testing

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false  # Let all versions complete for better debugging
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Required for hatch-vcs version detection

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install package and dev tools
        run: |
          pip install -e .
          pip install ruff mypy pytest pytest-cov

      - name: Run all checks
        run: make check

  build:
    needs: quality-gates
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Required for hatch-vcs

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install build frontend
        run: pip install build

      - name: Build distributions
        run: python -m build

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: distributions
          path: dist/

  verify-wheel:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: distributions
          path: dist/

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install wheel
        run: pip install dist/*.whl

      - name: Verify import
        run: python -c "import semantic_model_generator; print(semantic_model_generator.__version__)"

  publish-to-pypi:
    needs: verify-wheel
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/semantic-model-generator
    permissions:
      id-token: write  # MANDATORY for Trusted Publishing
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: distributions
          path: dist/

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1

  create-release:
    needs: publish-to-pypi
    runs-on: ubuntu-latest
    permissions:
      contents: write  # Required to create releases
    steps:
      - uses: actions/checkout@v4

      - name: Extract changelog
        id: changelog
        run: |
          # Extract section for this version from MILESTONES.md
          VERSION=${GITHUB_REF_NAME#v}
          # Implementation specific to MILESTONES.md format

      - uses: actions/download-artifact@v4
        with:
          name: distributions
          path: dist/

      - name: Create release
        uses: softprops/action-gh-release@v2
        with:
          name: ${{ github.ref_name }}
          body: |
            ${{ steps.changelog.outputs.notes }}

            ## Links
            - [PyPI](https://pypi.org/project/semantic-model-generator/${{ github.ref_name }}/)
            - [MILESTONES.md](.planning/MILESTONES.md)
          files: dist/*
          prerelease: ${{ contains(github.ref_name, '-rc') || contains(github.ref_name, '-beta') || contains(github.ref_name, '-alpha') }}
```

### Pattern 2: Tag Trigger with Branch Filtering

**What:** Trigger on tag push but only from main branch to prevent accidental publishes
**When to use:** All production CD workflows to ensure only vetted code publishes

**Example:**
```yaml
# Source: GitHub Actions Documentation
# https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow

on:
  push:
    tags:
      - 'v*'           # Match v1.0.0, v0.2.0-rc1, etc.
    branches:
      - main           # Only tags on main branch

# Additional runtime check in job:
jobs:
  check-branch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Verify tag on main
        run: |
          if ! git branch -r --contains ${{ github.ref }} | grep -q 'origin/main'; then
            echo "Error: Tag must be on main branch"
            exit 1
          fi
```

### Pattern 3: Trusted Publishing Configuration

**What:** OIDC-based authentication eliminating API tokens
**When to use:** All PyPI publishing workflows (security best practice)

**Configuration steps:**
1. On PyPI, navigate to project → Manage → Publishing
2. Add GitHub Actions publisher with:
   - Owner: repository owner (e.g., `your-org`)
   - Repository: repository name (e.g., `semantic-model-generator`)
   - Workflow: filename (e.g., `publish.yml`)
   - Environment: name (e.g., `pypi`) — strongly recommended for approval gates

**Workflow requirements:**
```yaml
# Source: PyPI Trusted Publishing Documentation
# https://docs.pypi.org/trusted-publishers/using-a-publisher/

jobs:
  publish:
    environment: pypi  # Must match PyPI configuration
    permissions:
      id-token: write  # MANDATORY - workflow fails without this
```

### Pattern 4: Pre-release Detection

**What:** Automatically mark releases as pre-release based on tag pattern
**When to use:** Projects using semantic versioning with pre-release identifiers

**Example:**
```yaml
# Source: softprops/action-gh-release examples
# https://github.com/softprops/action-gh-release

- uses: softprops/action-gh-release@v2
  with:
    prerelease: ${{ contains(github.ref_name, '-rc') || contains(github.ref_name, '-beta') || contains(github.ref_name, '-alpha') }}
```

### Pattern 5: Matrix Strategy with fail-fast Control

**What:** Parallel testing across Python versions with complete failure reporting
**When to use:** Quality gates requiring multiple version testing

**Example:**
```yaml
# Source: GitHub Actions Documentation
# https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/running-variations-of-jobs-in-a-workflow

strategy:
  fail-fast: false  # Let all versions complete even if one fails
  matrix:
    python-version: ["3.11", "3.12"]
```

### Anti-Patterns to Avoid

- **Single-job workflows:** Mixing quality gates, build, and publish in one job prevents artifact preservation and makes debugging harder
- **Dependency caching in CD:** Cache hits can mask dependency conflicts; fresh installs ensure reproducibility
- **API token authentication:** Long-lived secrets are security risks; use Trusted Publishing
- **Shallow clones with VCS versioning:** hatch-vcs requires full history; always use `fetch-depth: 0`
- **Publishing before verification:** Always verify wheel installation before publishing (PyPI doesn't allow re-uploads)
- **Hardcoded versions:** Let hatch-vcs extract from tags; manual versions cause drift

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PyPI authentication | Custom token management, manual credentials | Trusted Publishing (OIDC) | GitHub mints short-lived tokens automatically, no secrets to leak or rotate |
| Package building | Custom setup.py builds, manual wheel creation | `python -m build` | Handles PEP 517 backends correctly, enforces isolation, catches build issues early |
| Release creation | curl to GitHub API, custom scripts | `softprops/action-gh-release` | Handles authentication, file uploads, pre-release detection, markdown formatting |
| Artifact passing | Storing in repo, external storage | `actions/upload-artifact` + `actions/download-artifact` | Native GitHub storage, automatic cleanup, workflow-scoped access |
| Version extraction | Regex parsing, custom scripts | hatch-vcs with git tags | Official solution, handles edge cases, integrates with build backend |
| Metadata validation | Custom checks | `twine check` | PyPA-official, validates against PyPI requirements, catches rendering issues |
| Changelog extraction | Complex regex | Dedicated actions or simple sed | Markdown structure is complex, edge cases abound |

**Key insight:** GitHub Actions and PyPI have invested heavily in making publishing secure and simple. Trusted Publishing is the result of PyPI's security team addressing the API token leak problem that plagued the ecosystem. Use official tools that have handled edge cases you haven't thought of yet.

## Common Pitfalls

### Pitfall 1: Missing fetch-depth with VCS Versioning

**What goes wrong:** hatch-vcs fails with "no suitable tags" or incorrect version numbers when workflow uses shallow clone (default `fetch-depth: 1`)

**Why it happens:** Shallow clones don't include tags by default. hatch-vcs needs git history to find the most recent tag and calculate version.

**How to avoid:**
```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Required for hatch-vcs
```

**Warning signs:** Build fails with version errors, or package gets version `0.0.0`

### Pitfall 2: Forgotten id-token Permission

**What goes wrong:** Trusted Publishing fails with "This request requires the `id-token: write` permission" error

**Why it happens:** OIDC token generation requires explicit permission grant. GitHub Actions denies by default for security.

**How to avoid:** Set at job level (recommended) or workflow level:
```yaml
jobs:
  publish:
    permissions:
      id-token: write  # MANDATORY for Trusted Publishing
```

**Warning signs:** Publishing step fails immediately with permission error

### Pitfall 3: PyPI Duplicate Version Upload

**What goes wrong:** Workflow fails with "File already exists" when trying to republish the same version

**Why it happens:** PyPI prohibits version overwrites to ensure reproducibility. Once published, a version is immutable.

**How to avoid:**
1. Never reuse version numbers — bump version for every publish
2. Use TestPyPI for testing before production publish
3. For pre-release testing, use version suffixes: `v0.2.0-rc1`, `v0.2.0-rc2`
4. Optional: Add version check before publishing:
```yaml
- name: Check version not on PyPI
  run: |
    VERSION=${GITHUB_REF_NAME#v}
    if curl -s "https://pypi.org/pypi/semantic-model-generator/json" | jq -e ".releases.\"$VERSION\""; then
      echo "Error: Version $VERSION already exists on PyPI"
      exit 1
    fi
```

**Warning signs:** Publish step fails with 400 Bad Request, "File already exists" message

### Pitfall 4: Tag on Wrong Branch

**What goes wrong:** Workflow publishes code from a feature branch instead of main, deploying untested or incomplete changes

**Why it happens:** Tags can be pushed from any branch. Without branch filtering, any tag triggers publish regardless of branch.

**How to avoid:**
```yaml
on:
  push:
    tags: ['v*']
    branches: [main]  # Trigger only for tags on main

# Additional runtime verification:
- name: Verify tag on main
  run: |
    if ! git branch -r --contains ${{ github.ref }} | grep -q 'origin/main'; then
      echo "Error: Tag must be on main branch"
      exit 1
    fi
```

**Warning signs:** Published package contains unexpected changes, version doesn't match main branch state

### Pitfall 5: Environment Not Configured on PyPI

**What goes wrong:** Trusted Publishing fails with authentication error despite correct workflow configuration

**Why it happens:** PyPI must be pre-configured with matching publisher settings (owner, repo, workflow, environment). Mismatch causes authentication failure.

**How to avoid:**
1. Add publisher on PyPI: Project → Manage → Publishing → GitHub Actions
2. Ensure exact match:
   - Owner name (not display name)
   - Repository name (exact case)
   - Workflow filename (must match file in `.github/workflows/`)
   - Environment name (must match `environment:` in workflow)
3. Environment name is optional but strongly recommended for approval gates

**Warning signs:** Authentication fails despite `id-token: write` permission, logs show OIDC token rejection

### Pitfall 6: Build Artifacts in Dirty Directory

**What goes wrong:** Old distribution files (from previous builds) get published alongside new ones, causing version conflicts or wrong file uploads

**Why it happens:** `python -m build` outputs to `dist/` but doesn't clean it first. Repeated local builds accumulate files.

**How to avoid:**
```yaml
- name: Clean dist directory
  run: rm -rf dist/

- name: Build distributions
  run: python -m build
```

Or rely on clean workflow environment (no prior builds)

**Warning signs:** Multiple versions in dist/, upload includes unexpected files

### Pitfall 7: Missing Environment Protection

**What goes wrong:** Automated workflow publishes to PyPI without human verification, potential for accidental publishes or broken releases

**Why it happens:** Default GitHub environments have no protection rules. Publish job runs automatically after quality gates pass.

**How to avoid:**
1. Configure GitHub environment with required reviewers:
   - Settings → Environments → pypi → Required reviewers
   - Add trusted maintainers (up to 6 reviewers)
2. Workflow references environment:
```yaml
jobs:
  publish:
    environment:
      name: pypi
      url: https://pypi.org/p/semantic-model-generator
```

**Warning signs:** No approval prompt during publish workflow, releases happen too fast

## Code Examples

Verified patterns from official sources:

### Building Distributions (PyPA Build)

```bash
# Source: PyPA Build Documentation
# https://build.pypa.io/en/latest/

# Install build frontend
pip install build

# Build both wheel and sdist
python -m build

# Output: dist/semantic_model_generator-X.Y.Z.tar.gz (sdist)
#         dist/semantic_model_generator-X.Y.Z-py3-none-any.whl (wheel)
```

### Verifying Wheel Installation

```yaml
# Source: Scientific Python GitHub Actions Guide
# https://learn.scientific-python.org/development/guides/gha-pure/

- name: Install wheel
  run: pip install dist/*.whl

- name: Verify import
  run: python -c "import semantic_model_generator; print(semantic_model_generator.__version__)"

# Alternative: Run subset of tests
- name: Smoke test
  run: pytest tests/test_imports.py --no-cov
```

### Extracting Tag Version

```yaml
# Source: GitHub Actions Context Documentation
# https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/accessing-contextual-information-about-workflow-runs

- name: Extract version
  id: version
  run: |
    # GITHUB_REF_NAME contains just the tag name (e.g., "v0.2.0")
    echo "tag=${GITHUB_REF_NAME}" >> $GITHUB_OUTPUT
    echo "version=${GITHUB_REF_NAME#v}" >> $GITHUB_OUTPUT

- name: Use version
  run: echo "Publishing version ${{ steps.version.outputs.version }}"
```

### Extracting Changelog Section

```bash
# Source: Community patterns for markdown section extraction
# Adapted for MILESTONES.md structure

# Extract milestone section for version
VERSION=${GITHUB_REF_NAME#v}

# Approach 1: Using sed (more reliable for specific markers)
sed -n "/## v${VERSION}/,/^##/p" .planning/MILESTONES.md | sed '$d'

# Approach 2: Using awk (for more complex extraction)
awk "/## v${VERSION}/,/^## [^#]/" .planning/MILESTONES.md | head -n -1
```

### Complete Publish Job

```yaml
# Source: PyPI Trusted Publishing Guide + softprops/action-gh-release
# https://docs.pypi.org/trusted-publishers/using-a-publisher/
# https://github.com/softprops/action-gh-release

publish:
  needs: [quality-gates, build, verify-wheel]
  runs-on: ubuntu-latest
  environment:
    name: pypi
    url: https://pypi.org/p/semantic-model-generator
  permissions:
    id-token: write  # Trusted Publishing
    contents: write  # Release creation
  steps:
    - uses: actions/checkout@v4

    - uses: actions/download-artifact@v4
      with:
        name: distributions
        path: dist/

    - name: Extract changelog
      id: changelog
      run: |
        VERSION=${GITHUB_REF_NAME#v}
        NOTES=$(sed -n "/## v${VERSION}/,/^##/p" .planning/MILESTONES.md | sed '$d')
        echo "notes<<EOF" >> $GITHUB_OUTPUT
        echo "$NOTES" >> $GITHUB_OUTPUT
        echo "EOF" >> $GITHUB_OUTPUT

    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1

    - name: Create GitHub release
      uses: softprops/action-gh-release@v2
      with:
        name: ${{ github.ref_name }}
        body: |
          ${{ steps.changelog.outputs.notes }}

          ## Links
          - [PyPI](https://pypi.org/project/semantic-model-generator/${{ github.ref_name }}/)
          - [MILESTONES.md](.planning/MILESTONES.md)
        files: dist/*
        prerelease: ${{ contains(github.ref_name, '-rc') || contains(github.ref_name, '-beta') || contains(github.ref_name, '-alpha') }}
```

### Validating Package Metadata

```yaml
# Source: PyPA Twine Documentation
# https://twine.readthedocs.io/

- name: Install twine
  run: pip install twine

- name: Check distributions
  run: twine check dist/*
```

### Inspecting Wheel Contents (Optional)

```yaml
# Source: check-wheel-contents PyPI package
# https://pypi.org/project/check-wheel-contents/

- name: Install check-wheel-contents
  run: pip install check-wheel-contents

- name: Inspect wheel
  run: check-wheel-contents dist/*.whl

# Or simpler: list contents
- name: List wheel contents
  run: unzip -l dist/*.whl
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| API tokens in secrets | OIDC Trusted Publishing | 2023 (PyPI announcement) | Eliminates long-lived credentials, prevents token leaks, reduces secret management |
| Manual version bumping | VCS-based versioning (hatch-vcs) | 2020s (PEP 517 adoption) | Single source of truth (git tags), eliminates version drift, automates process |
| setup.py builds | `python -m build` (PEP 517) | 2021+ (PEP 517 adoption) | Backend-agnostic, isolated builds, catches dependency issues early |
| actions/create-release | softprops/action-gh-release | 2020 (create-release deprecated) | Maintained action, better features, glob support |
| Dependency caching in CD | No caching (fresh installs) | Best practice evolution | Catches dependency conflicts, ensures reproducibility, prevents cache poisoning |
| Single job workflows | Multi-job with artifacts | 2020s (Actions maturity) | Better separation, artifact preservation, easier debugging, parallel execution |
| Draft releases on failure | Fail workflow immediately | Simplicity trend | Clearer CI/CD state, no orphaned drafts, simpler error handling |

**Deprecated/outdated:**
- **actions/create-release**: Deprecated by GitHub, use softprops/action-gh-release or GitHub CLI
- **Manual token rotation**: Trusted Publishing eliminates this entirely
- **setup.py builds**: Use PEP 517 build frontends (python -m build)
- **Poetry publish directly**: Better to use build + gh-action-pypi-publish for consistency
- **Branch-specific caching in CD**: No longer recommended for publish workflows (reliability over speed)

## Open Questions

1. **Changelog extraction from MILESTONES.md format**
   - What we know: MILESTONES.md uses `## v{version}` headings for releases
   - What's unclear: Exact structure of milestone sections (nested headings, formatting)
   - Recommendation: Examine MILESTONES.md during planning, write extraction script specific to its structure

2. **Version validation strictness**
   - What we know: User wants extra validation beyond make check (Claude's discretion)
   - What's unclear: Whether to validate tag matches hatch-vcs output, check SemVer compliance, verify against PyPI
   - Recommendation: Implement basic check that tag matches built package version, skip complex validation (build failure is sufficient signal)

3. **Wheel verification depth**
   - What we know: User wants wheel installation test (import vs smoke test is Claude's discretion)
   - What's unclear: Whether simple import is sufficient or should run actual tests
   - Recommendation: Start with import verification (`import semantic_model_generator; print(__version__)`), add smoke test if import is too shallow

4. **Package inspection before upload**
   - What we know: Claude's discretion whether to list contents before upload
   - What's unclear: Value vs noise tradeoff, whether inspection catches real issues
   - Recommendation: Skip inspection (twine check provides metadata validation, contents are deterministic from source)

## Sources

### Primary (HIGH confidence)

**Official Documentation:**
- [PyPI Trusted Publishers Documentation](https://docs.pypi.org/trusted-publishers/) - Complete OIDC setup guide
- [PyPI Adding a Trusted Publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/) - Step-by-step PyPI configuration
- [PyPI Using a Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/) - Workflow configuration requirements
- [GitHub Actions OpenID Connect in PyPI](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-pypi) - OIDC configuration from GitHub side
- [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/running-variations-of-jobs-in-a-workflow) - Matrix strategy, fail-fast, job dependencies
- [GitHub Actions Triggering Workflows](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow) - Tag triggers, branch filters
- [GitHub Actions GITHUB_TOKEN Permissions](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token) - Permission scopes
- [GitHub Actions Store Artifacts](https://docs.github.com/actions/using-workflows/storing-workflow-data-as-artifacts) - Artifact upload/download
- [GitHub Actions Environment Protection](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments) - Manual approval gates

**Official Actions:**
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish) - Official PyPA publishing action
- [actions/checkout](https://github.com/actions/checkout) - Repository checkout with fetch-depth options
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release) - Release creation action
- [hatch-vcs](https://github.com/ofek/hatch-vcs) - VCS versioning plugin for Hatchling

**Official Guides:**
- [Publishing Package Distribution Releases Using GitHub Actions](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) - PyPA official guide
- [PyPA Build Documentation](https://build.pypa.io/en/latest/) - Official build frontend docs

### Secondary (MEDIUM confidence)

- [Python Packaging Guide: Trusted Publishing Tutorial](https://www.pyopensci.org/python-package-guide/tutorials/trusted-publishing.html) - Comprehensive setup walkthrough
- [Scientific Python GitHub Actions Guide](https://learn.scientific-python.org/development/guides/gha-pure/) - Pure Python wheel building patterns
- [GitHub Actions Matrix Strategy Best Practices](https://codefresh.io/learn/github-actions/github-actions-matrix/) - Matrix configuration patterns

### Tertiary (LOW confidence)

- Community blog posts on changelog extraction techniques
- Third-party GitHub Actions for version checking (not used in final recommendation, but validated approaches)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All official PyPA/GitHub actions and tools, extensive documentation
- Architecture: HIGH - Patterns from official PyPA guide and GitHub docs, widely adopted
- Pitfalls: HIGH - Documented in official GitHub issues, PyPI documentation, and community experience
- Changelog extraction: MEDIUM - Requires custom solution for MILESTONES.md format, no official tool
- Version validation: MEDIUM - Multiple approaches exist, optimal choice depends on strictness preference

**Research date:** 2026-02-10
**Valid until:** 30 days (stack is stable, GitHub Actions and PyPI evolve slowly)
