# Architecture Research

**Domain:** Python TMDL Semantic Model Generator for Microsoft Fabric
**Researched:** 2026-02-09
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PUBLIC API LAYER                          │
│  ┌────────────────────────────────────────────────────┐     │
│  │  generate_semantic_model(metadata, config, ...)    │     │
│  └────────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                  PIPELINE ORCHESTRATION                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Connect │→ │ Classify│→ │ Infer   │→ │Generate │        │
│  │ Schema  │  │ Tables  │  │ Rels    │  │ TMDL    │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
├─────────────────────────────────────────────────────────────┤
│                  CORE TRANSFORM FUNCTIONS                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Schema Read  │  │Relationship  │  │TMDL Template │      │
│  │ & Filter     │  │Inference     │  │Generation    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                  DOMAIN LOGIC FUNCTIONS                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Type Map  │  │Key Match │  │Table     │  │Watermark │   │
│  │          │  │Pattern   │  │Classify  │  │Preserve  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                     OUTPUT LAYER                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  File System Writer  │  Fabric REST API Client      │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    EXTERNAL SYSTEMS                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │  Fabric  │  │Lakehouse │  │  Fabric  │                   │
│  │Warehouse │  │Metadata  │  │REST API  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Public API** | Single entry point for external callers | Top-level function with sensible defaults, validates inputs |
| **Pipeline Orchestration** | Coordinate transformation steps in correct order | Pure functions calling pure functions, pass immutable data structures |
| **Schema Read & Filter** | Connect to data source, read schema, apply table filtering | Functions using include/exclude patterns, return metadata dicts |
| **Relationship Inference** | Detect dimension vs fact, match keys, handle role-playing | Pattern matching on key prefixes, return relationship tuples |
| **TMDL Generation** | Transform metadata into valid TMDL syntax | Template functions, one per file type (table, relationship, expressions) |
| **Type Mapping** | Convert SQL types to TMDL types | Lookup dict/function, deterministic mapping |
| **Watermark Preservation** | Detect generated vs manual files | File parsing, preserve non-watermarked content |
| **File System Writer** | Write TMDL folder structure to disk | I/O functions, create directories, write UTF-8 text |
| **Fabric REST API Client** | Deploy semantic model via Fabric API | HTTP client, base64 encode definition parts, poll LRO |

## Recommended Project Structure

```
semantic-model-generator/
├── src/
│   └── semantic_model_generator/
│       ├── __init__.py                 # Public API exports
│       ├── api.py                      # generate_semantic_model() entry point
│       ├── pipeline/                   # Orchestration layer
│       │   ├── __init__.py
│       │   └── orchestrator.py         # Pipeline coordination
│       ├── schema/                     # Schema operations
│       │   ├── __init__.py
│       │   ├── reader.py               # Read INFORMATION_SCHEMA
│       │   ├── filter.py               # Include/exclude table filtering
│       │   └── classifier.py           # Classify dims vs facts
│       ├── relationships/              # Relationship inference
│       │   ├── __init__.py
│       │   ├── inference.py            # Detect relationships from keys
│       │   └── patterns.py             # Key matching (exact, role-playing)
│       ├── tmdl/                       # TMDL generation
│       │   ├── __init__.py
│       │   ├── database.py             # database.tmdl
│       │   ├── model.py                # model.tmdl
│       │   ├── table.py                # tables/*.tmdl
│       │   ├── column.py               # Column definitions
│       │   ├── measure.py              # Measure definitions
│       │   ├── relationship.py         # relationships.tmdl
│       │   ├── expression.py           # expressions.tmdl
│       │   └── platform.py             # .platform, definition.pbism
│       ├── domain/                     # Domain logic (pure functions)
│       │   ├── __init__.py
│       │   ├── types.py                # SQL→TMDL type mapping
│       │   ├── identifiers.py          # Deterministic UUID generation
│       │   ├── summarization.py        # Summarization strategy
│       │   └── formatting.py           # Format string selection
│       ├── output/                     # Output layer
│       │   ├── __init__.py
│       │   ├── filesystem.py           # Write TMDL folder structure
│       │   ├── watermark.py            # Preserve manual content
│       │   └── fabric_client.py        # Fabric REST API client
│       ├── config/                     # Configuration
│       │   ├── __init__.py
│       │   └── settings.py             # Configuration dataclasses
│       └── utils/                      # Utilities
│           ├── __init__.py
│           └── validation.py           # Input validation
├── tests/
│   ├── unit/                           # Unit tests (fast, isolated)
│   │   ├── test_schema/
│   │   ├── test_relationships/
│   │   ├── test_tmdl/
│   │   ├── test_domain/
│   │   └── test_output/
│   ├── integration/                    # Integration tests (I/O, API)
│   │   ├── test_pipeline/
│   │   └── test_fabric_client/
│   └── fixtures/                       # Test data
│       ├── sample_metadata.json
│       └── expected_outputs/
├── examples/                           # Usage examples
│   ├── basic_usage.py
│   └── notebooks/
│       └── fabric_example.ipynb
├── pyproject.toml                      # Poetry/pip config
├── README.md
└── .gitignore
```

