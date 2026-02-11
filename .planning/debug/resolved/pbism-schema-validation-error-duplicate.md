---
status: resolved
trigger: "Investigate issue: pbism-schema-validation-error"
created: 2026-02-10T00:00:00Z
updated: 2026-02-10T00:03:00Z
---

## Current Focus

hypothesis: This issue was ALREADY FIXED in commit a075822 "fix: remove unsupported properties from definition.pbism". The reported error may be from an old deployment or cached output.
test: Verify current code does NOT generate the rejected properties
expecting: Current code only generates $schema, settings, version - no rejected properties
next_action: Verify current implementation and determine if this is a duplicate report or stale error

## Symptoms

expected: Semantic model should deploy successfully to Fabric workspace
actual: Deployment fails with RuntimeError from Fabric API during TMDL import
errors:
```
RuntimeError: Operation fc780e8e-e0fa-4a6a-ae0e-37ce009a5775 failed: [Workload_FailedToParseFile] Dataset Workload failed to import the dataset with dataset id 00000000-0000-0000-0000-000000000000. Cannot read 'definition.pbism'. 'definition.pbism':
Property 'author' has not been defined and the schema does not allow additional properties. Path 'author', line 3, position 11.
Property 'createdAt' has not been defined and the schema does not allow additional properties. Path 'createdAt', line 4, position 14.
Property 'description' has not been defined and the schema does not allow additional properties. Path 'description', line 5, position 16.
Property 'modifiedAt' has not been defined and the schema does not allow additional properties. Path 'modifiedAt', line 6, position 15.
Property 'name' has not been defined and the schema does not allow additional properties. Path 'name', line 7, position 9.
```
reproduction: Run smg.generate_semantic_model(config) with dev_mode=False targeting a Fabric workspace
started: This appears to be a regression - the code was working before based on git history showing recent debug sessions resolved

## Eliminated

- hypothesis: Code currently generates rejected properties
  evidence: Verified generate_definition_pbism_json() only outputs $schema, settings, version. Test test_generate_definition_pbism_json_does_not_contain_rejected_properties explicitly verifies rejected properties are NOT present. All 6 pbism tests pass.
  timestamp: 2026-02-10T00:02:00Z

## Evidence

- timestamp: 2026-02-10T00:01:00Z
  checked: Git history for pbism-related changes
  found: Commit a075822 "fix: remove unsupported properties from definition.pbism" and commit 4186c04 "docs: resolve debug pbism-schema-validation-error" are the two most recent commits
  implication: This exact issue was already debugged and fixed

- timestamp: 2026-02-10T00:01:30Z
  checked: src/semantic_model_generator/tmdl/metadata.py lines 40-67
  found: generate_definition_pbism_json() ONLY generates $schema, settings, version. Contains comment: "Fabric's definition.pbism schema v1.0.0 only accepts $schema, settings, and version." Parameters model_name, description, author, timestamp are kept for API compatibility but unused.
  implication: Current code is correct and does NOT generate the rejected properties

- timestamp: 2026-02-10T00:02:00Z
  checked: tests/tmdl/test_metadata.py line 158-176
  found: test_generate_definition_pbism_json_does_not_contain_rejected_properties explicitly asserts name, description, author, createdAt, modifiedAt are NOT in output. Asserts only $schema, settings, version are present. Test passes.
  implication: Fix is verified and working

- timestamp: 2026-02-10T00:02:30Z
  checked: .planning/debug/resolved/pbism-schema-validation-error.md
  found: Previous debug session with identical symptoms, same root cause, same fix. Resolution shows all tests passed, linter passed, type checker passed.
  implication: This is a duplicate report of an already-resolved issue

## Resolution

root_cause: This is a DUPLICATE REPORT of an issue that was already resolved in commit a075822 (2026-02-10). The issue described in the symptoms (Fabric rejecting author, createdAt, description, modifiedAt, name properties in definition.pbism) was caused by generate_definition_pbism_json() including metadata properties not allowed by Fabric's schema v1.0.0. However, this was already fixed - the function now ONLY outputs $schema, settings, and version. The error in the user's report is likely from: (1) cached/stale output from before the fix, (2) running old code before pulling latest changes, or (3) reporting an error that occurred before the fix was applied.

fix: NO NEW FIX NEEDED. The fix was already applied in commit a075822. Current code is correct.

verification:
- Current code verified: generate_definition_pbism_json() only outputs $schema, settings, version
- Tested function directly: Confirmed no rejected properties in output even when passing description/author/timestamp arguments
- All 6 pbism tests pass including test_generate_definition_pbism_json_does_not_contain_rejected_properties
- Package installed in editable mode, Python imports from workspace source
- No definition.pbism files found in workspace (no stale cached output)

files_changed: []

recommendation: User should regenerate the semantic model output using current code. If error persists, need to check: (1) Is user running latest code? (2) Is there cached output being reused? (3) When exactly did the deployment error occur - before or after commit a075822?
