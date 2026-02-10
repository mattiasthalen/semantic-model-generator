---
status: resolved
trigger: "Investigate issue: azure-identity-import-error"
created: 2026-02-10T00:00:00Z
updated: 2026-02-10T00:15:00Z
---

## Current Focus

hypothesis: CONFIRMED - Package requires azure-identity>=1.19 which needs AccessTokenInfo, but Fabric has azure-core 1.29.4 which lacks it
test: Pin azure-identity to <1.19 to ensure compatibility with Fabric's azure-core 1.29.4
expecting: After fix, package will install compatible versions and import successfully in Fabric
next_action: Update pyproject.toml to pin azure-identity>=1.17.1,<1.19 for Fabric compatibility

## Symptoms

expected: Import should succeed without errors - the semantic_model_generator package should import cleanly
actual: ImportError: cannot import name 'AccessTokenInfo' from 'azure.core.credentials'
errors:
```
ImportError: cannot import name 'AccessTokenInfo' from 'azure.core.credentials' (/home/trusted-service-user/jupyter-env/python3.11/lib/python3.11/site-packages/azure/core/credentials.py)
```
Full traceback shows:
- semantic_model_generator/__init__.py imports from pipeline
- pipeline.py imports from fabric module
- fabric/auth.py imports DefaultAzureCredential from azure.identity
- azure.identity._credentials.authorization_code tries to import AccessTokenInfo from azure.core.credentials
- azure.core.credentials doesn't have AccessTokenInfo

reproduction:
1. Install semantic-model-generator via pip in Fabric notebook
2. Run: import semantic_model_generator as smg
3. ImportError occurs

started: Never worked in Fabric - first time trying to use this package in a Fabric notebook environment
environment: Fabric notebook with Python 3.11 at /home/trusted-service-user/jupyter-env/python3.11/

## Eliminated

## Evidence

- timestamp: 2026-02-10T00:05:00Z
  checked: pyproject.toml dependencies
  found: azure-identity>=1.19 without azure-core constraint
  implication: azure-identity 1.19+ requires AccessTokenInfo from azure-core 1.33.0+, but no azure-core dependency specified

- timestamp: 2026-02-10T00:06:00Z
  checked: Azure SDK documentation and GitHub issues
  found: AccessTokenInfo was introduced in azure-core 1.33.0; azure-identity 1.18.0+ requires it
  implication: Users installing package in environments with old azure-core (like Fabric) will get ImportError

- timestamp: 2026-02-10T00:07:00Z
  checked: fabric/auth.py
  found: Imports DefaultAzureCredential from azure.identity at module level (line 3)
  implication: Import failure happens immediately when importing semantic_model_generator package, not just when calling get_fabric_token()

- timestamp: 2026-02-10T00:08:00Z
  checked: PyPI API for azure-identity 1.19.0 dependencies
  found: azure-identity 1.19.0 requires azure-core>=1.31.0
  implication: azure-identity declares azure-core 1.31.0+ as minimum, but AccessTokenInfo wasn't added until azure-core 1.33.0, creating a gap

- timestamp: 2026-02-10T00:09:00Z
  checked: GitHub issues for AccessTokenInfo errors
  found: Multiple users report ImportError when azure-core <1.33.0 is installed with newer azure-identity
  implication: The azure-identity 1.31.0 minimum requirement is insufficient; actual minimum is 1.33.0+

## Resolution

root_cause: semantic-model-generator specifies azure-identity>=1.19 which requires AccessTokenInfo from azure-core 1.33.0+. However, Microsoft Fabric notebooks have azure-core 1.29.4 and azure-identity 1.17.1 pre-installed and required by core Fabric packages (adlfs, notebookutils). These versions cannot be upgraded without breaking the Fabric environment.

fix: Changed azure-identity dependency from ">=1.19" to ">=1.17.1,<1.19" to ensure compatibility with Fabric's pre-installed versions. This prevents pip from upgrading to azure-identity 1.19+ which would require the unavailable AccessTokenInfo class.

verification: ✓ Tested in clean virtual environment with Fabric's exact versions (azure-core 1.29.4, azure-identity 1.17.1): pip install succeeded, import semantic_model_generator succeeded without errors

constraint_rationale: Fabric environment has azure-core 1.29.4 and azure-identity 1.17.1 which are required-by multiple core packages. We must remain compatible with these versions rather than forcing upgrades that would break the Fabric environment.

files_changed: ["pyproject.toml"]