### Structure Rationale

- **`api.py`**: Single entry point isolates external interface from internals, makes versioning/deprecation easier
- **`pipeline/`**: Orchestration logic separated from transforms, enables swapping orchestration strategies (sequential, parallel)
- **`schema/`, `relationships/`, `tmdl/`**: Organized by domain concern, each folder has clear input/output contract
- **`domain/`**: Pure functions with no I/O, highly testable, reusable across TMDL generation modules
- **`output/`**: All I/O confined to one layer, makes testing easier (mock file system, mock HTTP)
- **`config/`**: Configuration as immutable data structures (dataclasses/pydantic), passed through pipeline
- **Separate `tests/unit/` and `tests/integration/`**: Fast unit tests run always, integration tests run pre-commit/CI

## Architectural Patterns

### Pattern 1: Functional Pipeline with Immutable Data Structures

**What:** Data flows through a series of pure functions, each transforming immutable data structures. No shared state, no side effects until output layer.

**When to use:** When building data transformation pipelines where reproducibility and testability are critical. Perfect for code generation and ETL-like workflows.

**Trade-offs:**
- **Pro:** Extremely testable (no mocks needed for pure functions), easy to reason about, parallelizable
- **Pro:** No hidden state mutations, no "spooky action at a distance"
- **Con:** More verbose than mutating state in place, requires discipline to avoid classes with methods
- **Con:** Python doesn't enforce immutability (use frozen dataclasses, avoid mutation by convention)

**Example:**
```python
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass(frozen=True)
class SchemaMetadata:
    """Immutable container for schema metadata."""
    tables: Dict[str, List[Dict[str, Any]]]
    catalog: str
    schemas: List[str]

@dataclass(frozen=True)
class RelationshipInferenceResult:
    """Immutable result of relationship inference."""
    relationships: List[Dict[str, str]]
    orphaned_tables: List[str]

def read_schema(connection_string: str, schemas: List[str]) -> SchemaMetadata:
    """Pure function: same inputs → same outputs (if schema unchanged)."""
    # Read from database, return immutable metadata
    pass

def infer_relationships(
    metadata: SchemaMetadata,
    key_prefixes: List[str]
) -> RelationshipInferenceResult:
    """Pure function: no side effects, testable with fixtures."""
    # Pattern matching logic, return immutable result
    pass

# Pipeline composition
metadata = read_schema(conn_str, ["Dim", "Fact"])
relationships = infer_relationships(metadata, ["_hk__", "_wk__"])
tmdl_files = generate_tmdl(metadata, relationships)
write_to_disk(tmdl_files, output_dir)  # Only I/O at the end
```

### Pattern 2: Metadata-Driven Configuration

**What:** Schema discovery, filtering rules, type mappings, and output options are parameterized through configuration objects, not hard-coded.

**When to use:** When different users have different schema conventions (key prefixes, naming patterns). Enables reusability across organizations without code changes.

