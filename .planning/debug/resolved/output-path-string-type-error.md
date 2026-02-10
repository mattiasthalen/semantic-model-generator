---
status: resolved
trigger: "Investigate issue: output-path-string-type-error"
created: 2026-02-10T00:00:00Z
updated: 2026-02-10T00:00:00Z
---

## Current Focus

hypothesis: PipelineConfig accepts output_path as Path | None but doesn't convert string to Path in __post_init__, so when user passes string it remains a string and causes TypeError in writer.py line 42
test: confirming that PipelineConfig.__post_init__ doesn't convert output_path to Path type
expecting: no Path() conversion in __post_init__, which means string values pass through unconverted
next_action: confirm the type annotation allows string but dataclass doesn't convert it

## Symptoms

expected: User passes output_path="./builtin" as string, should be converted to Path and work correctly
actual: TypeError raised when trying to use / operator on string: "unsupported operand type(s) for /: 'str' and 'str'"
errors: |
  File ~/jupyter-env/python3.11/lib/python3.11/site-packages/semantic_model_generator/output/writer.py:42, in get_output_folder(base_path, model_name, dev_mode, timestamp)
       41         timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
  ---> 42     return base_path / f"{model_name}_{timestamp}"
       44 return base_path / model_name

  TypeError: unsupported operand type(s) for /: 'str' and 'str'

  PipelineError: [output] Failed to write folder at ./builtin: unsupported operand type(s) for /: 'str' and 'str'
reproduction: |
  config = smg.PipelineConfig(
      output_mode="folder",
      output_path="./builtin",  # String instead of Path
      ...
  )
  result = smg.generate_semantic_model(config)
started: User just upgraded to v0.2.2 from PyPI and is testing in Fabric notebook. The issue occurs when output_path is passed as a string (which is natural in notebook environments) instead of a Path object.

## Eliminated

## Evidence

- timestamp: 2026-02-10T00:01:00Z
  checked: /workspaces/semantic-model-generator/src/semantic_model_generator/output/writer.py line 42
  found: get_output_folder expects base_path: Path (type annotation on line 15) and uses / operator on line 42: "return base_path / f"{model_name}_{timestamp}""
  implication: The / operator only works with Path objects, not strings. If base_path is a string, TypeError occurs.

- timestamp: 2026-02-10T00:02:00Z
  checked: /workspaces/semantic-model-generator/src/semantic_model_generator/pipeline.py lines 71, 83-110, 188-190
  found: PipelineConfig has output_path: Path | None = None (line 71), but __post_init__ only validates presence, not type. Line 188 passes config.output_path directly to write_tmdl_folder without conversion.
  implication: If user passes string to PipelineConfig(output_path="./builtin"), it stays as string and gets passed to write_tmdl_folder, then to get_output_folder where / operator fails.

- timestamp: 2026-02-10T00:03:00Z
  checked: Python dataclass behavior with Path type annotation
  found: Dataclasses do NOT automatically convert types. TestConfig(output_path='./test') results in output_path remaining as str, not converted to Path.
  implication: Type annotations in dataclasses are hints only, not runtime converters. PipelineConfig must explicitly convert string to Path in __post_init__.

## Resolution

root_cause: PipelineConfig dataclass has output_path type annotation as Path | None, but dataclasses don't auto-convert types. When user passes output_path="./builtin" (string), it remains a string. This string is passed to write_tmdl_folder → get_output_folder where line 42 tries base_path / string, causing TypeError because / operator requires Path objects on both sides.
fix: |
  1. Updated PipelineConfig.output_path type annotation to str | Path | None to signal users that strings are acceptable
  2. Added explicit conversion in PipelineConfig.__post_init__ that converts string to Path using object.__setattr__ (required for frozen dataclass)
  3. Added two new tests: test_output_path_converts_string_to_path and test_output_path_accepts_path_object
verification: |
  ✓ Unit tests pass: Created config with output_path="./builtin", verified isinstance(config.output_path, Path) returns True
  ✓ Integration test: Used converted path with write_tmdl_folder and get_output_folder, verified / operator works correctly
  ✓ All 32 existing pipeline tests still pass (no regressions)
  ✓ Reproduction scenario verified: config = PipelineConfig(output_path="./builtin") now works without TypeError
files_changed:
  - /workspaces/semantic-model-generator/src/semantic_model_generator/pipeline.py
  - /workspaces/semantic-model-generator/tests/test_pipeline.py
