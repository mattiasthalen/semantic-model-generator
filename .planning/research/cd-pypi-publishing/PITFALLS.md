# Pitfalls Research: CD for PyPI Publishing

**Domain:** Tag-based CD for PyPI Publishing (Python Package with Hatchling + Git Tag Versioning)
**Project:** semantic-model-generator v0.2.0 milestone
**Researched:** 2026-02-10
**Confidence:** HIGH

---

## Critical Pitfalls

Mistakes that cause failed releases, version burns, or security vulnerabilities.

---

### Pitfall 1: Publishing Without Quality Gates

**What goes wrong:**
Package gets published to PyPI with failing tests, broken builds, or lint errors. Once published, the version cannot be removed or replaced on PyPI, forcing a new version bump to fix issues. Users install broken package.

**Why it happens:**
Developers structure workflows where the publish job runs independently rather than depending on test/check jobs. Tag push triggers immediate publish without verification. Workflow has tests and publish as parallel jobs instead of sequential dependencies.

**Consequences:**
- Broken package on PyPI that cannot be deleted (only yanked)
- Version number burned - must bump to `.postN` or next patch version
- User complaints and lost trust
- Emergency patch release required
- Poor package reputation

**Prevention:**
- Use `needs: [test, lint, typecheck, build]` in publish job to enforce dependency chain
- Separate CI workflow (`ci.yml` for push/PR) from CD workflow (`release.yml` for tags)
- Add smoke test step that imports package and verifies basic functionality before final publish
- Build artifacts in separate job, run quality gates, then pass artifacts to publish job via GitHub Actions artifacts
- Never use parallel jobs for test and publish

**Warning signs:**
```yaml
# BAD: Publish job has no needs clause
jobs:
  test:
    runs-on: ubuntu-latest
    steps: [...]
  publish:  # Will run in parallel with test!
    runs-on: ubuntu-latest
    steps: [...]

# BAD: Tests and publish in same job
jobs:
  release:
    steps:
      - run: pytest  # Tests might be skipped if this fails
      - uses: pypa/gh-action-pypi-publish@release/v1  # Still runs!
```

**Phase to address:**
Phase 1: Workflow Design - establish job dependency structure before implementing any steps

---

### Pitfall 2: OIDC Token Over-Exposure

**What goes wrong:**
GitHub Actions workflow grants `id-token: write` permission at workflow level or to jobs with many steps. Malicious contributors could inject steps that request OIDC token and publish corrupted releases to PyPI. Token leakage through logs or environment variable exposure.

**Why it happens:**
Developers copy example workflows that use workflow-level permissions rather than job-level. Not understanding that OIDC token access should be minimized to smallest possible scope. Publishing job has many steps (checkout, setup-python, install-deps, run-tests, build, publish) all with access to OIDC token.

**Consequences:**
- Security vulnerability allowing unauthorized PyPI publishes
- Supply chain attack risk
- Malicious code published to PyPI under legitimate package name
- Cannot revoke published versions
- Package reputation destroyed
- PyPI trusted publisher relationship may be revoked

**Prevention:**
- Set `id-token: write` at job level (publish job only), NEVER workflow level
- Limit publish job to exactly 2 steps: (1) download artifacts, (2) run `pypa/gh-action-pypi-publish`
- Use separate build job to keep number of steps with OIDC token access minimal
- Use dedicated GitHub environment (e.g., "pypi-publish") with protection rules
- Enable required reviewers for environment if publishing sensitive packages
- Use tag protection rules to limit who can create release tags

**Warning signs:**
```yaml
# BAD: Workflow-level permissions
permissions:
  id-token: write  # All jobs get token access!

# BAD: Many steps in job with id-token
jobs:
  publish:
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install build
      - run: pytest  # Too many steps with token access
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

**Good pattern:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
      - run: pip install build
      - run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: [build, test]
    runs-on: ubuntu-latest
    environment: pypi-publish
    permissions:
      id-token: write  # Job-level only
      contents: read
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
```

**Phase to address:**
Phase 2: Security Configuration - before writing any workflow code, establish security boundaries

---

### Pitfall 3: Version Desynchronization (Git Tag vs Package Metadata)

**What goes wrong:**
Git tag says `v1.2.3` but published package has version `1.2.2` or `1.2.3.dev0+abc123`. Users can't correlate PyPI releases with git tags. Debugging becomes nightmare. Re-running failed workflow with stale checkout publishes wrong version to PyPI.

**Why it happens:**
With hatch-vcs, version is derived from git tags at build time. If git history isn't fetched (`fetch-depth: 0` missing), hatch-vcs calculates wrong version from shallow clone. If workflow checks out before tag creation propagates, build sees old version. Workflow triggered by tag push but checkout happens before tag is visible.