**Trade-offs:**
- **Pro:** Highly flexible, same library works for different warehouse schemas
- **Pro:** Configuration can be versioned, validated, tested independently
- **Con:** More complex than hard-coded values, requires validation
- **Con:** Users need to understand configuration options

**Example:**
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class GeneratorConfig:
    """Configuration for semantic model generation."""
    catalog: str
    schemas: List[str]
    key_prefixes: List[str] = ("_hk__", "_wk__")
    exact_match_prefixes: List[str] = ("_wk__ref__",)
    include_tables: Optional[List[str]] = None
    exclude_tables: Optional[List[str]] = None
    assume_referential_integrity: bool = False
    output_format: str = "tmdl"

def generate_semantic_model(
    metadata: SchemaMetadata,
    config: GeneratorConfig
) -> TMDLOutput:
    """Generate using config, not hard-coded values."""
    # Filter tables based on config.include_tables/exclude_tables
    # Use config.key_prefixes for relationship inference
    # Apply config.assume_referential_integrity
    pass
```

### Pattern 3: Template Functions for Code Generation

**What:** Each TMDL file type has a dedicated template function that takes data and returns a string. Templates are pure functions, not class methods.

**When to use:** Always for code generation. Makes it easy to test output format, modify templates, and compose templates.

**Trade-offs:**
- **Pro:** Each template is independently testable (input dict → output string)
- **Pro:** Easy to modify formatting without touching business logic
- **Pro:** Templates can be composed (table contains columns, columns contain annotations)
- **Con:** String concatenation can be verbose, but Python f-strings help

**Example:**
```python
def generate_column_tmdl(
    column_name: str,
    data_type: str,
    format_string: str,
    lineage_tag: str,
    summarize_by: str
) -> str:
    """Generate TMDL for a single column."""
    lines = [
        f"\tcolumn '{column_name}'",
        f"\t\tdataType: {data_type}"
    ]
    if format_string:
        lines.append(f"\t\tformatString: {format_string}")
    lines.append(f"\t\tlineageTag: {lineage_tag}")
    lines.append(f"\t\tsummarizeBy: {summarize_by}")
    return "\n".join(lines)

def generate_table_tmdl(
    table_name: str,
    columns: List[Dict[str, str]]
) -> str:
    """Generate TMDL for a complete table."""
    header = f"table '{table_name}'\n"
    column_sections = [
        generate_column_tmdl(**col) for col in columns
    ]
    return header + "\n".join(column_sections)
```

### Pattern 4: Watermark-Based Preservation

**What:** Generated files have a watermark comment (e.g., `/// Generated by semantic-model-generator`). On regeneration, only watermarked files are deleted; non-watermarked files are preserved.

**When to use:** When users need to manually extend generated content (custom tables, manual relationships) and you want to avoid overwriting their work.

**Trade-offs:**
- **Pro:** Enables "generate once, then customize" workflows
- **Pro:** Users can add custom content without fear of losing it
- **Con:** Must carefully parse existing files before regenerating
- **Con:** Potential confusion if users edit generated files (edits will be lost)

**Example:**
```python
WATERMARK = "/// Generated by semantic-model-generator - Do not edit manually"

def generate_table_tmdl(table_name: str, columns: List[Dict]) -> str:
    """Generate table TMDL with watermark."""
    return f"{WATERMARK}\ntable '{table_name}'\n..."

def detect_preserved_tables(output_dir: Path) -> List[str]:
    """Find tables without watermark (manually maintained)."""
    preserved = []
    tables_dir = output_dir / "definition" / "tables"
    if tables_dir.exists():
        for table_file in tables_dir.iterdir():
            content = table_file.read_text(encoding="utf-8")
            if not content.startswith(WATERMARK):
                preserved.append(table_file.stem)
    return preserved
```

### Pattern 5: Dual Output Strategy (Folder + REST API)

**What:** Support both writing TMDL to local folder (for Git/manual editing) and deploying directly to Fabric via REST API (for automation).

