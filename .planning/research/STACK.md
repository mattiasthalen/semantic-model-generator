# Stack Research: CD Pipeline to PyPI

**Domain:** Automated CD pipeline for Python package publishing
**Researched:** 2026-02-10
**Confidence:** HIGH

## Executive Summary

The CD pipeline requires **minimal new dependencies** since the existing build system (hatchling + hatch-vcs) already handles package building and versioning from git tags. The core additions are GitHub Actions workflow components and PyPI authentication configuration—no new Python packages or build tools needed.

**Key principle:** Leverage existing infrastructure. The project already has hatchling for builds, hatch-vcs for versioning, and make check for quality gates. The CD pipeline orchestrates these, rather than duplicating them.

## Core CD Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| GitHub Actions | N/A (platform) | CI/CD orchestration | Native GitHub integration, free for public repos, built-in secrets management |
| PyPI Trusted Publishing | N/A (feature) | Secure authentication to PyPI | OIDC-based, no stored tokens, automatically rotating credentials, required by PyPI for modern workflows |
| TestPyPI | N/A (service) | Pre-production testing | Separate PyPI instance for validation before production publish |

## GitHub Actions - Official Actions

| Action | Version | Purpose | Why This Version |
|--------|---------|---------|------------------|
| actions/checkout | v6 | Clone repository | Latest major version (2026), includes node24 runtime |
| actions/setup-python | v6 | Install Python | Latest major version (2026), supports Python 3.11+, includes pip caching |
| actions/upload-artifact | v4 | Store build artifacts | Latest version with 90% faster uploads, immediate availability |
| actions/download-artifact | v4 | Retrieve build artifacts | Matches upload-artifact v4 architecture |
| pypa/gh-action-pypi-publish | v1.13.0 | Publish to PyPI | Official PyPA action, supports trusted publishing + PEP 740 attestations |

## Build Tools (Existing - No Changes)

| Tool | Current Version | Status | Notes |
|------|----------------|--------|-------|
| hatchling | (via pyproject.toml) | **Keep as-is** | PEP 517 build backend, 7.5x faster than setuptools, already configured |
| hatch-vcs | (via pyproject.toml) | **Keep as-is** | Dynamic versioning from git tags, already configured |
| pypa/build | N/A | **Do NOT add** | Unnecessary - hatchling is already a PEP 517 backend |

## Quality Gates (Existing - No Changes)

| Tool | Current Version | Status | Notes |
|------|----------------|--------|-------|
| ruff | v0.15.0 | **Keep as-is** | Linting + formatting, already in pre-commit |
| mypy | (in dev dependencies) | **Keep as-is** | Type checking configured for strict mode |
| pytest | (in dev dependencies) | **Keep as-is** | Test suite with 398 passing tests |

## Changelog Generation

| Tool | Version | Purpose | Recommendation |
|------|---------|---------|----------------|
| mikepenz/release-changelog-builder-action | v6 | Generate changelog from conventional commits | **Recommended** - Reads conventional commits from pre-commit hooks, customizable categories, no additional Python dependencies |
| git-cliff | Latest | Alternative changelog generator | **Alternative** - Rust-based, fast (120ms), requires separate installation |
| gh CLI | (pre-installed on runners) | Create GitHub releases | **Use for release creation** - Pre-installed on GitHub Actions runners |

**Recommendation:** Use `mikepenz/release-changelog-builder-action@v6` because:
- Works directly with existing conventional-pre-commit setup
- No additional dependencies
- Proven track record (v6 release, active maintenance)
- Outputs markdown suitable for GitHub releases

## Installation (CD Pipeline Only)

**No new Python packages required.** The CD pipeline uses:

```yaml
# Existing tools are invoked via make check
- run: make check

# Package building uses existing hatchling backend
- run: python -m build

# Publishing uses GitHub Action (no pip install needed)
- uses: pypa/gh-action-pypi-publish@v1.13.0
```

**No changes to pyproject.toml, Makefile, or pre-commit-config.yaml.**

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|-------------------------|
| PyPI Auth | Trusted Publishing (OIDC) | API Tokens | Never - API tokens are deprecated for security reasons |
| Build Tool | hatchling (existing) | setuptools | Never - hatchling is faster and already configured |
| Changelog | release-changelog-builder-action | git-cliff | If Rust tooling is preferred and 120ms vs 1s matters |
| Release Creation | gh CLI | softprops/action-gh-release | If custom release asset handling needed |
| Build Command | python -m build | hatch build | Either works - python -m build is more standard |