**Consequences:**
- PyPI package version doesn't match git tag
- Users report bugs against wrong versions
- Cannot reproduce builds from git tags
- Version confusion in issue tracker
- Wasted debugging time
- Trust in versioning system eroded

**Prevention:**
- Always use `fetch-depth: 0` in checkout action (hatch-vcs needs full history)
- For tag-triggered workflows, verify tag is visible: `git describe --tags` before build
- Validate built package version matches triggering tag before publish:
  ```bash
  BUILT_VERSION=$(python -c "import pkginfo; print(pkginfo.Wheel('dist/*.whl').version)")
  TAG_VERSION=${GITHUB_REF_NAME#v}  # Strip 'v' prefix
  if [ "$BUILT_VERSION" != "$TAG_VERSION" ]; then
    echo "Version mismatch: tag=$TAG_VERSION but built=$BUILT_VERSION"
    exit 1
  fi
  ```
- Use hatch-vcs `version-file` to generate `_version.py` (already configured in project at lines 21-22 of pyproject.toml)
- Test in CI: verify version derivation works correctly

**Warning signs:**
```yaml
# BAD: Shallow clone
- uses: actions/checkout@v4
  # Missing fetch-depth: 0

# BAD: No version validation
- name: Build
  run: python -m build
- name: Publish
  uses: pypa/gh-action-pypi-publish@release/v1
  # No check that version matches tag
```

**Phase to address:**
Phase 3: Build Configuration - during build step implementation, add version validation immediately after build

---

### Pitfall 4: Tag Format Mismatch (PEP 440 Non-Compliance)

**What goes wrong:**
Developer creates tag `v1.0.0-beta1` (SemVer style with dash). hatch-vcs derives `1.0.0-beta1`. PyPI rejects upload: "400 Bad Request: Invalid version, must be PEP 440 compliant." Version is burned, can't reuse tag name for corrected version.

**Why it happens:**
Git allows any tag format but PyPI requires PEP 440. SemVer uses dashes (`1.0.0-beta1`), PEP 440 doesn't (`1.0.0b1`). Developers unfamiliar with PEP 440 create invalid tags. twine normalizes some cases (`1.0.0-dev1` → `1.0.0dev1`) but not all (`1.0.0-beta.1` → invalid).

**Consequences:**
- PyPI upload fails after all tests pass
- Tag name burned - cannot reuse
- Must create new tag with corrected format
- Confusion about which version was actually released
- Wasted CI/CD time on failed publish

**Prevention:**
- Document tag format in CONTRIBUTING.md and README:
  ```
  Release tags: vMAJOR.MINOR.PATCH[{a|b|rc}N][.postN][.devN]
  Examples:
    v1.0.0      - Final release
    v1.0.0b1    - Beta 1 (not v1.0.0-beta1)
    v1.0.0rc2   - Release candidate 2
    v1.0.0.post1 - Post-release patch
  ```
- Add tag protection rules requiring maintainer approval for `v*` tags
- Implement pre-publish validation:
  ```python
  from packaging.version import Version
  try:
      Version(tag_version)
  except Exception as e:
      print(f"Invalid PEP 440 version: {tag_version}")
      exit(1)
  ```
- Configure hatch-vcs `tag-pattern` if using non-standard prefix
- Test tag format in TestPyPI workflow before production publish

**Warning signs:**
- Tags like `v1.0.0-beta1`, `v1.0.0-rc.1`, `release-1.0.0`, `v1.0.0-alpha`
- No documentation of tagging convention in repository
- No automated tag format validation in workflow
- PyPI publish fails with "Invalid version" error

**Phase to address:**
Phase 1: Workflow Design - define tag convention and validation before implementing workflows

---

### Pitfall 5: Duplicate Version Publishing Attempt

**What goes wrong:**
Workflow fails with "400 Client Error: File already exists" because version was already published to PyPI. Happens when re-running failed workflow, publishing from multiple branches simultaneously, or manual + automated publish race condition.

**Why it happens:**
PyPI blocks duplicate versions to ensure reproducible builds. Developer tags, workflow fails mid-publish (TestPyPI succeeded but PyPI network error), developer re-runs workflow, PyPI says version already exists.

**Consequences:**
- Workflow failure appears as error but may be expected
- Confusion about whether version was actually published
- CI/CD shows red status even though publish partially succeeded
- Requires manual verification of PyPI to determine state

**Prevention:**
- Use `skip-existing: true` parameter in pypa/gh-action-pypi-publish (fails gracefully if version exists)
- Check if version exists on PyPI before attempting publish:
  ```bash
  if pip index versions semantic-model-generator | grep -q "$VERSION"; then
    echo "Version $VERSION already exists on PyPI"
    exit 0  # Success, not error
  fi
  ```
- Never delete and re-create git tags with same name
- If publish partially fails, bump to `.postN` version instead of retrying with same version
- Use TestPyPI for validation, only promote to PyPI on full success
- Document recovery procedure: if TestPyPI succeeds but PyPI fails, create `.post1` version