**When to use:** Users have different workflows: some want Git-based development, others want automated deployment from notebooks.

**Trade-offs:**
- **Pro:** Flexibility for different user workflows
- **Pro:** Local folder output enables version control
- **Con:** Two code paths to maintain (filesystem vs API)
- **Con:** API deployment requires polling LRO (long-running operation)

**Example:**
```python
def write_to_filesystem(tmdl_files: Dict[str, str], output_dir: Path):
    """Write TMDL files to local folder."""
    for path, content in tmdl_files.items():
        file_path = output_dir / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

def deploy_to_fabric(
    tmdl_files: Dict[str, str],
    workspace_id: str,
    model_name: str,
    token: str
):
    """Deploy TMDL to Fabric via REST API."""
    # Build definition payload
    parts = [
        {
            "path": path,
            "payload": base64.b64encode(content.encode()).decode(),
            "payloadType": "InlineBase64"
        }
        for path, content in tmdl_files.items()
    ]

    # Create semantic model
    response = requests.post(
        f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/semanticModels",
        headers={"Authorization": f"Bearer {token}"},
        json={"displayName": model_name, "definition": {"parts": parts}}
    )

    # Poll LRO if 202 Accepted
    if response.status_code == 202:
        location = response.headers["Location"]
        # Poll until status == "Succeeded"
```

## Data Flow

### High-Level Pipeline Flow

```
[Fabric Warehouse INFORMATION_SCHEMA]
    ↓ (read_schema)
[SchemaMetadata: Dict[table_name, List[column_dict]]]
    ↓ (filter_tables)
[Filtered SchemaMetadata]
    ↓ (classify_tables + infer_relationships)
[RelationshipInferenceResult: List[relationship_dict], List[orphaned_tables]]
    ↓ (generate_tmdl_files)
[Dict[file_path, tmdl_content]]
    ↓ (output layer)
    ├─→ [Filesystem: .SemanticModel folder]
    └─→ [Fabric REST API: deployed model]
```

### Detailed Transform Flow

```
1. Schema Discovery
   Input:  connection_string, catalog, schemas
   Process: Query INFORMATION_SCHEMA.COLUMNS
   Output: DataFrame → Dict[table_name, List[{col_name, data_type, ...}]]

2. Table Filtering
   Input:  SchemaMetadata, include_patterns, exclude_patterns
   Process: Filter tables by name patterns
   Output: Filtered SchemaMetadata

3. Table Classification
   Input:  SchemaMetadata, key_prefixes
   Process: Count key columns per table (1 = dim, >1 = fact, 0 = other)
   Output: Dict[table_type, List[table_name]]

4. Relationship Inference
   Input:  SchemaMetadata, key_prefixes, exact_match_prefixes
   Process: Match fact FK columns to dim PK columns
            Handle role-playing (base key extraction)
            Mark first relationship active, rest inactive
   Output: List[{from_table, from_col, to_table, to_col, is_active}]

5. TMDL Generation
   Input:  SchemaMetadata, relationships, config
   Process: For each component (database, model, tables, relationships, expressions):
              Apply template function
              Generate deterministic lineage tags
              Convert SQL types → TMDL types
   Output: Dict[file_path, tmdl_content]

6. Watermark Preservation
   Input:  existing output_dir, new TMDL files
   Process: Read existing files, detect watermarks
            Preserve non-watermarked files
            Delete watermarked files (will be regenerated)
   Output: Updated Dict[file_path, tmdl_content] (merged)

7. Output
   Input:  Dict[file_path, tmdl_content], output_config
   Process: Write to filesystem OR deploy via REST API
   Output: Semantic model (folder or deployed item)
```

### Key Data Flows

