---
created: 2026-02-10T23:24:29.097Z
title: Remove Python 3.12 from CI checks
area: ci
files:
  - .github/workflows/ci.yml:14
---

## Problem

The CI workflow currently runs `make check` on both Python 3.11 and 3.12 (matrix strategy). However, Microsoft Fabric notebooks only support Python 3.11, and this is the primary target environment for semantic-model-generator.

Running checks on Python 3.12 provides no value since:
1. Fabric users cannot use Python 3.12
2. The library's `requires-python = ">=3.11"` constraint allows 3.12+ but Fabric doesn't
3. Testing against unsupported environments wastes CI time

## Solution

Update `.github/workflows/ci.yml` to only test Python 3.11:

```yaml
strategy:
  matrix:
    python-version: ["3.11"]
```

This aligns CI testing with the actual deployment environment (Fabric notebooks).