**Warning signs:**
- Workflow re-runs after partial publish failure
- Multiple tags for same version (deleted and recreated)
- No duplicate version handling in workflow
- "File already exists" errors in workflow logs

**Phase to address:**
Phase 4: Publish Implementation - add duplicate handling when writing publish job

---

### Pitfall 6: Missing Git in Production Build Environment

**What goes wrong:**
Build succeeds in CI (GitHub Actions) but fails when users try to build from source distribution. Error: "git: command not found" or "No tags found, version defaulting to 0.0.0." Users report package installs with version `0.0.0`.

**Why it happens:**
hatch-vcs requires git at build time to derive version from tags. GitHub Actions runners have git pre-installed, masking the problem. Users installing from source distribution (`pip install .` from git clone) may not have git. Production Docker builds often don't include git to minimize image size.

**Consequences:**
- Users cannot install from source
- Version shows as `0.0.0` when building without git
- Confusion about installation methods
- Bug reports from users building from source
- Broken editable installs in some environments

**Prevention:**
- Generate `_version.py` file during build (already configured: `tool.hatch.build.hooks.vcs`)
- Include `_version.py` in source distributions (hatch does this automatically)
- Test build in minimal container without git:
  ```bash
  docker run --rm python:3.11-slim bash -c "
    pip install semantic-model-generator-1.2.3.tar.gz
    python -c 'import semantic_model_generator; print(semantic_model_generator.__version__)'
  "
  ```
- Document in README that building from git clone requires git + hatch-vcs:
  ```markdown
  ## Development Installation

  Requires git (for version detection):
  ```bash
  git clone https://github.com/user/semantic-model-generator.git
  cd semantic-model-generator
  pip install -e .
  ```
  ```
- For editable installs in dev, require git in dev dependencies (optional-dependencies section)

**Warning signs:**
- Users report "version 0.0.0" when installing from source
- Build works in CI but not in Docker containers
- `_version.py` not present in built distributions
- ImportError or version detection failures

**Phase to address:**
Phase 3: Build Configuration - verify version file generation and test in minimal environment

---

### Pitfall 7: Changelog Desynchronization

**What goes wrong:**
GitHub Release created with automated changelog from commit messages, but changelog is misleading or missing context. Major breaking changes not highlighted. Migration steps absent. Users surprised by API changes. Changelog is raw commit dump with no narrative.

**Why it happens:**
Fully automated changelog generation from conventional commits works for feature lists but misses human context. Commit messages optimized for developers (internal details, PR numbers), not users (feature benefits, migration steps). No review process before release publication. Tools like `auto-changelog` generate from commits but don't add editorial context.

**Consequences:**
- Users don't know what changed or why to upgrade
- Breaking changes buried in commit list
- No migration guide for API changes
- Users surprised by breaking changes
- Support burden increases (users ask what changed)
- Poor upgrade adoption

**Prevention:**
- Use automated changelog as draft, not final
- Generate changelog in separate step before publish, save as artifact
- Require manual review/edit of changelog before GitHub Release creation
- Include custom sections: "Breaking Changes," "Migration Guide," "Known Issues," "New Features," "Bug Fixes"
- Use tools like `git-changelog` or `auto-changelog` with Jinja2 templates for structure
- Link to detailed migration docs for major versions
- Conventional commit types for automation: `feat:`, `fix:`, `BREAKING CHANGE:`
- Create draft GitHub Release, review/edit, then publish manually or with approval

**Warning signs:**
- GitHub Release created automatically with no review step
- Changelog is raw commit message dump with no sections
- No breaking change warnings despite API changes
- Changelog doesn't match what users need to know (internal details vs user impact)
- Users ask "what changed?" in issues

**Phase to address:**
Phase 5: Changelog Generation - implement draft-review-publish workflow, not direct automation

---

### Pitfall 8: Release Atomicity Failure

**What goes wrong:**
Publish job succeeds for PyPI but fails for GitHub Release creation. Or vice versa. Or TestPyPI succeeds but PyPI fails due to network issue. Package exists in one location but not others. Users confused about where to get package or what the latest version is.

**Why it happens:**
Each publish step (TestPyPI, PyPI, GitHub Release) can fail independently due to network issues, API rate limits, token expiration. Workflow doesn't treat release as atomic unit. No rollback mechanism. Steps run in parallel or without verification between them.

**Consequences:**
- Inconsistent state: package on PyPI but no GitHub Release
- Users find package on PyPI but no release notes
- Or GitHub Release exists but PyPI publish failed
- Confusion about official release status
- Must manually fix inconsistent state
- Support burden from confused users