1. **Metadata Flow:** INFORMATION_SCHEMA → DataFrame → normalized dict → filtered dict → TMDL templates
2. **Relationship Flow:** Key columns → pattern matching → relationship tuples → TMDL relationship blocks
3. **Type Flow:** SQL data types → type mapping function → (tmdl_type, format_string) → column TMDL
4. **Preservation Flow:** Existing files → watermark detection → preserved content → merged with generated content

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-100 tables | Single-threaded, synchronous pipeline is fine. In-memory metadata dict. |
| 100-1000 tables | Consider parallel TMDL generation (table files can be generated independently). Still in-memory. |
| 1000+ tables | Stream table processing (generator pattern), write files as generated. Consider incremental updates (only regenerate changed tables). |

### Scaling Priorities

1. **First bottleneck:** Relationship inference becomes slow with many tables (O(n²) comparisons). **Fix:** Index tables by base key name, use dict lookups instead of nested loops.
2. **Second bottleneck:** File I/O for 1000+ table files. **Fix:** Batch writes, use async I/O, or write to archive (zip) instead of folder.
3. **Third bottleneck:** Fabric REST API rate limits for large deployments. **Fix:** Use batch update API if available, or chunk deployments.

## Anti-Patterns

### Anti-Pattern 1: Mutable Global State

**What people do:** Store metadata in global variables or class instance variables that get mutated during processing.

**Why it's wrong:** Makes testing difficult (need to reset state), makes parallelization impossible, creates hidden dependencies between functions.

**Do this instead:** Pass immutable data structures through function parameters. Use frozen dataclasses.

```python
# BAD
class Generator:
    def __init__(self):
        self.metadata = {}  # Mutated throughout
        self.relationships = []

    def read_schema(self):
        self.metadata = query_database()  # Mutation

    def infer_relationships(self):
        self.relationships = []  # Reset
        for table in self.metadata:  # Mutates self.relationships
            ...

# GOOD
def read_schema(conn_str: str) -> SchemaMetadata:
    return SchemaMetadata(tables=query_database())

def infer_relationships(metadata: SchemaMetadata) -> List[Relationship]:
    return [...]  # Returns new immutable list
```

### Anti-Pattern 2: Hard-Coded Schema Conventions

**What people do:** Hard-code key prefixes like `_hk__`, table patterns like `Dim` and `Fact`, type mappings.

**Why it's wrong:** Library only works for one organization's schema conventions. Requires code changes to support different warehouses.

**Do this instead:** Accept configuration parameters with sensible defaults.

```python
# BAD
def infer_relationships(metadata):
    for table_name, columns in metadata.items():
        if table_name.startswith("Dim"):  # Hard-coded
            key_cols = [c for c in columns if c.startswith("_hk__")]  # Hard-coded

# GOOD
def infer_relationships(
    metadata: SchemaMetadata,
    dim_pattern: str = "Dim",
    key_prefixes: List[str] = ["_hk__", "_wk__"]
):
    for table_name, columns in metadata.items():
        if table_name.startswith(dim_pattern):
            key_cols = [
                c for c in columns
                if any(c.startswith(prefix) for prefix in key_prefixes)
            ]
```

### Anti-Pattern 3: Mixed Concerns (I/O + Transform)

**What people do:** Read from database, transform data, and write to disk all in one function.

**Why it's wrong:** Impossible to test transforms without database access. Can't reuse transforms for different input sources.

**Do this instead:** Separate I/O (input, output) from pure transforms.

```python
# BAD
def generate_model(conn_str: str, output_dir: str):
    # Read (I/O)
    cursor = connect(conn_str)
    rows = cursor.execute("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")

    # Transform (pure logic mixed with I/O)
    for row in rows:
        tmdl = generate_tmdl(row)
        # Write (I/O)
        with open(f"{output_dir}/{row.table}.tmdl", "w") as f:
            f.write(tmdl)

# GOOD
def read_schema(conn_str: str) -> SchemaMetadata:
    """I/O: Read from database."""
    cursor = connect(conn_str)
    rows = cursor.execute("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")
    return parse_rows(rows)

def generate_tmdl_files(metadata: SchemaMetadata) -> Dict[str, str]:
    """Pure: Transform metadata to TMDL."""
    return {
        f"tables/{table}.tmdl": generate_table_tmdl(table, cols)
        for table, cols in metadata.tables.items()
    }

def write_files(files: Dict[str, str], output_dir: Path):
    """I/O: Write to disk."""
    for path, content in files.items():
        (output_dir / path).write_text(content)
```

