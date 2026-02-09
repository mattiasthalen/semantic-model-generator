# Phase 5: TMDL Generation - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Generate complete, syntactically correct TMDL folder structure from schema metadata and inferred relationships. Output must be deterministic (byte-identical on regeneration) and suitable for Git version control. Includes all required files: database.tmdl, model.tmdl, expressions.tmdl, relationships.tmdl, per-table .tmdl files, .platform, definition.pbism, and diagram layout JSON.

</domain>

<decisions>
## Implementation Decisions

### File generation approach
- Use Python f-strings (no Jinja2 dependency)
- Break into helper functions per section: generate_columns(), generate_partition(), etc. - compose sections
- Create indent(level: int) helper function that returns tabs for clean indentation handling
- Validate all generated TMDL files using the whitespace validation helper from Phase 2 before returning

### Sorting & determinism
- **Tables**: Dimensions first, then facts (classification-based primary sort)
- **Within classification**: Sort by (schema_name, table_name) tuple - secondary sort keeps schemas grouped
- **Columns**: Key columns first, then remaining columns alphabetically by name
- **Relationships**: Active first, then inactive (sort by active flag as primary key, then by table names)

### Metadata files structure
- **.platform**: Match reference examples from TMDL spec or Fabric-generated models (all standard fields)
- **definition.pbism**: Full metadata structure including model name, description, version, author (if available), timestamps
- **Diagram layout**: Facts in left column, dimensions in rows above and below facts
- **Layout positioning**: Hardcoded algorithm (fixed spacing and positioning logic - simple, deterministic, not configurable)

### Expression & locale handling
- **expressions.tmdl**: Placeholder comments showing where custom expressions go (empty with locale definition)
- **Locale**: Hardcoded to en-US (no configuration needed)
- **Expression generation**: Leave expressions.tmdl minimal - users add their own DAX expressions manually (generator doesn't try to guess)
- **Model name**: Configurable parameter (user supplies model name explicitly, not derived from warehouse)

### Claude's Discretion
- Exact spacing values in diagram layout algorithm
- Error message formatting for validation failures
- Internal function signatures and organization within the module
- Test fixture data structure

</decisions>

<specifics>
## Specific Ideas

- "Facts to the left, in a column, dimension as a row above and below" - clear visual separation in diagram layout
- Validate using Phase 2's validation helper - ensures consistency with existing utilities
- Helper functions per section - promotes testability and composition

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 05-tmdl-generation*
*Context gathered: 2026-02-09*
