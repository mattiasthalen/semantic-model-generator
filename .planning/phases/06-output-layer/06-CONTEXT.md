# Phase 6: Output Layer - Context

**Gathered:** 2026-02-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Write generated TMDL to a folder on disk with watermark-based preservation of manually-maintained files. Supports dev mode (timestamped folders for safe iteration) and prod mode (base name with overwrite protection). REST API deployment is Phase 7; pipeline orchestration is Phase 8.

</domain>

<decisions>
## Implementation Decisions

### Watermark design
- Multi-line header block at the top of every generated file
- Includes generator name, version, and UTC timestamp
- Uses TMDL triple-slash comment syntax (`///`) for .tmdl files
- Detection: file is considered auto-generated if it contains the string `semantic-model-generator` in a comment line
- Non-TMDL files (.pbism, .json, .platform): Claude's discretion on comment syntax appropriate for each format

### Overwrite behavior
- Files with watermark are overwritten on regeneration
- Files without watermark are skipped (preserved) and included in summary as "skipped (manually maintained)"
- Removing the watermark is the intentional signal to protect a file from regeneration
- Extra files on disk that are NOT in the generated output set are left untouched (not deleted)
- Writer returns a summary data structure listing: files written, files skipped (manually maintained), files unchanged
- Output directory is created automatically (mkdir -p) if it doesn't exist

### Dev vs prod mode
- Dev mode is the default when caller doesn't specify
- Dev mode appends ISO compact timestamp suffix: `ModelName_20260210T120000Z`
- Each dev run creates a new folder; no automatic cleanup of old dev folders
- Prod mode writes to the base model name folder
- Prod mode requires explicit `overwrite=True` flag when folder already exists; errors otherwise

### Folder structure
- Writer accepts any user-provided output path (no default lakehouse assumption)
- Folder name uses the exact model name as provided, preserving case and spaces
- Internal structure matches Fabric's TMDL spec: `definition/` subdirectory for .tmdl files, `.pbism` and `.platform` at root level
- Writer accepts the Phase 5 `dict[str, str]` output directly (filename-to-content mapping)

### Claude's Discretion
- Comment syntax for watermark in non-TMDL files (.json, .pbism, .platform)
- Exact header block formatting and line count
- Summary data structure design (dataclass, TypedDict, etc.)
- Error messages for prod mode overwrite rejection

</decisions>

<specifics>
## Specific Ideas

- Watermark detection should be simple string containment, not regex — keep it predictable
- The summary should make it obvious what changed, so the caller can log or display it
- Folder structure should be deployable to Fabric as-is (definition/ subdirectory is critical)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-output-layer*
*Context gathered: 2026-02-10*