## What NOT to Add

| Avoid | Why | Consequence |
|-------|-----|-------------|
| setuptools_scm | Duplicate versioning tool | Conflicts with hatch-vcs, causes build failures |
| New linting/formatting tools | Ruff already handles this | Contradictory style rules, slower pre-commit |
| Custom build scripts | hatchling + PEP 517 is standard | Non-standard builds, harder maintenance |
| Stored API tokens | Security anti-pattern | Token leaks, manual rotation, broader permissions |
| Hatch CLI tool | Not needed for CD | Adds dependency when python -m build works |
| tox | Over-engineering for this use case | Existing make check + matrix strategy already tests multiple Python versions |
| Poetry | Different ecosystem | Conflicts with hatchling, requires migration |
| Separate version files | hatch-vcs auto-generates | Manual sync issues, source of truth confusion |

## Integration Points

### Existing Build System
```toml
# pyproject.toml (NO CHANGES)
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.hooks.vcs]
version-file = "src/semantic_model_generator/_version.py"
```

**CD pipeline uses this unchanged:**
1. `actions/checkout@v6` with `fetch-depth: 0` (hatch-vcs needs full git history)
2. `python -m build` invokes hatchling backend
3. hatch-vcs reads git tags to determine version
4. Artifacts placed in `dist/` directory

### Existing Quality Gates
```makefile
# Makefile (NO CHANGES)
check: lint typecheck test
```

**CD pipeline calls this directly:**
```yaml
- run: make check
```

### Existing Conventional Commits
```yaml
# .pre-commit-config.yaml (NO CHANGES)
- repo: https://github.com/compilerla/conventional-pre-commit
  rev: v3.4.0
  hooks:
    - id: conventional-pre-commit
      stages: [commit-msg]
```

**CD pipeline reads these:**
- Changelog generator parses commit messages following conventional commit format
- Categories: feat, fix, docs, chore, test, refactor, ci, build, perf, style

## Workflow Architecture

### Three-Job Pattern (Recommended)

**1. Build Job** (Runs on all pushes)
- Checkout with full history (`fetch-depth: 0`)
- Setup Python 3.11, 3.12 (matrix)
- Install package: `pip install -e .`
- Run quality gates: `make check`
- Build package: `python -m build`
- Upload artifacts: `actions/upload-artifact@v4`

**2. TestPyPI Job** (Runs on main branch pushes)
- Download artifacts: `actions/download-artifact@v4`
- Publish to TestPyPI using trusted publishing
- No environment protection (automatic)

**3. PyPI + Release Job** (Runs on tag pushes only)
- Download artifacts: `actions/download-artifact@v4`
- Generate changelog: `release-changelog-builder-action@v6`
- Create GitHub release: `gh release create`
- Publish to PyPI using trusted publishing
- **Requires manual approval** (GitHub environment protection)

### Separation Rationale

| Separation | Security Benefit |
|------------|------------------|
| Build job has no publish permissions | Cannot accidentally publish |
| PyPI job requires `id-token: write` | Scoped to specific job only |
| GitHub environment protection | Manual approval prevents bad releases |
| TestPyPI publishes on all main merges | Early detection of publishing issues |

## PyPI Trusted Publishing Setup

**One-time manual configuration on PyPI:**

1. **TestPyPI**: https://test.pypi.org/manage/account/publishing/
   - Repository owner: `username`
   - Repository name: `semantic-model-generator`
   - Workflow name: `cd.yml`
   - Environment name: (leave blank for TestPyPI)

2. **Production PyPI**: https://pypi.org/manage/account/publishing/
   - Repository owner: `username`
   - Repository name: `semantic-model-generator`
   - Workflow name: `cd.yml`
   - Environment name: `pypi`

3. **GitHub Environment Protection**:
   - Settings → Environments → New environment: `pypi`
   - Enable "Required reviewers"
   - Add yourself as reviewer
   - Check "Prevent self-review" (optional, for team workflows)

**Workflow configuration:**
```yaml
jobs:
  publish-pypi:
    environment: pypi  # Links to protection rules
    permissions:
      id-token: write  # CRITICAL: Required for trusted publishing
      contents: write  # For creating GitHub releases
```