### Anti-Pattern 4: String Concatenation Without Structure

**What people do:** Build TMDL as one giant string with + or .join(), making it hard to modify individual sections.

**Why it's wrong:** Hard to test individual components (column, measure, relationship). Changes to one section require touching a giant string builder.

**Do this instead:** Separate template function for each TMDL component, compose them hierarchically.

```python
# BAD
def generate_table_tmdl(table_name, columns):
    tmdl = f"table {table_name}\n"
    for col in columns:
        tmdl += f"\tcolumn {col['name']}\n\t\tdataType: {col['type']}\n"
        # ... 50 more lines
    tmdl += "partition ...\n"
    # Hard to modify, hard to test

# GOOD
def generate_column_tmdl(col: Dict) -> str:
    """Testable: input dict → output string."""
    lines = [
        f"\tcolumn '{col['name']}'",
        f"\t\tdataType: {col['type']}"
    ]
    return "\n".join(lines)

def generate_partition_tmdl(table_name: str) -> str:
    """Testable: input → output."""
    return f"\tpartition '{table_name}' = entity\n\t\tmode: directLake"

def generate_table_tmdl(table_name: str, columns: List[Dict]) -> str:
    """Compose smaller templates."""
    header = f"table '{table_name}'\n"
    column_blocks = [generate_column_tmdl(col) for col in columns]
    partition = generate_partition_tmdl(table_name)
    return header + "\n".join(column_blocks) + "\n" + partition
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Fabric Warehouse | SQL connection via `mssql-python`, token auth | Use `notebookutils.credentials.getToken()` in Fabric notebooks, or Azure credential chain |
| Fabric REST API | HTTP client with bearer token, POST to `/workspaces/{id}/semanticModels` | Must poll LRO for 202 Accepted responses, definition parts are base64-encoded TMDL files |
| OneLake | Direct Lake URL format: `https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}` | Used in expressions.tmdl for AzureStorage.DataLake connection |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `api.py` ↔ `pipeline/orchestrator.py` | Function call: `api.py` validates inputs, calls orchestrator with config object | Orchestrator is pure function: config in, TMDL files out |
| `pipeline/` ↔ `schema/`, `relationships/`, `tmdl/` | Function calls: orchestrator calls domain modules in sequence | Orchestrator owns the pipeline order, domain modules are stateless |
| `tmdl/` ↔ `domain/` | Function calls: TMDL generators call domain functions (type mapping, UUID generation) | Domain functions are pure utilities, no knowledge of TMDL structure |
| `pipeline/` ↔ `output/` | Function call: orchestrator passes TMDL files dict to output layer | Output layer handles all I/O (filesystem writes, REST API calls) |
| `output/filesystem.py` ↔ `output/watermark.py` | Function call: filesystem writer calls watermark detector before writing | Watermark detector reads existing files, returns preserved content |

## Build Order Implications

### Phase 1: Foundation (Core Domain Functions)
**Build first:** Functions with zero dependencies on other modules.

- `domain/types.py`: SQL → TMDL type mapping
- `domain/identifiers.py`: Deterministic UUID generation
- `domain/summarization.py`: Summarization strategy
- `domain/formatting.py`: Format string selection
- `config/settings.py`: Configuration dataclasses

**Why first:** These are pure functions used everywhere. Building them first enables TDD for other modules.

**Tests:** Unit tests with hardcoded inputs/outputs. No mocks needed.

### Phase 2: Schema Operations
**Build second:** Schema reading and filtering (first I/O boundary).

- `schema/reader.py`: Query INFORMATION_SCHEMA
- `schema/filter.py`: Include/exclude table filtering
- `schema/classifier.py`: Classify dims vs facts by key count

**Why second:** Provides the input data structure for all downstream transforms.

**Tests:** Integration tests with mock database OR fixture data files. Unit tests for filter/classify logic.

### Phase 3: Relationship Inference
**Build third:** Core business logic for star schema detection.

- `relationships/patterns.py`: Key matching (exact, base key extraction)
- `relationships/inference.py`: Detect dims/facts, create relationship tuples

**Why third:** Depends on schema metadata from Phase 2. Independent of TMDL generation.

**Tests:** Unit tests with fixture SchemaMetadata. Test role-playing scenarios.

### Phase 4: TMDL Generation
**Build fourth:** Template functions for each TMDL file type.

- `tmdl/column.py`
- `tmdl/measure.py`
- `tmdl/table.py`
- `tmdl/relationship.py`
- `tmdl/model.py`
- `tmdl/database.py`
- `tmdl/expression.py`
- `tmdl/platform.py`

**Why fourth:** Depends on domain functions (Phase 1) and relationship data (Phase 3).

**Tests:** Unit tests: dict in → TMDL string out. Compare against golden files.

### Phase 5: Output Layer
**Build fifth:** Filesystem writer and watermark preservation.

- `output/watermark.py`: Detect and preserve manual content
- `output/filesystem.py`: Write TMDL folder structure

**Why fifth:** Depends on TMDL generation (Phase 4). Watermark logic needs to parse TMDL files.

**Tests:** Integration tests with temp directories. Verify watermark detection, preserved files.

### Phase 6: Fabric REST API Client
**Build sixth:** HTTP client for deploying to Fabric.

- `output/fabric_client.py`: POST semantic model, poll LRO

**Why sixth:** Optional feature, can be built after filesystem output works. Requires Fabric workspace access.

**Tests:** Integration tests against test workspace OR mocked HTTP client.

### Phase 7: Pipeline Orchestration
**Build seventh:** Coordinate all phases.

- `pipeline/orchestrator.py`: Call schema → classify → infer → generate → output

**Why seventh:** Orchestrator calls all other modules, so build it last.

**Tests:** Integration tests: end-to-end from fixture metadata to TMDL output.

### Phase 8: Public API
**Build eighth:** User-facing entry point.

- `api.py`: `generate_semantic_model()` function
- `__init__.py`: Public exports

**Why eighth:** Depends on orchestrator (Phase 7). Adds input validation and defaults.

**Tests:** Integration tests: full workflow from config to output.

## Testability Strategy

### Unit Tests (Fast, No I/O)

```python
# Test pure functions with fixtures
def test_sql_type_to_tmdl_type():
    assert sql_type_to_tmdl_type("bigint", "count") == ("int64", "0")
    assert sql_type_to_tmdl_type("varchar", "name") == ("string", "")