**Prevention:**
- Order operations sequentially: TestPyPI → verify → PyPI → verify → GitHub Release
- Use job dependencies: `needs: [publish-testpypi]` before `publish-pypi`
- Add verification steps between publishes: check package is installable from each index
- Make GitHub Release the final step (most recoverable if it fails - can be created manually)
- Document manual recovery procedures in runbook for each failure scenario
- Use `continue-on-error: false` (default) to stop on first failure
- Consider draft releases: publish to PyPI, create draft GitHub release, manual promotion after verification

**Warning signs:**
```yaml
# BAD: All publish steps in single job with no verification
- name: Publish to TestPyPI
  uses: pypa/gh-action-pypi-publish@release/v1
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
- name: Create GitHub Release
  uses: actions/create-release@v1
# No verification between steps!

# BAD: Parallel publish jobs
jobs:
  publish-testpypi: [...]
  publish-pypi: [...]  # No needs: clause, runs in parallel!
```

**Phase to address:**
Phase 6: Release Orchestration - design release as sequential gated process with verification between each step

---

### Pitfall 9: Credential Misconfiguration (Trusted Publishing)

**What goes wrong:**
Workflow runs but publish fails with error: "PyPI OIDC token validation failed" or "Trusted publisher authentication failed." Happens when trusted publisher configuration on PyPI doesn't match workflow environment, owner, repo, or workflow filename. Silent failure if testing only in forked repos (trusted publishing won't work in forks).

**Why it happens:**
Trusted publisher configuration on PyPI is exact-match: owner, repo, workflow filename, environment name all must match precisely (case-sensitive, character-perfect). Typos in PyPI configuration. Workflow renamed but PyPI not updated. Environment name mismatch (workflow says "pypi" but PyPI configured for "pypi-publish").

**Consequences:**
- Publish fails with cryptic OIDC error
- Must manually reconfigure on PyPI website
- Workflow fails after all tests pass
- Debugging requires understanding OIDC token claims
- Cannot test in forks (trusted publishing is repo-specific)

**Prevention:**
- Configure trusted publisher on PyPI with exact values before writing workflow:
  - Owner: `username` or `org-name`
  - Repository: `repo-name`
  - Workflow name: `.github/workflows/release.yml` (exact filename)
  - Environment: `pypi-publish` (if used in workflow)
- Use specific environment name in workflow and match exactly in PyPI config
- Document trusted publisher configuration in README or CONTRIBUTING.md:
  ```markdown
  ## PyPI Trusted Publisher Configuration

  This project uses PyPI Trusted Publishing (OIDC). Configuration:
  - Owner: myorg
  - Repo: semantic-model-generator
  - Workflow: .github/workflows/release.yml
  - Environment: pypi-publish
  ```