## Version Compatibility

| Component | Requirement | Notes |
|-----------|-------------|-------|
| Python | 3.11+ | Already specified in pyproject.toml |
| GitHub Actions runner | ubuntu-latest | v2.327.1+ for node24 support |
| Git | 2.0+ | For `fetch-depth: 0` and tagging |
| hatch-vcs | Any recent | Requires full git history (`fetch-depth: 0`) |

## Build Command Comparison

Both work with hatchling backend:

```bash
# Option 1: Standard PEP 517 frontend (recommended for CI)
python -m build

# Option 2: Hatch-specific command (requires hatch CLI)
hatch build
```

**Recommendation:** Use `python -m build` in CI because:
- Standard across all PEP 517 backends
- No additional tool installation
- Official recommendation from packaging.python.org
- Already available with Python standard library

## Performance Notes

- **hatchling**: 2.1s builds vs setuptools' 15.8s (7.5x speedup)
- **actions/upload-artifact@v4**: 90% faster uploads vs v3
- **Trusted publishing**: No token rotation overhead
- **Changelog generation**: ~1s for typical commit range

## Security Best Practices

1. **Never store PyPI tokens in GitHub secrets** - Use trusted publishing
2. **Scope `id-token: write` to publish job only** - Not globally
3. **Require manual approval for production** - GitHub environment protection
4. **Test on TestPyPI first** - Catches authentication issues early
5. **Use exact version tags for actions** - Not branch pointers like `master`
6. **Enable PEP 740 attestations** - Enabled by default in pypa/gh-action-pypi-publish v1.11.0+

## CI/CD Anti-Patterns to Avoid

1. **Don't duplicate quality checks** - CI already runs `make check`, CD should reuse it
2. **Don't build package in multiple jobs** - Build once, publish multiple times
3. **Don't use `pip install build hatchling`** - Python -m build works without installation
4. **Don't publish on every commit** - Only on tags (production) and main (TestPyPI)
5. **Don't skip `fetch-depth: 0`** - hatch-vcs needs full history for versioning
6. **Don't store wheels in git** - Artifacts are temporary, PyPI is the registry

## Sources

### Official Documentation (HIGH Confidence)
- [Publishing Python packages with GitHub Actions (Python Packaging User Guide)](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) — Workflow structure, trusted publishing setup
- [pypi-publish GitHub Action](https://github.com/marketplace/actions/pypi-publish) — v1.13.0 features, permissions requirements
- [build · PyPI](https://pypi.org/project/build/) — Version 1.4.0 (2026-01-08)
- [GitHub Actions: Managing environments](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment) — Environment protection rules
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/using-a-publisher/) — OIDC authentication setup

### GitHub Actions Versions (HIGH Confidence)
- [actions/setup-python Releases](https://github.com/actions/setup-python/releases) — v6 with node24
- [actions/upload-artifact](https://github.com/actions/upload-artifact) — v4 performance improvements

### Best Practices (MEDIUM Confidence)
- [Publishing Python Packages to PyPI: Complete Guide](https://inventivehq.com/blog/python-pypi-publishing-guide) — 2026 best practices
- [How to Automate Releases with GitHub Actions](https://oneuptime.com/blog/post/2026-01-25-automate-releases-github-actions/view) — Release automation patterns
- [Hatchling Build Backend 2026](https://johal.in/hatchling-build-backend-pep-517-compliant-python-packaging-2026-2/) — Performance benchmarks

### Changelog Tools (MEDIUM Confidence)
- [Release Changelog Builder](https://github.com/marketplace/actions/release-changelog-builder) — v6 features
- [git-cliff](https://git-cliff.org/) — Alternative changelog generator
- [gh release create](https://cli.github.com/manual/gh_release_create) — GitHub CLI documentation

### Anti-Patterns (MEDIUM Confidence)
- [Python CI/CD Pipeline Guide](https://medium.com/hydroinformatics/the-ultimate-guide-to-python-ci-cd-mastering-github-actions-composite-actions-for-modern-python-0d7730c17b9e) — Modern Python CI/CD patterns
- [setuptools_scm vs hatch-vcs](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-versions.html) — Versioning tool comparison

---
*Stack research for: semantic-model-generator CD pipeline*
*Researched: 2026-02-10*
