---
status: resolved
trigger: "Investigate issue: pbism-schema-validation-error"
created: 2026-02-10T00:00:00Z
updated: 2026-02-10T00:06:00Z
---

## Current Focus

hypothesis: Fabric's definition.pbism schema v1.0.0 ONLY accepts $schema, settings, and version properties. The author, createdAt, description, modifiedAt, name properties were added based on user decision but are not valid per Fabric's actual schema.
test: Create a minimal definition.pbism with ONLY $schema, settings, version and verify against error message
expecting: These are the only three properties Fabric accepts; all others cause "schema does not allow additional properties" error
next_action: Test hypothesis by examining minimal valid structure vs current code output

## Symptoms

expected: Successfully deploy semantic model to Fabric workspace when calling smg.generate_semantic_model(config)
actual: PipelineError during deployment - Fabric rejects the generated definition.pbism file with schema validation errors saying properties are not defined and schema does not allow additional properties
errors:
```
RuntimeError: Operation 5e745de6-03ee-4c21-aba7-3bc72b7f5aa7 failed: [Workload_FailedToParseFile] Dataset Workload failed to import the dataset with dataset id 00000000-0000-0000-0000-000000000000. Cannot read 'definition.pbism'. 'definition.pbism':
Property 'author' has not been defined and the schema does not allow additional properties. Path 'author', line 3, position 11.
Property 'createdAt' has not been defined and the schema does not allow additional properties. Path 'createdAt', line 4, position 14.
Property 'description' has not been defined and the schema does not allow additional properties. Path 'description', line 5, position 16.
Property 'modifiedAt' has not been defined and the schema does not allow additional properties. Path 'modifiedAt', line 6, position 15.
Property 'name' has not been defined and the schema does not allow additional properties. Path 'name', line 7, position 9.

PipelineError: [deployment] Failed to deploy to workspace Fabric - Dev
```
reproduction: Run smg.generate_semantic_model(config) with deployment to Fabric workspace configured (dev_mode=False)
started: Unknown - first time user is attempting this deployment

## Eliminated

## Evidence

- timestamp: 2026-02-10T00:01:00Z
  checked: src/semantic_model_generator/tmdl/metadata.py lines 41-77
  found: generate_definition_pbism_json() creates definition.pbism with properties: $schema, author, createdAt, description, modifiedAt, name, settings, version
  implication: Function writes metadata properties that Fabric schema may not accept

- timestamp: 2026-02-10T00:01:30Z
  checked: src/semantic_model_generator/tmdl/generate.py lines 392-398
  found: generate_all_tmdl() calls generate_definition_pbism_json(model_name, timestamp=fixed_timestamp) with only model_name and timestamp, not passing description or author (defaults to empty strings)
  implication: Even with empty strings, these properties are included in the JSON output

- timestamp: 2026-02-10T00:03:00Z
  checked: Web searches and Fabric REST API documentation
  found: References mention definition.pbism contains "version and settings" properties. No documentation found showing author/createdAt/description/modifiedAt/name are valid properties
  implication: Schema likely only accepts $schema, settings, version - not the metadata properties added per user decision

- timestamp: 2026-02-10T00:03:30Z
  checked: Error message pattern
  found: All five rejected properties (author, createdAt, description, modifiedAt, name) are properties BEYOND the $schema, settings, version base
  implication: Strong evidence that definition.pbism schema is minimal (only 3 properties), not the full metadata structure implemented

## Resolution

root_cause: The generate_definition_pbism_json() function includes properties (author, createdAt, description, modifiedAt, name) that are NOT allowed by Fabric's definition.pbism schema v1.0.0. The schema only accepts $schema, settings, and version. These extra properties were added based on a user decision documented in .planning/phases/05-tmdl-generation/05-02-PLAN.md but Fabric's actual schema does not support them. When deploying to Fabric, the service validates against its strict schema and rejects these additional properties.

fix: Removed author, createdAt, description, modifiedAt, name properties from generate_definition_pbism_json(). Function now only outputs $schema, settings, version. Updated function signature to keep parameters for API compatibility but noted they are unused. Updated tests to verify only allowed properties are present.

verification:
- All 400 tests pass including 21 metadata tests
- Linter (ruff) passes on src/ and tests/
- Type checker (mypy) passes on src/
- generate_definition_pbism_json() now produces minimal valid JSON with only $schema, settings, version
- New test verifies rejected properties are NOT present in output

files_changed:
- src/semantic_model_generator/tmdl/metadata.py
- tests/tmdl/test_metadata.py
