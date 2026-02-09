# Phase 5: TMDL Generation - Research

**Researched:** 2026-02-09
**Domain:** TMDL file format generation, Microsoft Fabric semantic model structure, DirectLake partition syntax, file hierarchy generation
**Confidence:** HIGH

## Summary

Phase 5 requires generating a complete, syntactically correct TMDL folder structure from schema metadata and inferred relationships. The research confirms TMDL is a well-specified, YAML-like format with strict tab-based indentation, explicit file organization requirements, and deterministic serialization rules. Microsoft Fabric adds wrapper files (.platform, definition.pbism, diagramLayout.json) that enable Git integration and API deployment.

TMDL uses a standardized folder structure with one level of subfolders: database.tmdl and model.tmdl at root, plus subdirectories for tables/, roles/, perspectives/, and cultures/. Each table gets its own .tmdl file containing columns, partitions, measures, and hierarchies. Relationships are consolidated in relationships.tmdl at root level. The format requires tab indentation (never spaces), single-quote escaping for special characters in identifiers, and specific property delimiters (equals for expressions, colon for values).

DirectLake partitions use `mode: directLake` with entitySource pointing to SQL endpoints or OneLake storage. The entitySource includes workspace GUID, lakehouse/warehouse GUID, schema name, and entity (table) name. Fabric's .platform file (V2 format) contains logicalId, metadata type, displayName, and description. The definition.pbism file is base64-encoded metadata for Fabric integration. DiagramLayout.json positions tables visually in Power BI.

**Primary recommendation:** Use Python f-strings for template generation (no Jinja2), compose sections via helper functions (generate_columns, generate_partition, etc.), use existing indent_tmdl() and validate_tmdl_indentation() from Phase 2, apply deterministic sorting (dimensions before facts, alphabetical within classification), and generate complete file structure using pathlib with mkdir(parents=True, exist_ok=True).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**File generation approach:**
- Use Python f-strings (no Jinja2 dependency)
- Break into helper functions per section: generate_columns(), generate_partition(), etc. - compose sections
- Create indent(level: int) helper function that returns tabs for clean indentation handling
- Validate all generated TMDL files using the whitespace validation helper from Phase 2 before returning

**Sorting & determinism:**
- **Tables**: Dimensions first, then facts (classification-based primary sort)
- **Within classification**: Sort by (schema_name, table_name) tuple - secondary sort keeps schemas grouped
- **Columns**: Key columns first, then remaining columns alphabetically by name
- **Relationships**: Active first, then inactive (sort by active flag as primary key, then by table names)

**Metadata files structure:**
- **.platform**: Match reference examples from TMDL spec or Fabric-generated models (all standard fields)
- **definition.pbism**: Full metadata structure including model name, description, version, author (if available), timestamps
- **Diagram layout**: Facts in left column, dimensions in rows above and below facts
- **Layout positioning**: Hardcoded algorithm (fixed spacing and positioning logic - simple, deterministic, not configurable)

