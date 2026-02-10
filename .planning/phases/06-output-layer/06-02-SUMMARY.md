---
phase: 06-output-layer
plan: 02
subsystem: output
tags: [folder-writer, dev-prod-modes, watermark-preservation, tdd]
dependencies:
  requires: [watermark, WriteSummary, atomic-write]
  provides: [write_tmdl_folder, get_output_folder]
  affects: []
tech-stack:
  added: [datetime.UTC, pathlib.Path.mkdir]
  patterns: [dev-prod-mode-pattern, folder-structure-generation, file-preservation]
key-files:
  created:
    - src/semantic_model_generator/output/writer.py
    - tests/output/test_writer.py
  modified:
    - src/semantic_model_generator/output/__init__.py
decisions:
  - "Dev mode (default) appends UTC timestamp to folder name for safe iteration"
  - "Prod mode uses base model name and protects against accidental overwrites"
  - "FileExistsError raised in prod mode when folder exists and overwrite=False"
  - "Watermark detection determines if files are overwritten or preserved"
  - "Byte-identical content reported as unchanged to skip unnecessary writes"
  - "Extra files on disk not deleted (non-destructive regeneration)"
  - "Timestamp format: YYYYMMDDTHHMMSSz (ISO compact, sortable)"
metrics:
  duration: 168
  tests_added: 25
  completed_at: "2026-02-10T08:32:57Z"
---

# Phase 06 Plan 02: TMDL Folder Writer with Dev/Prod Modes Summary

**One-liner:** Folder writer with dev/prod mode support, watermark-based file preservation, and structured WriteSummary reporting for safe TMDL regeneration.

## Objective Achievement

Created the core output capability that materializes Phase 5's in-memory TMDL semantic model to disk:
- Dev mode enables safe iteration with timestamped folders (no overwrites)
- Prod mode provides production deployment with overwrite protection
- Watermark detection preserves manually-maintained files from regeneration
- WriteSummary provides accurate feedback on written/skipped/unchanged files
- Proper Fabric-compatible directory structure (definition/, definition/tables/)

## TDD Execution

### RED Phase (Commit: 88ec731)
Created comprehensive failing test suite covering:
- `get_output_folder()`: dev/prod mode behavior, timestamp handling, name preservation
- `write_tmdl_folder()`: directory creation, file writing, watermark injection
- Dev mode: timestamped folder creation, no overwrite conflicts
- Prod mode: base name folder, FileExistsError protection, overwrite=True bypass
- Watermark preservation: skip manual files, overwrite auto-generated
- WriteSummary accuracy: written/skipped/unchanged file tracking
- File format handling: .tmdl (triple-slash), .json/.pbism/.platform (_comment)
- Edge cases: parent directory creation, extra file preservation, determinism

Total: 25 comprehensive test cases

### GREEN Phase (Commit: 1ab2970)
Implemented full folder writer module:
- `get_output_folder()` - dev/prod mode path calculation with timestamp support
- `write_tmdl_folder()` - main entry point for writing TMDL dict to disk
- Creates proper directory structure: definition/, definition/tables/
- Watermarks all files using `add_watermark_to_content()` from plan 06-01
- File processing logic:
  - New files: write with watermark
  - Existing files: check for byte-identical content (skip write)
  - Watermarked files: overwrite on regeneration
  - Non-watermarked files: preserve and report as skipped
- Prod mode protection: raises FileExistsError if folder exists without overwrite=True
- Returns WriteSummary with sorted, deterministic file lists

All 299 tests pass (274 existing + 25 new). make check clean.

### REFACTOR Phase
No refactoring needed. Implementation is clean, well-documented, follows project conventions:
- Clear step-by-step structure with inline comments
- Functional style with proper separation of concerns
- Explicit type hints and encoding specifications
- Good error messages with actionable guidance

## Implementation Details

### Dev/Prod Mode Pattern

**Dev Mode (default):**
```python
get_output_folder(Path("/out"), "My Model", dev_mode=True)
# => Path("/out/My Model_20260210T083257Z")
```
- Appends UTC timestamp to folder name
- Never conflicts with existing folders (new timestamp each run)
- Safe for iterative development

**Prod Mode:**
```python
get_output_folder(Path("/out"), "My Model", dev_mode=False)
# => Path("/out/My Model")
```
- Uses base model name (no timestamp)
- Raises FileExistsError if folder exists and overwrite=False
- Requires explicit overwrite=True for regeneration

### File Processing Logic

```python
for relative_path, content in files.items():
    full_path = folder_path / relative_path
    watermarked_content = add_watermark_to_content(relative_path, content, version, timestamp)

    if not full_path.exists():
        write_file_atomically(full_path, watermarked_content)
        written.append(relative_path)
    else:
        existing = full_path.read_text(encoding="utf-8")

        if existing == watermarked_content:
            unchanged.append(relative_path)  # Byte-identical, skip write
        elif is_auto_generated(existing):
            write_file_atomically(full_path, watermarked_content)
            written.append(relative_path)  # Overwrite auto-generated
        else:
            skipped.append(relative_path)  # Preserve manual files
```

### Directory Structure

```
ModelName_20260210T083257Z/
├── model.tmdl                    (triple-slash watermark)
├── definition.pbism              (_comment watermark)
├── definition.platform           (_comment watermark)
└── definition/
    ├── expressions.tmdl          (triple-slash watermark)
    ├── relationships.tmdl        (triple-slash watermark)
    └── tables/
        ├── DimCustomer.tmdl      (triple-slash watermark)
        └── FactSales.tmdl        (triple-slash watermark)
```