def test_deterministic_uuid():
    uuid1 = deterministic_uuid("column", "customers", "id")
    uuid2 = deterministic_uuid("column", "customers", "id")
    assert uuid1 == uuid2  # Deterministic

def test_generate_column_tmdl():
    col = {"COLUMN_NAME": "id", "DATA_TYPE": "bigint"}
    tmdl = generate_column_tmdl(col, "customers", "star_schema")
    assert "column 'id'" in tmdl
    assert "dataType: int64" in tmdl
```

### Integration Tests (I/O, API)

```python
# Test with temp directories
def test_write_semantic_model_files(tmp_path):
    metadata = {"customers": [{"COLUMN_NAME": "id", "DATA_TYPE": "bigint"}]}
    relationships = []
    save_semantic_model_files(
        tmp_path,
        metadata,
        relationships,
        catalog="gold",
        model_name="Test"
    )
    assert (tmp_path / "definition" / "database.tmdl").exists()
    assert (tmp_path / "definition" / "tables" / "customers.tmdl").exists()

# Test watermark preservation
def test_watermark_preservation(tmp_path):
    # Create existing model with manual table
    manual_table = tmp_path / "definition" / "tables" / "custom.tmdl"
    manual_table.parent.mkdir(parents=True)
    manual_table.write_text("table 'custom'\n...")  # No watermark

    # Regenerate
    output_path, preserved_tables, _, _ = get_output_directory("Test", tmp_path)
    assert "custom" in preserved_tables
    assert manual_table.exists()  # Not deleted