- Test in target repository, not fork (trusted publishing won't work in forks)
- Add validation step: attempt to request OIDC token before publish to fail fast
- Keep workflow filename stable, update PyPI config if renaming

**Warning signs:**
```yaml
# Workflow file: .github/workflows/publish-release.yml
environment: pypi

# PyPI trusted publisher config:
# Workflow name: publish.yml  # WRONG - doesn't match actual filename
# Environment: release        # WRONG - doesn't match workflow environment
```

**Phase to address:**
Phase 2: Security Configuration - configure trusted publisher on PyPI and document values before writing workflows

---

### Pitfall 10: Test Pollution (TestPyPI Dependency Issues)

**What goes wrong:**
Package successfully installs from TestPyPI but fails when published to PyPI. Dependencies pulled from wrong index during testing. Users install from PyPI but get broken dependency mix. Tests pass with TestPyPI but fail with real PyPI installation.

**Why it happens:**
TestPyPI is separate index with different packages and versions. Installing from TestPyPI with dependencies tries to resolve from TestPyPI first, may find wrong versions or missing packages. Some dependencies exist only on PyPI (e.g., `mssql-python`, `azure-identity`), causing installation failure from TestPyPI. No validation that PyPI install actually works.

**Consequences:**
- False confidence from TestPyPI success
- PyPI publish succeeds but users cannot install due to missing deps
- Dependencies pulled from TestPyPI are different versions than PyPI
- Test results not representative of production installs
- Users report "package not found" for dependencies

**Prevention:**
- Test installation from TestPyPI with `--no-deps` flag:
  ```bash
  pip install --index-url https://test.pypi.org/simple/ --no-deps semantic-model-generator
  ```
- Separately install dependencies from PyPI, package from TestPyPI:
  ```bash
  # Install dependencies from PyPI
  pip install mssql-python azure-identity tenacity requests
  # Install package from TestPyPI (no deps)
  pip install --index-url https://test.pypi.org/simple/ --no-deps semantic-model-generator
  ```
- Add explicit TestPyPI validation job: install (no-deps), import, run basic smoke test
- Add PyPI validation job (after publish): install from PyPI in fresh environment, verify functionality
- Use matrix testing: test against both TestPyPI and PyPI indexes
- Document in workflow comments that TestPyPI is for package validation only, not dependency testing

**Warning signs:**
```yaml
# BAD: No explicit index specification
- run: pip install semantic-model-generator
  # Which index? TestPyPI or PyPI?

# BAD: Installing deps from TestPyPI
- run: pip install --index-url https://test.pypi.org/simple/ semantic-model-generator
  # Will try to install mssql-python, azure-identity from TestPyPI - will fail!
```

**Good pattern:**
```yaml
- name: Test installation from TestPyPI
  run: |
    pip install mssql-python azure-identity tenacity requests
    pip install --index-url https://test.pypi.org/simple/ --no-deps semantic-model-generator
    python -c "import semantic_model_generator; print(semantic_model_generator.__version__)"
```

**Phase to address:**
Phase 4: Publish Implementation - add proper validation steps for each publish target

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip TestPyPI publish | Faster releases, one less step to maintain | No validation before production, version burn on failures, cannot test install process | Never - always use TestPyPI for safety |
| API tokens instead of OIDC | Simpler to understand initially, works in forks | Security risk (long-lived secrets), token rotation overhead, secret management burden, broader access scope | Development/testing only, never production releases |
| Manual version bumping in `pyproject.toml` | Full control over version numbers, no git dependency | Desync with git tags, human error in version strings, merge conflicts on version file | Never with hatch-vcs - defeats entire purpose of tag-based versioning |
| Single-job workflow (test+build+publish together) | Fewer moving parts, simpler YAML structure | Can't rerun publish without rerunning tests, OIDC token over-exposure to all steps, harder to debug failures | Never - always separate concerns for security and maintainability |
| Skip changelog generation | Faster releases, less work | Users don't know what changed, poor documentation, lower adoption of new versions, increased support burden | Small internal packages only, never public packages |
| Workflow-level permissions | Shorter YAML, less configuration | Security risk with broad access scope, all jobs get excessive permissions | Development/testing workflows only, never publish workflows |
| Skip version validation | Fewer steps, simpler workflow | Publish wrong versions to PyPI, debugging nightmares, version confusion in issue tracker | Never - validation is cheap insurance |

---

## Integration Gotchas

Common mistakes when connecting external services in CD pipeline.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| **PyPI Trusted Publishing** | Configuring on PyPI website with wrong workflow filename or environment name | Use exact match (case-sensitive): owner/repo/workflow/environment must be character-perfect, document configuration values |
| **hatch-vcs Version Detection** | Shallow git clone (`fetch-depth` not set to 0) | Always use `fetch-depth: 0` in checkout action to get full git history for version derivation |
| **GitHub Actions Artifacts** | Building and publishing in same job with OIDC token access | Separate jobs: build → test → publish, pass wheel/sdist artifacts between jobs using actions/upload-artifact and actions/download-artifact |
| **TestPyPI Index** | Installing package with dependencies from TestPyPI | Use `--no-deps` when testing TestPyPI, install dependencies separately from PyPI to avoid missing packages |
| **PEP 440 Versions** | Creating git tags with SemVer format (`v1.0.0-beta1` with dash) | Use PEP 440 format (`v1.0.0b1`, `v1.0.0rc1` without dash) or configure tag pattern normalization in hatch-vcs |
| **GitHub Releases** | Creating GitHub Release before PyPI publish succeeds | Publish to TestPyPI first, verify, then PyPI, verify installation, then create GitHub Release as final step |
| **OIDC Tokens** | Setting `id-token: write` at workflow level giving all jobs access | Set `id-token: write` at job level, only for publish job, with minimal steps (download artifact + publish only) |
| **Workflow Triggers** | Using `push: tags: v*` with no tag protection rules | Use tag-based trigger with tag protection rules requiring maintainer approval, or use `release: types: [published]` trigger |
| **Version Validation** | Assuming built version matches tag without checking | Extract version from built wheel metadata, compare to `$GITHUB_REF_NAME`, fail if mismatch detected |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Building all platform wheels in single job | Job timeout on large projects with many platforms (Windows/Linux/macOS) | Use matrix strategy to build wheels in parallel across runners for each platform | Projects with >3 platform-specific binary extensions or complex build requirements |
| Running full test suite in publish workflow | Slow releases (10+ minutes), double-testing (already tested in CI on every commit) | Run smoke tests only in release workflow (import, basic function call), rely on comprehensive CI testing | Test suite >5 minutes runtime |
| Installing all dev dependencies in publish job | Slow workflow startup, unnecessary package installations | Minimal environment: only build tools (build, twine if needed), not dev/test dependencies (pytest, mypy, ruff) | Development dependencies >20 packages or >100MB |
| Re-cloning large repository in each job | Slow workflow, wastes bandwidth, GitHub API rate limits | Upload checkout as artifact in first job, download in dependent jobs using actions/cache or actions/download-artifact | Repositories >100 MB or with large git history |
| No caching of Python dependencies | Every workflow run reinstalls dependencies from PyPI | Use actions/cache with pip cache or actions/setup-python built-in caching | Dependencies >50 packages or frequent workflow runs (>10/day) |

---

## Security Mistakes

Domain-specific security issues beyond general security best practices.

| Mistake | Risk | Prevention |
|---------|------|------------|
| **API token in repository secret** | Token leakage through logs or compromised repo, rotation complexity, tokens grant broad PyPI access | Use OIDC trusted publishing (tokenless authentication), no long-lived secrets required |
| **No environment protection rules** | Anyone with write access can trigger publish by pushing tags | Require reviewers for publish environment, use tag protection rules limiting tag creation to maintainers only |
| **Verbose logging in publish job** | Token/credential exposure in public workflow logs | Minimal logging, never log auth details, pypa/gh-action-pypi-publish handles this automatically for OIDC |
| **Forked PR can trigger publish workflow** | Malicious publish from untrusted contributor's fork | Tag-based trigger only (not pull_request trigger), tags can only be created by repo maintainers, not fork contributors |
| **No artifact signing/attestations** | Package tampering risk, supply chain attacks, cannot verify authenticity | Use PEP 740 attestations (automatic in gh-action-pypi-publish v1.11.0+), no manual signing steps needed |
| **Broad workflow permissions** | Excessive token capabilities allowing unintended actions | Minimal permissions per job, explicit permission grants (id-token: write, contents: read), never use write-all |
| **Same workflow for dev and prod** | Accidental production publish from test branch or PR | Separate workflows: ci.yml (testing on push/PR), release.yml (publishing on tags only), different trigger conditions |
| **No tag protection rules** | Anyone can create release tags triggering production publish | Configure tag protection rules in GitHub settings: require maintainer approval for `v*` tags |

---

## UX Pitfalls

User experience mistakes in release process.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| **No release notes** | Users don't know what changed, can't decide whether to upgrade, no changelog in GitHub | Auto-generate draft from commits, manually review/enhance before publishing, include breaking changes and migration steps |
| **Breaking changes not highlighted** | Users upgrade without warning, code breaks, frustration and bug reports | Dedicated "Breaking Changes" section at top of release notes, use BREAKING CHANGE commits, bump major version |
| **No migration guide for breaking changes** | Users stuck on old versions unable to upgrade safely | Include migration steps in release notes for each breaking change, link to detailed migration docs for major versions |
| **Version skipping confusion** | Published v1.2.3 after failed v1.2.2 attempt, users wonder where v1.2.2 is | Explain version skips in release notes: "Note: v1.2.2 was not released due to [reason], this version includes those changes" |
| **Silent prereleases on PyPI** | Users install alpha/beta by accident via pip install, report bugs in unstable code | Clear prerelease marking in version (1.0.0a1, 1.0.0b2), use --pre flag required for pip install, document stability in README |
| **Yanked versions not explained** | Users confused why specific version disappeared from PyPI, uncertainty about what was wrong | Add yank reason to PyPI project page, create GitHub issue explaining problem, link to fixed version in issue |
| **No installation verification instructions** | Users unsure if installation succeeded or how to verify version | Include verification steps in README: `pip install semantic-model-generator && python -c "import semantic_model_generator; print(semantic_model_generator.__version__)"` |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Workflow triggers:** Configured for tag push but no tag protection rules — verify only maintainers can create `v*` tags
- [ ] **OIDC publishing:** Workflow has `id-token: write` but PyPI trusted publisher not configured — verify PyPI configuration matches workflow exactly (owner/repo/workflow/environment)
- [ ] **Version validation:** Builds package but doesn't verify version matches tag — verify built wheel version matches `$GITHUB_REF_NAME`
- [ ] **TestPyPI testing:** Publishes to TestPyPI but doesn't verify installation — verify `pip install --index-url https://test.pypi.org/simple/ --no-deps <package>` succeeds and imports work
- [ ] **PyPI verification:** Publishes to PyPI but doesn't verify availability — verify `pip install <package>` succeeds from fresh environment and correct version installed
- [ ] **Quality gates:** Has test job but publish doesn't depend on it — verify `needs: [test, lint, typecheck]` in publish job
- [ ] **Artifact isolation:** Builds in publish job instead of separate build job — verify build job uploads artifact, publish job only downloads and publishes
- [ ] **Changelog automation:** GitHub Release created but no changelog or only raw commits — verify release notes generated, reviewed, and enhanced with user-facing information
- [ ] **Rollback plan:** Workflow has publish steps but no recovery documentation — verify runbook exists for partial failures (TestPyPI success, PyPI failure, etc.)
- [ ] **Error notifications:** Workflow can fail silently with no alerts — verify failure notifications configured (GitHub notifications, email, Slack, etc.)
- [ ] **Tag format validation:** Accepts any tag format — verify tags validated against PEP 440 before build
- [ ] **Duplicate version handling:** No handling for re-runs — verify `skip-existing: true` configured or version existence checked
- [ ] **Environment protection:** Publish job has no environment — verify dedicated environment (pypi-publish) with protection rules if needed

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| **Published wrong version to PyPI** | MEDIUM | Cannot delete from PyPI. Yank broken version on PyPI (prevents new installs). Publish patch version with fixes using `.postN` suffix (e.g., `1.2.3.post1`). Update GitHub Release notes explaining issue. Notify users via issue or announcement. |
| **Published without tests passing** | MEDIUM | Yank version on PyPI immediately (existing installs unaffected but new installs prevented). Fix issues in code. Publish patch version (e.g., `1.2.4`). Document in release notes which version to skip. Create GitHub issue explaining what went wrong. |
| **Version desync (tag vs package)** | HIGH | Cannot reuse version on PyPI. Delete incorrect tag from GitHub. Create new tag with bumped version (e.g., `v1.2.4` instead of broken `v1.2.3`). Publish corrected package with new version. Delete broken release from GitHub Releases (can delete from GitHub but not PyPI). Update documentation. |
| **OIDC configuration mismatch** | LOW | Update PyPI trusted publisher configuration to match workflow (owner/repo/workflow/environment). Or update workflow to match PyPI configuration. Re-run workflow. No version burn if workflow fails before publish. Document correct configuration for future. |
| **Partial publish (TestPyPI yes, PyPI no)** | LOW | Fix issue (usually network error or transient PyPI issue). Re-run workflow. TestPyPI publish will fail with "already exists" (expected, use `skip-existing: true`). PyPI publish should succeed on retry. Verify package installable from PyPI. |
| **Broken changelog in GitHub Release** | LOW | Edit GitHub Release (can be edited after creation). Update release notes with proper formatting, add migration guide, clarify breaking changes. GitHub Releases are editable anytime. Re-publish edited release notes. |
| **Missing dependencies from TestPyPI** | LOW | No PyPI impact if TestPyPI-only issue. Verify dependencies exist on PyPI. Test installation with `--no-deps` next time. Document in workflow that TestPyPI testing is package-only, not dependency testing. |
| **Duplicate version attempt** | LOW | Use `skip-existing: true` in pypa/gh-action-pypi-publish to handle gracefully. If truly need new publish, bump to `.postN` version. Don't delete and recreate tags with same name. Verify publish state on PyPI before retrying. |
| **Tag format wrong (PEP 440 non-compliant)** | HIGH | Cannot reuse version/tag if published to PyPI. Delete incorrect tag from GitHub. Create new tag with correct PEP 440 format (e.g., `v1.0.0b1` not `v1.0.0-beta1`). Document tagging convention in CONTRIBUTING.md. Add tag format validation to workflow to prevent recurrence. Version burned if upload to PyPI succeeded. |
| **Security token exposed in logs** | HIGH | If using OIDC (recommended): tokens are short-lived (15 minutes), limited risk, regenerate trusted publisher configuration if concerned. If using API token: rotate token immediately on PyPI. Audit all releases published with exposed token for tampering. Consider yanking releases if compromised. Report to PyPI security team if malicious use suspected. |
| **GitHub Release exists but PyPI publish failed** | MEDIUM | Fix PyPI publish issue (credentials, network, PEP 440 compliance). Re-run workflow or manually publish to PyPI with `twine upload dist/*`. Verify version installable from PyPI. Update GitHub Release notes if needed. In future, make GitHub Release the final step after PyPI. |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification Method |
|---------|------------------|---------------------|
| Publishing without quality gates | Phase 1: Workflow Design | Test job must complete successfully before publish job starts, verify `needs:` clause |
| OIDC token over-exposure | Phase 2: Security Configuration | Publish job has exactly 2 steps and job-level `id-token: write`, not workflow-level |
| Version desynchronization | Phase 3: Build Configuration | Built wheel version extracted and compared to `$GITHUB_REF_NAME`, fails if mismatch |
| Tag format mismatch | Phase 1: Workflow Design | Tag format validation script passes PEP 440 compliance check using `packaging.version.Version` |
| Duplicate version publishing | Phase 4: Publish Implementation | `skip-existing: true` configured in pypa/gh-action-pypi-publish, duplicate handling tested |
| Missing git in production | Phase 3: Build Configuration | `_version.py` present in wheel and sdist, package installable in container without git |
| Changelog desynchronization | Phase 5: Changelog Generation | Draft GitHub Release created with changelog, manual review step before publish |
| Release atomicity failure | Phase 6: Release Orchestration | Jobs run sequentially with `needs:` dependencies, verification step between each publish |
| Credential misconfiguration | Phase 2: Security Configuration | Trusted publisher config on PyPI matches workflow exactly, documented values verified |
| Test pollution from TestPyPI | Phase 4: Publish Implementation | TestPyPI install uses `--no-deps`, PyPI install verified in separate fresh environment |

---

## Sources

### Official Python Packaging Documentation (HIGH Confidence)
- [Publishing package distribution releases using GitHub Actions CI/CD workflows - Python Packaging User Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [PEP 440 – Version Identification and Dependency Specification](https://peps.python.org/pep-0440/)
- [Packaging Python Projects — Python Packaging User Guide](https://packaging.python.org/tutorials/packaging-projects/)

### PyPI Official Resources (HIGH Confidence)
- [Security Model and Considerations - PyPI Docs](https://docs.pypi.org/trusted-publishers/security-model/)
- [Publishing to PyPI with a Trusted Publisher - PyPI Docs](https://docs.pypi.org/trusted-publishers/)
- [Introducing 'Trusted Publishers' - The Python Package Index Blog](https://blog.pypi.org/posts/2023-04-20-introducing-trusted-publishers/)

### GitHub Official Documentation (HIGH Confidence)
- [Configuring OpenID Connect in PyPI - GitHub Docs](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-pypi)
- [OpenID Connect - GitHub Docs](https://docs.github.com/en/actions/concepts/security/openid-connect)

### PyPA Official Tools & Actions (HIGH Confidence)
- [pypa/gh-action-pypi-publish - The blessed GitHub Action](https://github.com/pypa/gh-action-pypi-publish)
- [How to cut tagged releases from the default repo branch - Discussion #42](https://github.com/pypa/gh-action-pypi-publish/discussions/42)

### Hatch & Version Management (HIGH Confidence)
- [hatch-vcs - Hatch plugin for versioning with your preferred VCS](https://github.com/ofek/hatch-vcs)
- [hatch-vcs-footgun-example - Version sync pitfalls with editable installs](https://github.com/maresb/hatch-vcs-footgun-example)

### Security Best Practices (MEDIUM-HIGH Confidence)
- [7 GitHub Actions Security Best Practices - StepSecurity](https://www.stepsecurity.io/blog/github-actions-security-best-practices)
- [Top 10 GitHub Actions Security Pitfalls - Arctiq](https://arctiq.com/blog/top-10-github-actions-security-pitfalls-the-ultimate-guide-to-bulletproof-workflows)
- [Pypi Trusted Publisher Management and pitfalls](https://dreamnetworking.nl/blog/2025/01/07/pypi-trusted-publisher-management-and-pitfalls/)

### PyPI Publishing Guides (MEDIUM Confidence)
- [Publishing Python Packages to PyPI: Complete Guide with Trusted Publishing](https://inventivehq.com/blog/python-pypi-publishing-guide)
- [Build Python Packages: Development to PyPI Guide](https://www.glukhov.org/post/2025/11/building-python-packages-from-development-to-pypi/)
- [How to Secure Your Python Packages When Publishing to PyPI - pyOpenSci](https://www.pyopensci.org/blog/python-packaging-security-publish-pypi.html)

### Release Management (MEDIUM Confidence)
- [What to do when you botch a release on PyPI - Brett Cannon](https://snarky.ca/what-to-do-when-you-botch-a-release-on-pypi/)
- [Release workflow: Atomic PyPI pushing? - psf/black Issue #4839](https://github.com/psf/black/issues/4839)
- [How to Automate Releases with GitHub Actions](https://oneuptime.com/blog/post/2026-01-25-automate-releases-github-actions/view)

### Version Management & Git Tags (MEDIUM Confidence)
- [How to single-source a package's version - Python.org Discussion](https://discuss.python.org/t/how-to-single-source-a-packages-version-when-publishing-to-pypi-using-github-action/50982)
- [vercheck - Check if version is PEP-440 compliant](https://github.com/cleder/vercheck)

### Changelog Generation Tools (MEDIUM Confidence)
- [auto-changelog - PyPI](https://pypi.org/project/auto-changelog/)
- [git-changelog - PyPI](https://pypi.org/project/git-changelog/)
- [conventional-changelog - GitHub](https://github.com/conventional-changelog/conventional-changelog)

### Duplicate Version & PyPI Errors (MEDIUM Confidence)
- [How to Force Overwrite a PyPI Package - CodeGenes](https://www.codegenes.net/blog/how-to-overwrite-pypi-package-when-doing-upload-from-command-line/)
- [Versioning - Python Packaging User Guide](https://packaging.python.org/en/latest/discussions/versioning/)

---

*Pitfalls research for: Tag-based CD for PyPI Publishing with Hatchling + Git Tag Versioning*
*Researched: 2026-02-10*
*Project: semantic-model-generator v0.2.0 milestone*
*Context: Adding CD automation to existing Python package with 398 passing tests and complete build system*
