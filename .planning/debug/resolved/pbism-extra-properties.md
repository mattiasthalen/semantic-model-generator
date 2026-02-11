---
status: resolved
trigger: "Investigate and fix issue: pbism-extra-properties"
created: 2026-02-11T00:00:00Z
updated: 2026-02-11T00:00:00Z
---

## Current Focus

hypothesis: Root cause confirmed - definition.pbism contains properties not allowed by Fabric schema
test: Fix implemented and verified
expecting: definition.pbism will only contain $schema, version, and settings
next_action: Archive session

## Symptoms

expected: `definition.pbism` should only contain properties allowed by the Fabric semanticModel schema: `$schema`, `version`, and optionally `settings`.
actual: The generated `definition.pbism` includes extra properties (`author`, `createdAt`, `description`, `modifiedAt`, `name`) that cause a `Workload_FailedToParseFile` error when deploying via the Fabric REST API.
errors: RuntimeError: Operation failed: [Workload_FailedToParseFile] Cannot read 'definition.pbism'. Property 'author' has not been defined and the schema does not allow additional properties. Same for 'createdAt', 'description', 'modifiedAt', 'name'.
reproduction: Run the pipeline with `generate_semantic_model(config)` targeting a Fabric workspace. The deploy step fails when Fabric validates the definition.pbism file.
started: First production deployment test (the code was written based on assumptions about the schema that turned out to be wrong).

## Eliminated

(Root cause already identified by orchestrator - skipping investigation phase)

## Evidence

- timestamp: 2026-02-11T00:00:00Z
  checked: Fabric schema at https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json
  found: Schema only allows $schema, version, and settings with additionalProperties: false
  implication: All other properties (author, createdAt, description, modifiedAt, name) must be removed

## Resolution

root_cause: `generate_definition_pbism_json()` in `src/semantic_model_generator/tmdl/metadata.py` generates a definition.pbism JSON object that includes properties (author, createdAt, description, modifiedAt, name) which are NOT allowed by the Fabric schema. The schema has additionalProperties: false and only allows $schema, version, and settings.

fix: Simplified generate_definition_pbism_json() to only emit $schema, version, and settings. Removed author, description, timestamp parameters. Updated call sites in generate.py and all tests.

verification: All 401 tests pass. Generated definition.pbism now only contains the three allowed properties: $schema, settings, and version. This matches the Fabric schema requirements and will not be rejected during deployment.

files_changed:
- src/semantic_model_generator/tmdl/metadata.py: Simplified generate_definition_pbism_json() to remove extra properties and unused datetime import
- src/semantic_model_generator/tmdl/generate.py: Updated call to generate_definition_pbism_json() to remove arguments
- tests/tmdl/test_metadata.py: Updated all tests to match new signature and verify only allowed properties are present