```

### End-to-End Tests

```python
# Test full pipeline with fixture metadata
def test_generate_semantic_model_e2e(tmp_path):
    metadata_df = pd.DataFrame({
        "TABLE_CATALOG": ["gold", "gold"],
        "TABLE_SCHEMA": ["Dim", "Fact"],
        "TABLE_NAME": ["customers", "sales"],
        "COLUMN_NAME": ["_hk__customer", "_hk__customer"],
        "DATA_TYPE": ["varchar", "varchar"]
    })

    output_path = generate_semantic_model(
        metadata_df,
        catalog="gold",
        schemas=["Dim", "Fact"],
        model_name="Test",
        direct_lake_url="https://...",
        output_dir=tmp_path
    )

    # Verify all files created
    assert (output_path / "definition.pbism").exists()
    assert (output_path / "definition" / "relationships.tmdl").exists()
```

## Sources

- [Why Power BI developers should care about TMDL](https://endjin.com/blog/2025/01/why-power-bi-developers-should-care-about-the-tabular-model-definition-language-tmdl) - TMDL overview and code generation techniques
- [Tabular Model Definition Language (TMDL) | Microsoft Learn](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025) - Official TMDL documentation
- [Read data from semantic models with Python - Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/data-science/read-write-power-bi-python) - SemPy library architecture
- [Semantic link and Power BI connectivity](https://learn.microsoft.com/en-us/fabric/data-science/semantic-link-power-bi) - Semantic link patterns
- [Functional Programming Paradigm for Python Pipelines](https://arxiv.org/html/2405.16956v1) - FP pipeline architecture for scientific computation
- [Data Pipeline Design Patterns - Coding patterns in Python](https://www.startdataengineering.com/post/code-patterns/) - Metadata-driven design, composable patterns
- [Data Pipeline Architecture: Design Patterns with Examples](https://dagster.io/guides/data-pipeline/data-pipeline-architecture-5-design-patterns-with-examples) - Declarative framework, factory patterns
- [Functional Programming in Python - Core Principles](https://arjancodes.com/blog/functional-programming-principles-in-python/) - Pure functions, testability
- [Mastering Functional Programming in Python](https://www.qodo.ai/blog/mastering-functional-programming-in-python/) - Pure functions eliminate side effects
- [Functions over classes? Simpler, functional style in Python](https://www.nijho.lt/post/functional-python/) - Small, pure functions for testability
- [Structuring Your Project — The Hitchhiker's Guide to Python](https://docs.python-guide.org/writing/structure/) - Project structure principles
- [Modular monolith in Python](https://breadcrumbscollector.tech/modular-monolith-in-python/) - Component boundaries, public API vs internal details
- [Data Pipelines in Python: Frameworks & Building Processes](https://lakefs.io/blog/python-data-pipeline/) - Modular, reusable components
- [Composable Data Architecture: 2026 Tipping Point](https://www.infojiniconsulting.com/blog/composable-data-architectures-explained-why-2026-is-the-tipping-point/) - Self-contained services, composable frameworks
- [Functional pipelines in Python](https://labex.io/tutorials/python-how-to-create-functional-pipelines-466964) - Sequential operations, composable code
- [Microsoft Fabric REST APIs - Get Semantic Model Definition](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/get-semantic-model-definition) - TMDL format support via REST API
- [Semantic Model definition - Microsoft Fabric REST APIs](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/semantic-model-definition) - Base64-encoded definition parts
- [What is semantic link? - Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/data-science/semantic-link-overview) - SemPy architecture overview
- [Semantic link propagation with SemPy](https://learn.microsoft.com/en-us/fabric/data-science/semantic-link-semantic-propagation) - Metadata propagation patterns

---
*Architecture research for: Python TMDL Semantic Model Generator*
*Researched: 2026-02-09*