## Verification Results

- All 25 new tests pass
- All 274 existing tests still pass (299 total)
- ruff check: clean
- mypy typecheck: clean (21 source files)
- Code coverage: 100% for writer module

## Deviations from Plan

None. Plan executed exactly as written. All requirements met:
- ✅ get_output_folder correctly computes dev/prod paths
- ✅ write_tmdl_folder writes all files from dict to correct structure
- ✅ Every written file contains appropriate watermark
- ✅ Files with watermark are overwritten on regeneration
- ✅ Files without watermark are skipped and reported
- ✅ Files with identical content reported as unchanged
- ✅ Extra files on disk are not deleted
- ✅ Prod mode raises FileExistsError appropriately
- ✅ Prod mode proceeds when overwrite=True
- ✅ Dev mode always creates new timestamped folder
- ✅ Output directory created automatically via mkdir -p
- ✅ make check passes

## Key Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Dev mode as default | Safe iteration without conflicts | Prevents accidental overwrites during development |
| Timestamp format: YYYYMMDDTHHMMSSz | ISO compact, sortable, filesystem-safe | Easy to sort/filter folders by creation time |
| FileExistsError in prod mode | Explicit protection against data loss | Forces deliberate overwrite=True for regeneration |
| Byte-identical check before write | Avoid unnecessary disk I/O | Better performance, clearer changelog tracking |
| Non-destructive regeneration | Don't delete extra files | Preserves user-added documentation, scripts, etc. |
| Sorted WriteSummary lists | Deterministic output | Easier testing, consistent reporting |

## Files Created/Modified

### Source Code
- **src/semantic_model_generator/output/writer.py** (134 lines)
  - get_output_folder() - dev/prod mode path calculation
  - write_tmdl_folder() - main folder writing entry point with watermark preservation

- **src/semantic_model_generator/output/__init__.py** (modified)
  - Added exports: write_tmdl_folder, get_output_folder

### Tests
- **tests/output/test_writer.py** (518 lines)
  - 25 comprehensive tests covering all functionality
  - Test classes: TestGetOutputFolder (6 tests), TestWriteTmdlFolder (19 tests)

## Integration Points

**Provides:**
- Main output API for Phase 7 (REST deployment) and Phase 8 (CLI)
- get_output_folder() for path calculation with mode support
- write_tmdl_folder() for complete TMDL folder generation

**Consumes:**
- Phase 5 generate_all_tmdl() output (dict[str, str] of files)
- Plan 06-01 watermark functions and WriteSummary
- semantic_model_generator._version.__version__ (runtime version)

**Affects:**
- Phase 7: REST API will call write_tmdl_folder() with prod mode
- Phase 8: CLI will offer dev/prod mode flags for user control

## Test Coverage

| Category | Tests | Coverage |
|----------|-------|----------|
| get_output_folder | 6 | Dev/prod modes, timestamp handling, name preservation |
| Directory structure | 2 | Folder creation, definition/tables subdirectories |
| File writing | 4 | Dict-to-disk, watermark injection, format handling |
| Dev mode | 2 | Timestamped folders, no conflicts |
| Prod mode | 3 | Base name, FileExistsError, overwrite bypass |
| Watermark preservation | 5 | Skip manual files, overwrite auto-generated, reporting |
| WriteSummary | 2 | Correct categorization, sorted lists |
| Edge cases | 1 | Parent directory creation, extra files |
| **Total** | **25** | **100%** |

## Next Steps

Phase 6 is now complete. Both plans (06-01 watermark, 06-02 writer) delivered:
- Foundation: watermark generation, detection, atomic writes
- Core capability: folder writer with dev/prod modes and file preservation

**Ready for:**
- Phase 7: REST API deployment to Fabric (uses write_tmdl_folder with prod mode)
- Phase 8: CLI tool (exposes dev/prod modes to users)

## Self-Check: PASSED

Verified all claims:

**Files created:**
```bash
[FOUND] src/semantic_model_generator/output/writer.py
[FOUND] tests/output/test_writer.py
```

**Files modified:**
```bash
[FOUND] src/semantic_model_generator/output/__init__.py (exports added)
```

**Commits exist:**
```bash
[FOUND] 88ec731 - test(06-02): add failing tests for folder writer with dev/prod modes
[FOUND] 1ab2970 - feat(06-02): implement folder writer with dev/prod modes and watermark preservation
```

**Tests pass:**
```bash
299 passed in 4.72s (25 new tests in tests/output/test_writer.py)
```

**Quality checks:**
```bash
ruff check: ✓ All checks passed
mypy: ✓ Success: no issues found in 21 source files
pytest: ✓ 299 passed
```

**Key functionality verified:**
- ✅ Dev mode creates timestamped folders
- ✅ Prod mode uses base name with overwrite protection
- ✅ Watermarked files overwritten on regeneration
- ✅ Non-watermarked files preserved and reported as skipped
- ✅ Byte-identical files reported as unchanged
- ✅ Extra files not deleted (non-destructive)
- ✅ Proper directory structure created (definition/tables)
- ✅ All file formats watermarked correctly

All implementation claims verified against actual artifacts.
