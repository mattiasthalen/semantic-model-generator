---
created: 2026-02-10T23:24:29.097Z
title: Remove Python 3.12 from CI/CD workflows
area: ci
files:
  - .github/workflows/ci.yml:14
  - .github/workflows/publish.yml:19
  - .github/workflows/publish.yml:47
  - .github/workflows/publish.yml:74
---

## Problem

Both CI and CD workflows run checks on Python 3.12, but Microsoft Fabric notebooks only support Python 3.11 (the primary target environment).

**CI workflow (.github/workflows/ci.yml:14):**
- Matrix strategy runs `make check` on both 3.11 and 3.12

**Publish workflow (.github/workflows/publish.yml):**
- Line 19: validate job matrix includes 3.12
- Line 47: build job uses 3.12
- Line 74: verify job uses 3.12

Running checks on Python 3.12 provides no value since:
1. Fabric users cannot use Python 3.12
2. The library's `requires-python = ">=3.11"` allows 3.12+ but Fabric doesn't
3. Testing against unsupported environments wastes CI/CD time

## Solution

**CI workflow (.github/workflows/ci.yml):**
```yaml
strategy:
  matrix:
    python-version: ["3.11"]
```

**Publish workflow (.github/workflows/publish.yml):**
- Line 19: Change matrix to `python-version: ['3.11']`
- Line 47: Change to `python-version: '3.11'`
- Line 74: Change to `python-version: '3.11'`

This aligns all CI/CD testing with the actual deployment environment (Fabric notebooks).
