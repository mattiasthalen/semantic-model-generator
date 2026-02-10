# Feature Research

**Domain:** Tag-based CD pipeline for PyPI package publishing
**Researched:** 2026-02-10
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = pipeline feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Tag-triggered workflow | Industry standard for Python releases | LOW | `on: push: tags: 'v*'` pattern is universal across PyPI packages |
| Full test suite execution | Prevent broken releases | LOW | Already have `make check` (lint, typecheck, test) - just run it |
| Build both wheel and sdist | PyPI best practice requirement | LOW | `python -m build` creates both by default with hatchling |
| Trusted Publisher auth | Modern security standard (no API tokens) | LOW | PyPI OIDC with `id-token: write` permission - requires PyPI config |
| Publish to PyPI | Core purpose of CD pipeline | LOW | `pypa/gh-action-pypi-publish@release/v1` with trusted publishing |
| GitHub release creation | Users expect release notes on GitHub | MEDIUM | Can use `gh release create` or GitHub's auto-generated notes |
| Build artifact verification | Ensure package installs correctly | MEDIUM | Test install from built wheel before publishing to PyPI |
| Workflow failure notifications | Know when releases fail | LOW | GitHub Actions sends email on workflow failure by default |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Automated changelog in release | Users see what changed without reading commits | MEDIUM | User requires auto-generated changelog from git history + MILESTONES.md link |
| Multi-version testing matrix | Confidence across Python versions | LOW | Already testing 3.11, 3.12 in CI - reuse for CD validation |
| Package attestations | Supply chain security (provenance) | LOW | Enabled by default with trusted publishing via `pypa/gh-action-pypi-publish` |
| PyPI link in release notes | Direct navigation to published package | LOW | Auto-generate link to `https://pypi.org/project/{name}/{version}/` |
| Manual approval gate | Prevent accidental production releases | MEDIUM | GitHub environment protection with required reviewers |
| TestPyPI preview | Test package before production publish | MEDIUM | Separate workflow or job that publishes to test.pypi.org first |
| Version consistency checks | Ensure tag matches package version | LOW | Verify git tag version equals hatch-vcs generated version |
| Rollback documentation | Clear recovery process for bad releases | LOW | Document PyPI yanking process (can't delete, only yank) |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Automatic version bumping | "Automate everything" impulse | Loses control of versioning strategy, conflicts with tag-based approach where human decides version | Use git tags as source of truth - human creates tag, CD publishes it |
| Publishing on every commit | Fast iteration mindset | Pollutes PyPI with noise, no semantic meaning to versions, breaks user trust | Only publish on tagged releases with semantic versions |
| Bypassing quality gates for hotfixes | "This one is urgent" pressure | Creates precedent for skipping tests, leads to broken releases in production | Run full test suite always - if tests are too slow, optimize tests not gates |
| Building on multiple OS platforms | "Support all platforms" completeness | Pure Python package has no OS-specific code - wastes CI time | Build once on Linux - wheels are platform-independent for pure Python |
| Automatic retries on publish failure | Resilience to transient failures | Can result in duplicate publishes, masks real issues that need investigation | Fail fast, investigate, fix root cause, manually re-run |
| Embedding secrets in workflow | Convenience over security | Trusted publishing eliminates this need entirely | Use PyPI trusted publishers (OIDC) - no secrets needed |

## Feature Dependencies

```
Tag Push
    └──triggers──> Quality Gates (make check)
                       └──requires──> Multi-version Testing
                       └──success──> Build Artifacts (wheel + sdist)
                                         └──success──> Verify Package Install
                                                           └──success──> Publish to PyPI (Trusted Publisher)
                                                                             └──success──> Create GitHub Release
                                                                                               └──includes──> Auto-generated Changelog
                                                                                               └──includes──> PyPI Link
                                                                                               └──includes──> MILESTONES.md Link

Manual Approval Gate ──gates──> Publish to PyPI
    (optional enhancement)

TestPyPI Preview ──validates before──> Publish to PyPI
    (optional enhancement)

Package Attestations ──auto-enabled with──> Trusted Publisher
```

### Dependency Notes

- **Quality Gates require Multi-version Testing:** Must test on all supported Python versions (3.11, 3.12) before publishing
- **Build Artifacts require Quality Gates success:** Don't build if tests/lint/typecheck fail
- **Verify Package requires Build Artifacts:** Must build wheel before testing installation
- **Publish requires Verify success:** Don't publish if built package doesn't install correctly
- **GitHub Release requires Publish success:** Only create release after PyPI publish succeeds
- **Changelog generation is standalone:** Can run in parallel with build, combines results later
- **Manual Approval gates Publish (optional):** If environment protection enabled, blocks publish until reviewer approves
- **TestPyPI validates before production (optional):** Sequential - test on test.pypi.org, then publish to production PyPI
- **Attestations are automatic:** Enabled by default with trusted publishing, no explicit configuration needed

## MVP Definition

### Launch With (v0.2.0)

Minimum viable CD pipeline - what's needed to automate releases safely.

- [x] Tag-triggered workflow — Core CD activation mechanism
- [x] Full quality gates (make check) — Already have linting, type checking, 398 tests
- [x] Multi-version testing matrix — Already testing Python 3.11, 3.12 in CI
- [x] Build wheel + sdist — Standard `python -m build` with hatchling
- [x] Package installation verification — Test `pip install` from built wheel works
- [x] Trusted Publisher auth — Modern OIDC, no secrets needed
- [x] Publish to PyPI — Core publishing with `pypa/gh-action-pypi-publish`
- [x] Create GitHub release — With tag, title, and body
- [x] Auto-generated changelog — User requirement: git history-based changelog
- [x] PyPI link in release — User requirement: direct link to published package
- [x] MILESTONES.md link — User requirement: link to milestone documentation

### Add After Validation (v0.2.x)

Features to add once core CD is proven reliable.

- [ ] Manual approval gate — Add when team wants control over release timing (needs GitHub environment setup)
- [ ] TestPyPI preview — Add if team wants double-verification before production (separate test publish job)
- [ ] Release announcement automation — Slack/Discord notification on successful release
- [ ] Changelog improvement — Conventional commits parsing for better categorization
- [ ] Version mismatch detection — Explicit check that git tag matches hatch-vcs version

### Future Consideration (v0.3+)

Features to defer until more complex needs emerge.

- [ ] Multi-package publishing — If monorepo grows to multiple PyPI packages
- [ ] Conditional publishing — Different PyPI indices for alpha/beta/stable tags
- [ ] Rollback automation — Automated yanking + revert commit on critical failures
- [ ] Performance benchmarking — Automated performance regression detection in CD
- [ ] Documentation deployment — Publish docs to ReadTheDocs or GitHub Pages on release

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Tag-triggered workflow | HIGH | LOW | P1 |
| Quality gates execution | HIGH | LOW | P1 |
| Build wheel + sdist | HIGH | LOW | P1 |
| Trusted Publisher auth | HIGH | LOW | P1 |
| Publish to PyPI | HIGH | LOW | P1 |
| Package verification | HIGH | MEDIUM | P1 |
| GitHub release creation | HIGH | MEDIUM | P1 |
| Auto-generated changelog | HIGH | MEDIUM | P1 |
| PyPI link in release | MEDIUM | LOW | P1 |
| MILESTONES.md link | MEDIUM | LOW | P1 |
| Multi-version testing | HIGH | LOW | P1 |
| Package attestations | MEDIUM | LOW | P1 |
| Manual approval gate | MEDIUM | MEDIUM | P2 |
| TestPyPI preview | MEDIUM | MEDIUM | P2 |
| Version consistency check | LOW | LOW | P2 |
| Release notifications | LOW | MEDIUM | P3 |
| Rollback automation | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for v0.2.0 launch
- P2: Should have, add when team requests
- P3: Nice to have, future consideration

## Integration with Existing Tooling

### Already Built (v0.1.0)

| Existing Tool | CD Integration | Complexity |
|---------------|---------------|------------|
| `make check` | Run in CD workflow before build | LOW - single command |
| `hatchling` with `hatch-vcs` | Build backend, extracts version from git tags | LOW - already configured |
| Multi-Python CI matrix | Reuse existing CI matrix for CD validation | LOW - copy strategy from ci.yml |
| 398 passing tests | Quality gate prevents broken releases | LOW - already comprehensive |
| `pytest` with coverage | Ensures test coverage before publish | LOW - part of make check |
| `ruff` + `mypy` | Code quality gates | LOW - part of make check |

### New Requirements

| Tool | Purpose | Why This Tool |
|------|---------|--------------|
| `pypa/gh-action-pypi-publish` | Official PyPA GitHub Action for publishing | Industry standard, trusted publishing support, attestations by default |
| `gh` CLI or `actions/create-release` | Create GitHub releases | `gh` CLI simpler, allows custom changelog formatting |
| `git-changelog` or manual script | Generate changelog from git history | Flexible parsing, supports templates, recent release (Jan 2026) |
| GitHub Actions `environment` | Optional manual approval | Built-in GitHub feature, no external dependencies |

## Workflow Architecture

### Single Workflow vs. Multiple Workflows

**Recommendation:** Single workflow with sequential jobs

**Rationale:**
- **Simpler:** One `.github/workflows/release.yml` file
- **Atomic:** Either entire release succeeds or fails, no partial states
- **Dependency management:** GitHub Actions job dependencies ensure correct ordering
- **Artifact sharing:** Built wheel/sdist passed between jobs as artifacts

**Job Structure:**
```
1. validate (matrix: [py3.11, py3.12])
   - Run make check on each Python version
   - Build artifacts once (py3.11 only)

2. verify
   - Test install built wheel in fresh environment
   - Verify imports work

3. publish (environment: pypi, if using manual approval)
   - Upload to PyPI with trusted publishing
   - Attestations generated automatically

4. release
   - Generate changelog from git history
   - Create GitHub release with changelog, PyPI link, MILESTONES.md link
```

### Alternative: Two-Stage with TestPyPI

**If team wants preview capability:**
```
1. validate (same as above)
2. verify (same as above)
3. publish-test
   - Upload to test.pypi.org
   - Test install from test PyPI
4. publish-prod (environment: pypi with manual approval)
   - Upload to production PyPI
5. release (same as above)
```

**Tradeoff:** More confidence but adds manual approval requirement

## Competitor Analysis

| Feature | poetry-publish | flit | hatch | Our Approach |
|---------|----------------|------|-------|--------------|
| Build tool | poetry | flit | hatch | hatch (already using hatchling) |
| Version source | pyproject.toml | pyproject.toml | git tags (hatch-vcs) | git tags (hatch-vcs) - tag is source of truth |
| PyPI auth | API token or OIDC | API token or OIDC | API token or OIDC | OIDC only (trusted publishing) |
| GitHub release | Manual or separate action | Manual or separate action | Manual or separate action | Automated with changelog |
| Attestations | Optional | Optional | Optional | Automatic with trusted publishing |
| Quality gates | External (CI) | External (CI) | External (CI) | Built into CD workflow |
| TestPyPI | Optional separate job | Optional separate job | Optional separate job | v0.2.0: No; v0.2.x: Optional |

**Our differentiation:**
1. **Quality gates in CD:** Don't just publish on tag - validate first
2. **Package verification:** Test installation before publishing
3. **Complete release:** GitHub release with changelog + links generated automatically
4. **Multi-version validation:** Test on all supported Python versions before publish

## Common Pitfalls and Mitigations

### Pitfall: Publishing before tests complete

**Problem:** Workflow publishes even if earlier tests fail
**Mitigation:** Use job dependencies (`needs: [validate, verify]`) - publish only if all prerequisites succeed

### Pitfall: Version mismatch between tag and package

**Problem:** Git tag is `v1.2.3` but package builds as `1.2.4` due to uncommitted changes
**Mitigation:**
- Ensure workflow runs `fetch-depth: 0` so hatch-vcs sees full history
- Optional: Add explicit version consistency check job

### Pitfall: Trusted Publisher not configured on PyPI

**Problem:** First publish attempt fails because PyPI doesn't trust the GitHub repo
**Mitigation:** Document PyPI setup steps - must configure trusted publisher BEFORE first automated publish

### Pitfall: Secrets in environment variables

**Problem:** Developer adds PyPI token as secret "just in case"
**Mitigation:** Document that trusted publishing requires NO secrets - explicitly avoid token configuration

### Pitfall: Forgotten release notes

**Problem:** GitHub release created with empty body
**Mitigation:** Auto-generate changelog from git history - always have content

### Pitfall: Failed publish with no rollback

**Problem:** Publish fails halfway through, unclear how to recover
**Mitigation:**
- Atomic publish - either entire workflow succeeds or fails
- Document recovery: PyPI allows re-publishing same version if publish failed
- If publish succeeded but release failed, can manually create GitHub release

### Pitfall: No quality gate bypass for emergencies

**Problem:** Critical security fix needs immediate publish, but tests are failing for unrelated reason
**Mitigation:** Don't create bypass - fix tests or publish manually with explicit override (documented procedure)

## Sources

**PyPI Publishing Best Practices:**
- [PyPI Trusted Publishers Documentation](https://docs.pypi.org/trusted-publishers/)
- [Python Packaging User Guide - Publishing with GitHub Actions](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [pypa/gh-action-pypi-publish GitHub Repository](https://github.com/pypa/gh-action-pypi-publish)
- [PyPI Package Publishing Guide 2026](https://inventivehq.com/blog/python-pypi-publishing-guide)
- [Publishing to PyPI from GitHub Actions without tokens](https://til.simonwillison.net/pypi/pypi-releases-from-github)

**Tag-Based CD Pipelines:**
- [Tag-Based Python CI/CD Pipeline Guide](https://dhruv-ahuja.github.io/posts/tag-based-ci-cd-pipeline/)
- [Python CI/CD Pipeline Mastery 2025](https://atmosly.com/blog/python-ci-cd-pipeline-mastery-a-complete-guide-for-2025)
- [Python Packages CI/CD Guide](https://py-pkgs.org/08-ci-cd.html)

**Changelog Generation:**
- [git-changelog PyPI Package](https://pypi.org/project/git-changelog/) - Released Jan 30, 2026
- [changelog-gen PyPI Package](https://pypi.org/project/changelog-gen/) - Released Jan 7, 2026
- [python-semantic-release Documentation](https://python-semantic-release.readthedocs.io/)

**GitHub Actions Configuration:**
- [GitHub Docs - Building and Testing Python](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [GitHub Docs - Automatically Generated Release Notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes)
- [GitHub Actions Environment Protection Rules 2026](https://oneuptime.com/blog/post/2026-01-25-github-actions-environment-protection-rules/view)
- [GitHub Docs - Managing Environments for Deployment](https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment)

**Package Build & Verification:**
- [Python Packaging Guide - Package Formats](https://packaging.python.org/en/latest/discussions/package-formats/)
- [TestPyPI Usage Guide](https://packaging.python.org/guides/using-testpypi/)
- [PyPI Package Index Guide 2026](https://www.articsledge.com/post/python-package-index-pypi)

**Quality Gates:**
- [Enforce Code Quality Gates in GitHub Actions](https://graphite.com/guides/enforce-code-quality-gates-github-actions)
- [Deployment Gates Guide 2026](https://oneuptime.com/blog/post/2026-01-30-deployment-gates/view)
- [Status Checks in GitHub Actions 2026](https://oneuptime.com/blog/post/2026-01-26-status-checks-github-actions/view)

**Attestations & Security:**
- [PyPI Attestations Documentation](https://docs.pypi.org/attestations/)
- [GitHub Docs - Using Artifact Attestations](https://docs.github.com/actions/security-for-github-actions/using-artifact-attestations/using-artifact-attestations-to-establish-provenance-for-builds)
- [PyPI Digital Attestation Support](https://blog.deps.dev/pypi-attestations/)

**Anti-Patterns & Pitfalls:**
- [DevOps Common Mistakes and Anti-Patterns 2026](https://medium.com/@sainath.814/devops-roadmap-part-45-common-devops-mistakes-anti-patterns-how-to-avoid-them-based-on-real-de981419c7c4)
- [CI/CD Anti-Patterns Book](https://leanpub.com/ci-cd-anti-patterns)
- [CI/CD Anti-Patterns - What's Slowing Down Your Pipeline](https://em360tech.com/tech-articles/cicd-anti-patterns-whats-slowing-down-your-pipeline)

**PyPI Release Management:**
- [PyPI Docs - Yanking Releases](https://docs.pypi.org/project-management/yanking/)
- [What to Do When You Botch a PyPI Release](https://snarky.ca/what-to-do-when-you-botch-a-release-on-pypi/)

---
*Feature research for: Tag-based CD pipeline for PyPI package publishing*
*Researched: 2026-02-10*
*Research confidence: HIGH - Based on official PyPI documentation, PyPA tools, recent 2026 guides, and GitHub official documentation*