**Expression & locale handling:**
- **expressions.tmdl**: Placeholder comments showing where custom expressions go (empty with locale definition)
- **Locale**: Hardcoded to en-US (no configuration needed)
- **Expression generation**: Leave expressions.tmdl minimal - users add their own DAX expressions manually (generator doesn't try to guess)
- **Model name**: Configurable parameter (user supplies model name explicitly, not derived from warehouse)

### Claude's Discretion

- Exact spacing values in diagram layout algorithm
- Error message formatting for validation failures
- Internal function signatures and organization within the module
- Test fixture data structure

### Deferred Ideas (OUT OF SCOPE)

None - discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python f-strings (stdlib) | 3.11+ | Template generation for TMDL files | Built-in, no dependencies, clean syntax, easy to test, composes naturally with helper functions |
| pathlib (stdlib) | 3.11+ | File hierarchy generation | Modern Python path handling, cross-platform, mkdir(parents=True, exist_ok=True) for nested directories |
| json (stdlib) | 3.11+ | diagramLayout.json and definition.pbism generation | Built-in JSON serialization with deterministic ordering |
| base64 (stdlib) | 3.11+ | Encoding definition.pbism for Fabric API | Required by Fabric REST API definition structure |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Existing utils from Phase 2 | - | indent_tmdl(), validate_tmdl_indentation(), quote_tmdl_identifier() | All TMDL generation - reuse tested utilities |
| Existing uuid_gen from Phase 2 | - | Deterministic UUIDs for table lineage tags | Every table needs unique lineageTag for Fabric tracking |
| Existing type_mapping from Phase 2 | - | SQL to TMDL data type conversion | Every column needs dataType property |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python f-strings | Jinja2 template engine | Jinja2 adds dependency and learning curve; f-strings sufficient for structured output with clear composition |
| pathlib | os.path module | os.path is lower-level string manipulation; pathlib object-oriented API cleaner, more maintainable |
| Helper function composition | Single monolithic template | Monolithic templates hard to test and modify; composed helpers promote reusability and testability |
| Hardcoded JSON strings | JSON template files | Template files add indirection; hardcoded JSON with variables keeps structure visible and testable |

**Installation:**
```bash
# No external dependencies needed - all stdlib
python --version  # Ensure >= 3.11
```

## Architecture Patterns

### Recommended Project Structure
```
src/semantic_model_generator/
├── generation/              # NEW - TMDL generation module
│   ├── __init__.py
│   ├── tmdl.py             # Main generation orchestrator
│   ├── database.py         # database.tmdl generation
│   ├── model.py            # model.tmdl generation
│   ├── expressions.py      # expressions.tmdl generation
│   ├── tables.py           # Table .tmdl generation
│   ├── relationships.py    # relationships.tmdl generation
│   ├── metadata.py         # .platform, definition.pbism generation
│   └── diagram.py          # diagramLayout.json generation
├── domain/                  # Existing
│   └── types.py            # TableMetadata, Relationship types
└── utils/                   # Existing from Phase 2
    ├── whitespace.py       # indent_tmdl(), validate_tmdl_indentation()
    ├── identifiers.py      # quote_tmdl_identifier()
    ├── type_mapping.py     # map_sql_type_to_tmdl()
    └── uuid_gen.py         # generate_deterministic_uuid()
```

### Pattern 1: Composed Helper Functions for Section Generation
**What:** Break TMDL file generation into testable helper functions that return strings, compose them in parent functions
**When to use:** All TMDL file generation - database, model, tables, relationships
**Example:**
```python
# Source: User decision from CONTEXT.md
from semantic_model_generator.utils.whitespace import indent_tmdl
from semantic_model_generator.utils.identifiers import quote_tmdl_identifier
from semantic_model_generator.domain.types import ColumnMetadata

def generate_column_definition(column: ColumnMetadata, level: int) -> str:
    """Generate TMDL column definition section.

    Args:
        column: Column metadata from Phase 3 discovery
        level: Indentation level (typically 1 for table contents)

    Returns:
        TMDL column definition with properties
    """
    indent = indent_tmdl(level)
    quoted_name = quote_tmdl_identifier(column.name)
    data_type = map_sql_type_to_tmdl(column.sql_type)

    # Build column definition line by line
    lines = [f"{indent}column {quoted_name}"]
    lines.append(f"{indent}\tdataType: {data_type.value}")
    lines.append(f"{indent}\tsourceColumn: {column.name}")

    if not column.is_nullable:
        lines.append(f"{indent}\tisNullable: false")

    return "\n".join(lines)

def generate_columns_section(columns: tuple[ColumnMetadata, ...]) -> str:
    """Generate all column definitions for a table.

    Per user decision: Key columns first, then alphabetical.
    """
    # Separate key columns from regular columns
    key_cols = [col for col in columns if is_key_column(col)]
    regular_cols = [col for col in columns if not is_key_column(col)]

    # Sort each group
    key_cols_sorted = sorted(key_cols, key=lambda c: c.name)
    regular_cols_sorted = sorted(regular_cols, key=lambda c: c.name)

    # Generate each column
    all_cols = key_cols_sorted + regular_cols_sorted
    column_defs = [generate_column_definition(col, level=1) for col in all_cols]

    return "\n\n".join(column_defs)
```

**Benefits:**
- Each helper is independently testable with clear inputs/outputs
- Easy to validate individual sections with Phase 2's whitespace validator
- Composition pattern mirrors TMDL's nested structure
- Changes to one section don't affect others

### Pattern 2: DirectLake Partition with EntitySource
**What:** Generate DirectLake partition definition referencing SQL endpoint entity
**When to use:** Every table needs exactly one partition in DirectLake mode
**Example:**
```python
# Based on: https://docs.tabulareditor.com/common/Semantic%20Model/direct-lake-sql-model.html
from semantic_model_generator.utils.whitespace import indent_tmdl

def generate_directlake_partition(
    schema_name: str,
    table_name: str,
    workspace_id: str,
    warehouse_id: str
) -> str:
    """Generate DirectLake partition definition for SQL endpoint.

    DirectLake partitions have:
    - mode: directLake
    - entitySource with workspace/warehouse IDs, schema, entity name

    Args:
        schema_name: Source schema (e.g., "dbo")
        table_name: Source table (e.g., "FactSales")
        workspace_id: Fabric workspace GUID
        warehouse_id: Fabric warehouse GUID

    Returns:
        TMDL partition definition
    """
    indent1 = indent_tmdl(1)
    indent2 = indent_tmdl(2)

    # DirectLake partition structure
    partition_tmdl = f"""{indent1}partition {table_name} = entity
{indent2}mode: directLake
{indent2}source =
{indent2}\tworkspaceId: {workspace_id}
{indent2}\tlakehouseId: {warehouse_id}
{indent2}\tschemaName: {schema_name}
{indent2}\tentityName: {table_name}"""

    return partition_tmdl
```

**Key points:**
- `mode: directLake` indicates Direct Lake storage mode
- entitySource references SQL endpoint by GUIDs (workspace, warehouse)
- schemaName and entityName match source warehouse structure
- No M expression needed (unlike Import mode partitions)

### Pattern 3: Deterministic Collection Sorting for Git Stability
**What:** Apply stable, deterministic sorting to all collections before generation
**When to use:** Tables, columns, relationships - anything serialized to TMDL
**Example:**
```python
# Based on: User decision from CONTEXT.md + https://docs.python.org/3/howto/sorting.html
from semantic_model_generator.domain.types import TableMetadata, TableClassification

def sort_tables_for_generation(
    tables: tuple[TableMetadata, ...],
    classifications: dict[tuple[str, str], TableClassification]
) -> list[TableMetadata]:
    """Sort tables deterministically for TMDL generation.

    Per user decision:
    1. Dimensions first, then facts
    2. Within classification: alphabetical by (schema_name, table_name)

    Python's sort is stable, so secondary sort preserves schema grouping.
    """
    def sort_key(table: TableMetadata) -> tuple:
        # Get classification for this table
        table_key = (table.schema_name, table.table_name)
        classification = classifications.get(table_key, TableClassification.UNCLASSIFIED)

        # Primary sort: dimension=0, fact=1, unclassified=2
        classification_order = {
            TableClassification.DIMENSION: 0,
            TableClassification.FACT: 1,
            TableClassification.UNCLASSIFIED: 2
        }

        # Return tuple for multi-key sorting
        return (
            classification_order[classification],  # Primary: classification
            table.schema_name,                     # Secondary: schema
            table.table_name                       # Tertiary: table name
        )

    return sorted(tables, key=sort_key)
```

**Benefits:**
- Stable sort guarantees deterministic output across runs (REQ-33)
- Tuple sort keys enable multi-level sorting (classification, schema, table)
- Dimensions appear before facts in folder structure (conventional order)
- Schema grouping preserved within each classification

### Pattern 4: TMDL File Structure Generation with pathlib
**What:** Create nested directory structure using pathlib's mkdir with parents=True
**When to use:** When writing TMDL folder structure to disk
**Example:**
```python
# Based on: https://docs.python.org/3/library/pathlib.html
from pathlib import Path

def write_tmdl_structure(
    output_path: Path,
    database_tmdl: str,
    model_tmdl: str,
    tables_tmdl: dict[str, str],  # table_name -> tmdl content
    relationships_tmdl: str,
    expressions_tmdl: str
) -> None:
    """Write complete TMDL folder structure to disk.

    Creates:
    output_path/
    ├── database.tmdl
    ├── model.tmdl
    ├── expressions.tmdl
    ├── relationships.tmdl
    ├── tables/
    │   ├── Table1.tmdl
    │   ├── Table2.tmdl
    │   └── ...
    ├── .platform
    └── definition.pbism
    """
    # Create root directory if needed
    output_path.mkdir(parents=True, exist_ok=True)

    # Write root-level files
    (output_path / "database.tmdl").write_text(database_tmdl, encoding="utf-8")
    (output_path / "model.tmdl").write_text(model_tmdl, encoding="utf-8")
    (output_path / "expressions.tmdl").write_text(expressions_tmdl, encoding="utf-8")
    (output_path / "relationships.tmdl").write_text(relationships_tmdl, encoding="utf-8")

    # Create tables subdirectory
    tables_dir = output_path / "tables"
    tables_dir.mkdir(exist_ok=True)

    # Write table files (deterministically ordered)
    for table_name in sorted(tables_tmdl.keys()):
        table_file = tables_dir / f"{table_name}.tmdl"
        table_file.write_text(tables_tmdl[table_name], encoding="utf-8")
```

**Benefits:**
- pathlib handles cross-platform path separators automatically
- mkdir(parents=True, exist_ok=True) creates nested dirs without errors
- Path / operator makes path joining readable
- write_text() handles encoding consistently

### Pattern 5: Validation Before Return
**What:** Validate all generated TMDL content with Phase 2's whitespace validator before returning
**When to use:** All TMDL generation functions - validate before writing or returning
**Example:**
```python
# Based on: User decision from CONTEXT.md + existing Phase 2 utils
from semantic_model_generator.utils.whitespace import validate_tmdl_indentation

def generate_table_tmdl(table: TableMetadata, partition: str, columns: str) -> str:
    """Generate complete table TMDL file.

    Validates output before returning to catch indentation errors early.
    """
    table_name_quoted = quote_tmdl_identifier(table.table_name)
    lineage_tag = generate_deterministic_uuid("table", f"{table.schema_name}.{table.table_name}")

    # Compose table file from sections
    tmdl_content = f"""table {table_name_quoted}
\tlineageTag: {lineage_tag}

{partition}

{columns}
"""

    # Validate before returning (per user decision)
    errors = validate_tmdl_indentation(tmdl_content)
    if errors:
        # Format errors for clear failure message
        error_messages = [f"Line {e.line_number}: {e.message}" for e in errors]
        raise ValueError(
            f"Generated TMDL has indentation errors:\n" + "\n".join(error_messages)
        )

    return tmdl_content
```

**Benefits:**
- Early error detection prevents invalid TMDL from reaching file system
- Reuses tested validation from Phase 2 (no duplicate logic)
- Clear error messages point to specific line numbers
- Validates composition of helper function outputs

### Anti-Patterns to Avoid
- **Monolithic template strings:** Hard to test, debug, and modify; use composed helper functions
- **Mixing spaces and tabs:** TMDL requires tabs only; always use indent_tmdl() helper
- **Non-deterministic ordering:** Random iteration order breaks REQ-33; always sort before serialization
- **Hardcoded indentation strings:** Use indent_tmdl(level) not "\t\t"; centralizes indentation logic
- **Unvalidated output:** Always validate with Phase 2 validator before writing; catches errors early
- **Path string concatenation:** Use pathlib's / operator not string joining; avoids separator issues

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tab indentation generation | `"\t" * level` in every function | indent_tmdl() from Phase 2 | Centralized, tested, consistent across codebase |
| Identifier quoting | Manual single-quote escaping | quote_tmdl_identifier() from Phase 2 | Handles edge cases (nested quotes, special chars) correctly |
| SQL to TMDL type mapping | Inline type conversion | map_sql_type_to_tmdl() from Phase 2 | Complete mapping verified against MS docs |
| Whitespace validation | Manual space/tab detection | validate_tmdl_indentation() from Phase 2 | Tested, structured error reporting |
| Deterministic UUIDs | Random UUIDs or custom hashing | generate_deterministic_uuid() from Phase 2 | RFC-compliant, stable, REQ-12 compliance |
| Path handling | String concatenation with os.sep | pathlib Path objects | Cross-platform, safer, more readable |
| JSON serialization | Manual JSON string building | json.dumps() with sort_keys=True | Proper escaping, deterministic key ordering |
| Base64 encoding | Custom encoding logic | base64.b64encode() from stdlib | Standard encoding, Fabric API compatible |

**Key insight:** Phase 2 already built tested utilities for TMDL syntax (indentation, quoting, validation, type mapping). Phase 5 should compose these utilities into higher-level generation functions, not rebuild basic TMDL handling. Focus on orchestration and file structure, not low-level syntax.

## Common Pitfalls

### Pitfall 1: F-String Expression Complexity
**What goes wrong:** Nested f-strings with complex expressions become unreadable, hard to debug
**Why it happens:** Temptation to inline complex logic directly in template strings
**How to avoid:** Extract complex expressions into variables before f-string, keep templates simple
**Warning signs:** F-strings with nested conditionals, multiple method calls, or hard-to-follow logic
```python
# WRONG - complex logic inline
tmdl = f"""{indent_tmdl(1)}column {quote_tmdl_identifier(col.name)}
{indent_tmdl(2)}dataType: {map_sql_type_to_tmdl(col.sql_type).value if col.sql_type else 'string'}
{indent_tmdl(2)}isNullable: {'false' if not col.is_nullable and col.sql_type != 'bit' else 'true'}"""

# CORRECT - extract logic first
quoted_name = quote_tmdl_identifier(col.name)
data_type = map_sql_type_to_tmdl(col.sql_type).value
is_nullable = "false" if not col.is_nullable else "true"

tmdl = f"""{indent_tmdl(1)}column {quoted_name}
{indent_tmdl(2)}dataType: {data_type}
{indent_tmdl(2)}isNullable: {is_nullable}"""
```

### Pitfall 2: Incorrect TMDL Property Delimiter Usage
**What goes wrong:** Using equals (=) for non-expression properties or colon (:) for expressions
**Why it happens:** TMDL has two delimiters with specific rules that are easy to mix up
**How to avoid:** Remember: equals (=) for expressions and object defaults, colon (:) for all other properties
**Warning signs:** TMDL parser errors on valid-looking syntax, Fabric rejects model definition
```python
# WRONG - delimiter confusion
tmdl = f"""column Amount
\tdataType = double        # Should use colon
\texpression: SUM(...)     # Should use equals
"""

# CORRECT - proper delimiters
tmdl = f"""column Amount
\tdataType: double          # Colon for properties
\texpression = SUM(...)     # Equals for expressions
"""
```

### Pitfall 3: Non-Deterministic Dictionary Iteration
**What goes wrong:** Iterating over dict.items() in random order produces different TMDL output each run
**Why it happens:** Python dicts maintain insertion order (3.7+) but not sorted order
**How to avoid:** Always sort dict keys before iteration when generating TMDL
**Warning signs:** git diff shows table/column order changes between runs, REQ-33 tests fail
```python
# WRONG - non-deterministic order
for table_name, table_tmdl in tables_dict.items():
    write_table_file(table_name, table_tmdl)

# CORRECT - deterministic sorted order
for table_name in sorted(tables_dict.keys()):
    write_table_file(table_name, tables_dict[table_name])
```

### Pitfall 4: Forgetting lineageTag on Tables
**What goes wrong:** Fabric Git integration fails or produces errors when lineageTag is missing
**Why it happens:** lineageTag is not required by TMDL spec but is required by Fabric
**How to avoid:** Always generate lineageTag using deterministic UUID for every table
**Warning signs:** Fabric API rejects model, Git integration shows errors, round-trip fails
```python
# WRONG - missing lineageTag
tmdl = f"""table Sales
\tcolumn Amount
\t\tdataType: double
"""

# CORRECT - include lineageTag
lineage_tag = generate_deterministic_uuid("table", f"{schema}.{table_name}")
tmdl = f"""table Sales
\tlineageTag: {lineage_tag}

\tcolumn Amount
\t\tdataType: double
"""
```

### Pitfall 5: Incorrect Base64 Encoding for definition.pbism
**What goes wrong:** Fabric REST API rejects definition.pbism with encoding errors
**Why it happens:** Using wrong encoding (UTF-16 instead of UTF-8) or forgetting to decode bytes
**How to avoid:** Use UTF-8 encoding, base64.b64encode(), decode to string for JSON
**Warning signs:** Fabric API returns 400 errors, definition.pbism can't be decoded
```python
# WRONG - encoding issues
content = json.dumps(pbism_dict)
encoded = base64.b64encode(content)  # Returns bytes, not string

# CORRECT - proper encoding
content = json.dumps(pbism_dict)
encoded_bytes = base64.b64encode(content.encode('utf-8'))
encoded_string = encoded_bytes.decode('ascii')  # Base64 is ASCII-safe
```

### Pitfall 6: Hardcoded Workspace/Warehouse GUIDs
**What goes wrong:** Generated TMDL only works in one environment, not portable
**Why it happens:** GUIDs embedded in generation code instead of passed as parameters
**How to avoid:** Always accept workspace_id and warehouse_id as function parameters
**Warning signs:** TMDL works locally but fails when deployed to different workspace
```python
# WRONG - hardcoded GUIDs
def generate_partition(schema: str, table: str) -> str:
    workspace_id = "12345678-1234-1234-1234-123456789abc"  # Hardcoded!
    warehouse_id = "87654321-4321-4321-4321-cba987654321"  # Hardcoded!
    ...

# CORRECT - parameterized GUIDs
def generate_partition(
    schema: str,
    table: str,
    workspace_id: str,
    warehouse_id: str
) -> str:
    # Use passed parameters
    ...
```

### Pitfall 7: Missing Validation After Composition
**What goes wrong:** Individual helper functions generate valid TMDL but composition produces invalid indentation
**Why it happens:** Composing sections with incorrect indentation levels or missing newlines
**How to avoid:** Validate composed output with validate_tmdl_indentation() before returning
**Warning signs:** Helper function tests pass but integration tests fail with indentation errors
```python
# WRONG - no validation after composition
def generate_table(table: TableMetadata) -> str:
    columns = generate_columns_section(table.columns)
    partition = generate_partition_section(table)

    # Compose without validation
    return f"table {table.table_name}\n{partition}\n{columns}"

# CORRECT - validate composed output
def generate_table(table: TableMetadata) -> str:
    columns = generate_columns_section(table.columns)
    partition = generate_partition_section(table)

    tmdl_content = f"table {table.table_name}\n{partition}\n{columns}"

    # Validate before returning (per user decision)
    errors = validate_tmdl_indentation(tmdl_content)
    if errors:
        raise ValueError(f"Indentation errors: {errors}")

    return tmdl_content
```

## Code Examples

Verified patterns from official sources and project conventions:

### Complete Table TMDL Generation
```python
# Based on: https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview
from semantic_model_generator.domain.types import TableMetadata, ColumnMetadata
from semantic_model_generator.utils.whitespace import indent_tmdl, validate_tmdl_indentation
from semantic_model_generator.utils.identifiers import quote_tmdl_identifier
from semantic_model_generator.utils.type_mapping import map_sql_type_to_tmdl
from semantic_model_generator.utils.uuid_gen import generate_deterministic_uuid

def generate_table_tmdl(
    table: TableMetadata,
    workspace_id: str,
    warehouse_id: str,
    key_prefixes: tuple[str, ...]
) -> str:
    """Generate complete TMDL file for a table.

    Per user decision: Compose from helper functions, validate before return.
    """
    # Generate sections
    table_name_quoted = quote_tmdl_identifier(table.table_name)
    lineage_tag = generate_deterministic_uuid("table", f"{table.schema_name}.{table.table_name}")

    partition_section = generate_directlake_partition(
        table.schema_name,
        table.table_name,
        workspace_id,
        warehouse_id
    )

    columns_section = generate_columns_section(table.columns, key_prefixes)

    # Compose table file
    tmdl_content = f"""table {table_name_quoted}
\tlineageTag: {lineage_tag}

{partition_section}

{columns_section}
"""

    # Validate per user decision
    errors = validate_tmdl_indentation(tmdl_content)
    if errors:
        error_msgs = [f"Line {e.line_number}: {e.message}" for e in errors]
        raise ValueError(
            f"TMDL validation failed for table {table.table_name}:\n" +
            "\n".join(error_msgs)
        )

    return tmdl_content

def generate_columns_section(
    columns: tuple[ColumnMetadata, ...],
    key_prefixes: tuple[str, ...]
) -> str:
    """Generate all column definitions with deterministic ordering.

    Per user decision: Key columns first, then alphabetical.
    """
    # Separate and sort
    key_cols = [c for c in columns if any(c.name.startswith(p) for p in key_prefixes)]
    regular_cols = [c for c in columns if c not in key_cols]

    sorted_keys = sorted(key_cols, key=lambda c: c.name)
    sorted_regular = sorted(regular_cols, key=lambda c: c.name)

    all_columns = sorted_keys + sorted_regular

    # Generate each column
    column_defs = []
    for col in all_columns:
        col_def = generate_column_definition(col)
        column_defs.append(col_def)

    return "\n\n".join(column_defs)

def generate_column_definition(column: ColumnMetadata) -> str:
    """Generate single column definition."""
    indent1 = indent_tmdl(1)
    indent2 = indent_tmdl(2)

    quoted_name = quote_tmdl_identifier(column.name)
    data_type = map_sql_type_to_tmdl(column.sql_type)

    lines = [f"{indent1}column {quoted_name}"]
    lines.append(f"{indent2}dataType: {data_type.value}")
    lines.append(f"{indent2}sourceColumn: {column.name}")
    lines.append(f"{indent2}summarizeBy: none")

    return "\n".join(lines)

def generate_directlake_partition(
    schema_name: str,
    table_name: str,
    workspace_id: str,
    warehouse_id: str
) -> str:
    """Generate DirectLake partition for SQL endpoint."""
    indent1 = indent_tmdl(1)
    indent2 = indent_tmdl(2)
    indent3 = indent_tmdl(3)

    return f"""{indent1}partition {table_name} = entity
{indent2}mode: directLake
{indent2}source =
{indent3}workspaceId: {workspace_id}
{indent3}lakehouseId: {warehouse_id}
{indent3}schemaName: {schema_name}
{indent3}entityName: {table_name}"""
```

### Relationships TMDL Generation
```python
# Based on: https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview
from semantic_model_generator.domain.types import Relationship

def generate_relationships_tmdl(relationships: tuple[Relationship, ...]) -> str:
    """Generate relationships.tmdl file with all relationships.

    Per user decision: Active first, then inactive, sorted by table names.
    """
    # Sort per user decision: active first, then by table names
    sorted_rels = sorted(
        relationships,
        key=lambda r: (
            not r.is_active,      # False (active) before True (inactive)
            r.from_table,
            r.to_table,
            r.from_column
        )
    )

    # Generate each relationship
    rel_defs = [generate_relationship_definition(rel) for rel in sorted_rels]

    return "\n\n".join(rel_defs)

def generate_relationship_definition(rel: Relationship) -> str:
    """Generate single relationship definition."""
    indent1 = indent_tmdl(1)

    # Format qualified column references
    from_ref = f"{rel.from_table}.{quote_tmdl_identifier(rel.from_column)}"
    to_ref = f"{rel.to_table}.{quote_tmdl_identifier(rel.to_column)}"

    # TMDL uses lowercase true/false
    is_active_str = "true" if rel.is_active else "false"

    return f"""relationship {rel.id}
{indent1}fromColumn: {from_ref}
{indent1}toColumn: {to_ref}
{indent1}isActive: {is_active_str}
{indent1}crossFilteringBehavior: {rel.cross_filtering_behavior}
{indent1}fromCardinality: {rel.from_cardinality}
{indent1}toCardinality: {rel.to_cardinality}"""
```

### .platform File Generation (Fabric V2 Format)
```python
# Based on: https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format
import json

def generate_platform_file(
    model_name: str,
    description: str = ""
) -> str:
    """Generate .platform file for Fabric Git integration.

    Uses V2 format with combined config and metadata.
    Per user decision: All standard fields included.
    """
    # Generate logical ID (deterministic UUID for model)
    logical_id = generate_deterministic_uuid("model", model_name)

    platform_dict = {
        "version": "2.0",
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/platform/platformProperties.json",
        "config": {
            "logicalId": str(logical_id)
        },
        "metadata": {
            "type": "SemanticModel",
            "displayName": model_name,
            "description": description
        }
    }

    # Deterministic JSON with sorted keys (REQ-33)
    return json.dumps(platform_dict, indent=2, sort_keys=True, ensure_ascii=False)
```

### definition.pbism Generation
```python
# Based on: https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition
import json
from datetime import datetime, timezone

def generate_definition_pbism(
    model_name: str,
    description: str = "",
    author: str | None = None
) -> str:
    """Generate definition.pbism metadata file.

    Per user decision: Include model name, description, version, author, timestamps.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    pbism_dict = {
        "version": "1.0",
        "name": model_name,
        "description": description,
        "author": author or "semantic-model-generator",
        "createdDate": now_iso,
        "modifiedDate": now_iso,
        "compatibilityLevel": 1567  # SQL Server 2019 / Power BI
    }

    # Deterministic JSON with sorted keys
    return json.dumps(pbism_dict, indent=2, sort_keys=True, ensure_ascii=False)
```

### Diagram Layout JSON Generation
```python
# Based on: User decision from CONTEXT.md
import json
from semantic_model_generator.domain.types import TableMetadata, TableClassification

def generate_diagram_layout(
    tables: tuple[TableMetadata, ...],
    classifications: dict[tuple[str, str], TableClassification]
) -> str:
    """Generate diagramLayout.json for Power BI visual layout.

    Per user decision: Facts in left column, dimensions in rows above/below.
    Hardcoded spacing algorithm (not configurable).
    """
    # Separate by classification
    facts = [
        t for t in tables
        if classifications.get((t.schema_name, t.table_name)) == TableClassification.FACT
    ]
    dimensions = [
        t for t in tables
        if classifications.get((t.schema_name, t.table_name)) == TableClassification.DIMENSION
    ]

    # Sort each group deterministically
    facts_sorted = sorted(facts, key=lambda t: (t.schema_name, t.table_name))
    dims_sorted = sorted(dimensions, key=lambda t: (t.schema_name, t.table_name))

    # Layout algorithm (hardcoded per user decision)
    FACT_X = 100        # Left column for facts
    DIM_X = 500         # Right area for dimensions
    Y_SPACING = 200     # Vertical spacing between tables
    START_Y = 100       # Starting Y position

    nodes = []

    # Position facts in left column
    for i, fact in enumerate(facts_sorted):
        qualified_name = f"[{fact.schema_name}].[{fact.table_name}]"
        nodes.append({
            "table": qualified_name,
            "x": FACT_X,
            "y": START_Y + (i * Y_SPACING)
        })

    # Position dimensions in right area (row layout)
    for i, dim in enumerate(dims_sorted):
        qualified_name = f"[{dim.schema_name}].[{dim.table_name}]"
        nodes.append({
            "table": qualified_name,
            "x": DIM_X,
            "y": START_Y + (i * Y_SPACING)
        })

    layout_dict = {
        "version": "1.0",
        "nodes": nodes
    }

    # Deterministic JSON
    return json.dumps(layout_dict, indent=2, sort_keys=True, ensure_ascii=False)
```

### expressions.tmdl Generation (Minimal with Locale)
```python
# Based on: User decision from CONTEXT.md
def generate_expressions_tmdl(locale: str = "en-US") -> str:
    """Generate expressions.tmdl with locale and placeholder comments.

    Per user decision: Minimal, users add their own DAX expressions manually.
    Locale hardcoded to en-US (no configuration needed).
    """
    return f"""/// This file is for DAX expressions and calculated measures.
/// Add your custom DAX expressions here.

ref culture {locale}
"""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TMSL (JSON monolith) | TMDL (modular text files) | 2023 (TMDL GA) | Git-friendly, human-readable, easier collaboration |
| Manual JSON string building | F-strings with composition | Python 3.6+ (f-strings) | Cleaner syntax, better readability, easier testing |
| os.path string manipulation | pathlib object-oriented API | Python 3.4+ | Cross-platform, safer, more maintainable |
| Random/manual UUIDs | Deterministic uuid5 | Modern practice | Stable git diffs, reproducible output (REQ-12, REQ-33) |
| Jinja2 for code generation | F-strings with helpers | Simplification trend | No external deps, less abstraction, clearer data flow |
| Import mode | DirectLake mode | Fabric 2023+ | No data copy, real-time queries, better performance |

**Deprecated/outdated:**
- **TMSL JSON format for version control:** TMDL replaces TMSL for Git workflows; JSON is still valid but not Git-friendly
- **Jinja2 for simple templates:** F-strings sufficient for structured output with helpers; Jinja2 adds unnecessary dependency
- **os.path.join():** pathlib is modern standard; os.path kept for backward compatibility only
- **Non-deterministic collection ordering:** Modern tools expect stable diffs; REQ-33 requires deterministic output

## Open Questions

1. **DirectLake partition property completeness**
   - What we know: Mode, entitySource with workspace/warehouse/schema/entity required
   - What's unclear: Are there additional DirectLake-specific properties needed for Fabric compatibility?
   - Recommendation: Start with minimal required properties (mode, entitySource). Validate against Fabric API in integration tests. Add properties as needed based on Fabric API errors.

2. **Table ordering convention**
   - What we know: User decided dimensions first, facts second
   - What's unclear: Within TMDL `ref` statements in model.tmdl, should tables be listed in same order?
   - Recommendation: Apply same ordering (dimensions, then facts, alphabetical within each) to ref statements for consistency.

3. **Column summarization defaults**
   - What we know: Columns need summarizeBy property
   - What's unclear: Should numeric columns default to "sum" or "none"? Should dimension keys always be "none"?
   - Recommendation: Default all to "none" (no automatic aggregation). Users can change in Power BI if needed. Safer default than auto-summing.

4. **Relationship naming convention**
   - What we know: TMDL allows named relationships or UUID-only
   - What's unclear: Should relationships have human-readable names or just UUIDs?
   - Recommendation: Use UUID only (deterministic via uuid_gen). Human names add complexity without benefit for generated models.

## Sources

### Primary (HIGH confidence)
- [TMDL Overview - Microsoft Learn](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025) - Complete TMDL specification
- [TMDL How-To - Microsoft Learn](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-how-to?view=sql-analysis-services-2025) - TMDL file structure examples
- [Fabric Git Source Code Format - Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/source-code-format) - .platform file V2 structure
- [SemanticModel Definition - Fabric REST API](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition) - definition.pbism structure, required parts
- [Power BI Desktop Project Semantic Model Folder](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset) - Complete PBIP structure
- [Direct Lake Overview - Microsoft Learn](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview) - DirectLake mode fundamentals
- [Python pathlib Documentation](https://docs.python.org/3/library/pathlib.html) - Path object API
- [Python F-Strings Documentation](https://docs.python.org/3/reference/lexical_analysis.html#f-strings) - F-string syntax reference
- [Python Sorting How-To](https://docs.python.org/3/howto/sorting.html) - Stable sorting with sort keys

### Secondary (MEDIUM confidence)
- [Tabular Editor: Direct Lake on SQL Semantic Models](https://docs.tabulareditor.com/common/Semantic%20Model/direct-lake-sql-model.html) - DirectLake entitySource examples
- [TMDL Visual Studio Code Extension GA Announcement](https://powerbi.microsoft.com/en-us/blog/tmdl-visual-studio-code-extension-generally-available/) - TMDL tooling ecosystem
- [Python Multiline F-String Guide - CodeRivers](https://coderivers.org/blog/python-multiline-f-string/) - Multiline f-string patterns
- [Real Python: Python F-Strings Guide](https://realpython.com/python-f-strings/) - F-string best practices
- [Real Python: Python's pathlib Module](https://realpython.com/python-pathlib/) - pathlib usage patterns
- [Data Mozart: Direct Lake Models - OneLake or SQL?](https://data-mozart.com/direct-lake-models-are-they-onelake-or-sql-and-how-to-check/) - DirectLake connection patterns
- [Side Quests: Parameters for Direct Lake Semantic Model](https://sidequests.blog/2025/10/26/parameters-for-your-direct-lake-semantic-model/) - DirectLake configuration
- [Everything about PBIP Files - biSmart Blog](https://blog.bismart.com/en/power-bi-pbip-files) - PBIP structure overview
- [Medium: Understanding TMDL in Power BI](https://community.fabric.microsoft.com/t5/Power-BI-Community-Blog/Understanding-TMDL-in-Power-BI-A-Game-Changer-for-Data-Modeling/ba-p/4423323) - TMDL practical usage

### Tertiary (LOW confidence - general guidance)
- Various Power BI Community forum posts on TMDL structure - Cross-verified with official docs
- GitHub discussions on PBIP file formats - Anecdotal examples, verified with MS Learn

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib, user decisions clear, patterns align with existing project
- TMDL syntax: HIGH - Official Microsoft Learn specification comprehensive and detailed
- File structure: HIGH - Fabric Git format and REST API documentation explicit about required files
- DirectLake partitions: MEDIUM - Documentation exists but sparse on entitySource properties; may need validation
- Diagram layout: MEDIUM - User decision provides algorithm, but JSON schema not fully documented by Microsoft
- F-string composition: HIGH - Stdlib feature, well-documented, common pattern in modern Python

**Research date:** 2026-02-09
**Valid until:** 2026-04-09 (60 days - TMDL specification mature and stable, Fabric format V2 established)
