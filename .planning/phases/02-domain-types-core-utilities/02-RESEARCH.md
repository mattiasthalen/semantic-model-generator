# Phase 2: Domain Types & Core Utilities - Research

**Researched:** 2026-02-09
**Domain:** Python functional programming with immutable data structures, deterministic UUID generation, SQL-to-TMDL type mapping, and TMDL syntax validation
**Confidence:** HIGH

## Summary

Phase 2 focuses on building pure, deterministic utility functions and immutable domain types that serve as the foundation for all downstream phases. The research reveals that Python 3.11+ provides excellent support for immutable domain modeling through frozen dataclasses with slots, deterministic UUID generation via uuid5, and robust string handling for identifier quoting and whitespace validation.

The key technical insight is that frozen dataclasses with `slots=True` provide memory-efficient, hashable, immutable value objects that align perfectly with the functional programming requirement (REQ-22). These can be combined with Python's built-in `uuid.uuid5()` for deterministic UUID generation, simple dictionary-based type mapping, and straightforward string manipulation functions for TMDL identifier quoting and whitespace validation.

TMDL has specific syntax requirements: single quotes for identifiers with special characters (escaped with double single quotes), mandatory tab-based indentation (not spaces), and strict whitespace handling. SQL Server types in Microsoft Fabric warehouses map to a limited set of TMDL tabular model data types (Whole Number, Decimal Number, Boolean, Text, Date, Currency, Binary).

**Primary recommendation:** Use `@dataclass(frozen=True, slots=True)` for all domain types, Python's standard library `uuid.uuid5()` with a project-specific namespace for deterministic UUIDs, simple dict/enum-based SQL-to-TMDL type mapping, and pure functions for identifier quoting and whitespace validation.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| dataclasses (stdlib) | 3.11+ | Frozen immutable domain types | Built-in, zero dependencies, mypy strict support, hashable value objects |
| uuid (stdlib) | 3.11+ | Deterministic UUID generation with uuid5 | Built-in, RFC 9562 compliant, SHA-1 based determinism |
| enum (stdlib) | 3.11+ | Type mapping with StrEnum | Built-in, type-safe enumerations, StrEnum for string comparisons |
| re (stdlib) | 3.11+ | Whitespace and identifier validation | Built-in, robust pattern matching |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing (stdlib) | 3.11+ | Type annotations for mypy strict | All type hints, especially for pure functions |
| dataclasses.replace (stdlib) | 3.11+ | Creating modified copies of frozen instances | When you need a modified version of immutable data |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Frozen dataclasses | attrs with frozen=True | attrs offers more features but adds dependency; stdlib sufficient for this phase |
| Frozen dataclasses | Pydantic dataclasses | Pydantic adds runtime validation but requires dependency; not needed for internal types |
| Dict-based type mapping | SQLAlchemy type system | SQLAlchemy too heavyweight; simple dict mapping sufficient for static conversions |
| uuid5 | uuid4 (random) | uuid4 is non-deterministic; fails REQ-12 requirement for stable regeneration |

**Installation:**
```bash
# No external dependencies needed - all stdlib
python --version  # Ensure >= 3.11
```

## Architecture Patterns

### Recommended Project Structure
```
src/semantic_model_generator/
├── domain/              # Domain types (frozen dataclasses)
│   ├── __init__.py
│   └── types.py        # Core domain dataclasses
├── utils/              # Pure utility functions
│   ├── __init__.py
│   ├── uuid_gen.py     # Deterministic UUID generation
│   ├── type_mapping.py # SQL to TMDL type conversion
│   ├── identifiers.py  # TMDL identifier quoting
│   └── whitespace.py   # TMDL whitespace validation
```

### Pattern 1: Frozen Dataclasses with Slots
**What:** Immutable, memory-efficient value objects using `@dataclass(frozen=True, slots=True)`
**When to use:** For all domain types representing immutable data (metadata, configuration, schemas)
**Example:**
```python
# Source: https://docs.python.org/3/library/dataclasses.html
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ColumnMetadata:
    """Immutable metadata for a warehouse column."""
    name: str
    sql_type: str
    is_nullable: bool
    max_length: int | None = None
    precision: int | None = None
    scale: int | None = None

# Usage - create once, never mutate
col = ColumnMetadata(name="ProductName", sql_type="varchar", is_nullable=False, max_length=100)
# col.name = "NewName"  # Raises FrozenInstanceError

# To "modify", create new instance
col2 = dataclasses.replace(col, max_length=200)
```

**Benefits:**
- Hashable (can be dict keys, set members)
- Thread-safe (no mutation)
- Memory-efficient with slots
- mypy strict mode compatible
- Clear semantics: these are values, not mutable objects

### Pattern 2: Deterministic UUID Generation with uuid5
**What:** Generate stable UUIDs using uuid5 with namespace + name
**When to use:** When generating IDs for semantic model objects that must remain stable across regenerations
**Example:**
```python
# Source: https://docs.python.org/3/library/uuid.html
import uuid

# Define project-specific namespace (generated once, stored as constant)
SEMANTIC_MODEL_NAMESPACE = uuid.UUID('12345678-1234-5678-1234-567812345678')

def generate_table_uuid(table_name: str) -> uuid.UUID:
    """Generate deterministic UUID for a table."""
    # Normalize input to ensure consistency
    normalized_name = table_name.strip().lower()
    return uuid.uuid5(SEMANTIC_MODEL_NAMESPACE, f"table:{normalized_name}")

# Same input always produces same UUID
uuid1 = generate_table_uuid("Sales")
uuid2 = generate_table_uuid("Sales")
assert uuid1 == uuid2  # True - deterministic!
```

**Key considerations:**
- Always normalize inputs (trim whitespace, case-fold if appropriate)
- Use consistent namespace across the application
- Include object type in name string (e.g., "table:Sales", "column:Sales.Amount") to avoid collisions
- Document namespace UUID as a constant

### Pattern 3: Enum-Based Type Mapping
**What:** Use StrEnum (Python 3.11+) for SQL-to-TMDL type mapping
**When to use:** For static type conversions that need to be type-safe and serializable
**Example:**
```python
# Source: https://docs.python.org/3/library/enum.html
from enum import StrEnum

class TmdlDataType(StrEnum):
    """TMDL data types for tabular models."""
    WHOLE_NUMBER = "int64"      # Maps to: int, bigint, smallint, bit
    DECIMAL_NUMBER = "double"    # Maps to: float, real, decimal, numeric
    BOOLEAN = "boolean"          # Maps to: bit (when used as boolean)
    TEXT = "string"              # Maps to: varchar, char
    DATE = "dateTime"            # Maps to: date, datetime2, time
    CURRENCY = "decimal"         # Maps to: decimal with precision/scale for money
    BINARY = "binary"            # Maps to: varbinary, uniqueidentifier

# Type mapping dict
SQL_TO_TMDL_TYPE: dict[str, TmdlDataType] = {
    "int": TmdlDataType.WHOLE_NUMBER,
    "bigint": TmdlDataType.WHOLE_NUMBER,
    "smallint": TmdlDataType.WHOLE_NUMBER,
    "bit": TmdlDataType.BOOLEAN,
    "float": TmdlDataType.DECIMAL_NUMBER,
    "real": TmdlDataType.DECIMAL_NUMBER,
    "decimal": TmdlDataType.DECIMAL_NUMBER,
    "numeric": TmdlDataType.DECIMAL_NUMBER,
    "varchar": TmdlDataType.TEXT,
    "char": TmdlDataType.TEXT,
    "date": TmdlDataType.DATE,
    "datetime2": TmdlDataType.DATE,
    "time": TmdlDataType.DATE,
    "varbinary": TmdlDataType.BINARY,
    "uniqueidentifier": TmdlDataType.BINARY,
}

def map_sql_type_to_tmdl(sql_type: str) -> TmdlDataType:
    """Map SQL Server type to TMDL data type."""
    normalized = sql_type.lower().strip()
    if normalized not in SQL_TO_TMDL_TYPE:
        raise ValueError(f"Unsupported SQL type: {sql_type}")
    return SQL_TO_TMDL_TYPE[normalized]
```

### Pattern 4: Pure Function Identifier Quoting
**What:** Pure function that quotes TMDL identifiers according to syntax rules
**When to use:** When generating TMDL output for table/column names with special characters
**Example:**
```python
# Based on: https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview
import re

def quote_tmdl_identifier(name: str) -> str:
    """Quote identifier for TMDL if it contains special characters.

    Single quotes are required when names contain:
    - Dot (.)
    - Equals (=)
    - Colon (:)
    - Single quote (')
    - Whitespace

    Internal single quotes are escaped as double single quotes ('').
    """
    if not name:
        raise ValueError("Identifier cannot be empty")

    # Check if quoting is needed
    needs_quoting = bool(re.search(r"[.=:'\s]", name))

    if needs_quoting:
        # Escape internal single quotes by doubling them
        escaped = name.replace("'", "''")
        return f"'{escaped}'"

    return name

# Examples
assert quote_tmdl_identifier("Sales") == "Sales"
assert quote_tmdl_identifier("Product Name") == "'Product Name'"
assert quote_tmdl_identifier("Customer's Choice") == "'Customer''s Choice'"
assert quote_tmdl_identifier("Table.Column") == "'Table.Column'"
```

### Pattern 5: TMDL Whitespace Validation
**What:** Pure function to validate/enforce TMDL tab-based indentation
**When to use:** When generating or validating TMDL output
**Example:**
```python
# Based on: https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview
def validate_tmdl_indentation(tmdl_content: str) -> list[str]:
    """Validate that TMDL uses tabs (not spaces) for indentation.

    Returns list of error messages (empty if valid).
    """
    errors: list[str] = []
    lines = tmdl_content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        # Skip empty lines
        if not line.strip():
            continue

        # Check for leading spaces (should be tabs)
        if line.startswith(" "):
            # Count leading spaces
            space_count = len(line) - len(line.lstrip(" "))
            errors.append(
                f"Line {line_num}: Found {space_count} leading space(s), "
                f"TMDL requires tab indentation"
            )

    return errors

def indent_tmdl(level: int) -> str:
    """Generate TMDL indentation at specified level (0, 1, 2, ...)."""
    return "\t" * level
```

### Anti-Patterns to Avoid
- **Mutable dataclasses for domain types:** Leads to unintended mutations, threading issues, and violates functional programming principle (REQ-22)
- **uuid4 for deterministic IDs:** Produces different UUIDs each run, violates REQ-12 stability requirement
- **Hardcoded type mappings in business logic:** Scatter magic strings throughout code; centralize in dict/enum
- **Spaces for TMDL indentation:** TMDL requires tabs; spaces will produce invalid output
- **Unescaped identifier quoting:** Must double internal single quotes or output will be malformed
- **String concatenation for whitespace:** Use `\t` constant, not guessing at spacing

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| UUID generation | Custom hash-based ID generator | `uuid.uuid5()` from stdlib | RFC 9562 compliant, handles collisions, well-tested, namespace support |
| Immutable data structures | Custom `__setattr__` override classes | `@dataclass(frozen=True, slots=True)` | Stdlib solution, mypy integration, hashability, slots optimization |
| String enum types | String constants or custom classes | `StrEnum` (Python 3.11+) | Type-safe, comparable to strings, autocomplete support |
| Identifier escaping | Manual string replacement | Pure function with regex validation | Edge cases (nested quotes, empty strings, special chars) are subtle |
| Whitespace validation | Manual character checking | Regex or `str.startswith()` with clear rules | Tab/space detection is error-prone without systematic approach |

**Key insight:** Python 3.11+ stdlib provides everything needed for this phase. Custom solutions add complexity without benefit. The stdlib implementations are battle-tested, performant, and integrate seamlessly with type checkers.

## Common Pitfalls

### Pitfall 1: Mutable Default Arguments in Frozen Dataclasses
**What goes wrong:** Using mutable defaults (list, dict) in frozen dataclasses causes shared state across instances
**Why it happens:** Python evaluates default arguments once at function definition time
**How to avoid:** Use `field(default_factory=...)` for mutable defaults
**Warning signs:** Tests fail with unexpected data in "fresh" instances
```python
from dataclasses import dataclass, field

# WRONG
@dataclass(frozen=True)
class TableMetadata:
    columns: list[str] = []  # Shared across all instances!

# CORRECT
@dataclass(frozen=True)
class TableMetadata:
    columns: list[str] = field(default_factory=list)
```

### Pitfall 2: Non-Normalized UUID Inputs
**What goes wrong:** `generate_uuid("Sales")` and `generate_uuid(" Sales ")` produce different UUIDs
**Why it happens:** uuid5 hashes the exact input string, including whitespace
**How to avoid:** Always normalize inputs (strip, lowercase if case-insensitive) before hashing
**Warning signs:** UUIDs change across runs due to inconsistent input formatting
```python
# WRONG
def generate_table_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, name)  # Raw input

# CORRECT
def generate_table_uuid(name: str) -> uuid.UUID:
    normalized = name.strip()  # Remove whitespace
    # Note: Keep original casing if names are case-sensitive in source system
    return uuid.uuid5(NAMESPACE, f"table:{normalized}")
```

### Pitfall 3: Incorrect Single Quote Escaping
**What goes wrong:** Identifier `"Customer's Choice"` quoted as `'Customer's Choice'` produces invalid TMDL (unescaped quote)
**Why it happens:** Forgetting that internal single quotes must be doubled
**How to avoid:** Always use `name.replace("'", "''")` before wrapping in quotes
**Warning signs:** TMDL parser errors on identifiers with apostrophes
```python
# WRONG
def quote_identifier(name: str) -> str:
    if " " in name:
        return f"'{name}'"  # Doesn't escape internal quotes!

# CORRECT
def quote_identifier(name: str) -> str:
    if needs_quoting(name):
        escaped = name.replace("'", "''")  # Escape first
        return f"'{escaped}'"
    return name
```

### Pitfall 4: Mixing Tabs and Spaces in TMDL Output
**What goes wrong:** TMDL file uses spaces for some indentation, tabs for others
**Why it happens:** String concatenation with hardcoded spaces or inconsistent indentation functions
**How to avoid:** Centralize indentation in single function returning `"\t" * level`
**Warning signs:** TMDL parser rejects file, or indentation appears inconsistent in tab-aware editors
```python
# WRONG
def format_column(name: str, level: int) -> str:
    indent = "    " * level  # Spaces!
    return f"{indent}column {name}"

# CORRECT
def format_column(name: str, level: int) -> str:
    indent = "\t" * level  # Tabs
    return f"{indent}column {name}"
```

### Pitfall 5: Frozen Dataclasses Without Slots
**What goes wrong:** Memory usage is higher than necessary, attribute access is slower
**Why it happens:** Not using `slots=True` parameter (requires Python 3.10+)
**How to avoid:** Always use `@dataclass(frozen=True, slots=True)` for value objects
**Warning signs:** Higher memory usage in profiling, especially with many instances
```python
# ACCEPTABLE but not optimal
@dataclass(frozen=True)
class ColumnMetadata:
    name: str
    sql_type: str

# BETTER (Python 3.10+)
@dataclass(frozen=True, slots=True)
class ColumnMetadata:
    name: str
    sql_type: str
```

### Pitfall 6: Type Mapping Without Case Normalization
**What goes wrong:** `"VARCHAR"` doesn't map but `"varchar"` does
**Why it happens:** SQL type names can be case-insensitive in source but dict keys are case-sensitive
**How to avoid:** Always normalize to lowercase before lookup
**Warning signs:** Mapping works in tests but fails in production with different casing
```python
# WRONG
def map_type(sql_type: str) -> TmdlDataType:
    return SQL_TO_TMDL_TYPE[sql_type]  # Case-sensitive!

# CORRECT
def map_type(sql_type: str) -> TmdlDataType:
    normalized = sql_type.lower().strip()
    return SQL_TO_TMDL_TYPE[normalized]
```

## Code Examples

Verified patterns from official sources:

### Frozen Dataclass with Slots (Complete Example)
```python
# Source: https://docs.python.org/3/library/dataclasses.html
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class ColumnMetadata:
    """Immutable column metadata from warehouse schema."""
    name: str
    sql_type: str
    is_nullable: bool
    ordinal_position: int
    max_length: int | None = None
    numeric_precision: int | None = None
    numeric_scale: int | None = None

    def __post_init__(self) -> None:
        """Validate invariants after construction."""
        if not self.name:
            raise ValueError("Column name cannot be empty")
        if self.ordinal_position < 1:
            raise ValueError("Ordinal position must be >= 1")

# Usage
col = ColumnMetadata(
    name="ProductName",
    sql_type="varchar",
    is_nullable=False,
    ordinal_position=1,
    max_length=100
)

# Hashable - can use as dict key
metadata_cache: dict[ColumnMetadata, str] = {col: "cached_value"}

# To modify, create new instance
updated = dataclasses.replace(col, max_length=200)
```

### Deterministic UUID Generation (Complete Example)
```python
# Source: https://docs.python.org/3/library/uuid.html
import uuid

# Project namespace (generate once, commit to code)
# Generate with: uuid.uuid4() then hardcode
SEMANTIC_MODEL_NAMESPACE = uuid.UUID('a1b2c3d4-e5f6-7890-abcd-ef1234567890')

def generate_deterministic_uuid(object_type: str, object_name: str) -> uuid.UUID:
    """Generate stable UUID for semantic model object.

    Args:
        object_type: Type of object (table, column, measure, etc.)
        object_name: Fully qualified name of object

    Returns:
        Deterministic UUID based on type and name

    Example:
        >>> generate_deterministic_uuid("table", "Sales")
        UUID('...')  # Always the same for "table:Sales"
    """
    # Normalize inputs
    normalized_type = object_type.strip().lower()
    normalized_name = object_name.strip()  # Preserve case for names

    # Combine with delimiter to avoid collisions
    composite_name = f"{normalized_type}:{normalized_name}"

    return uuid.uuid5(SEMANTIC_MODEL_NAMESPACE, composite_name)

# Test determinism
uuid1 = generate_deterministic_uuid("table", "Sales")
uuid2 = generate_deterministic_uuid("table", "Sales")
assert uuid1 == uuid2  # Passes - deterministic!
```

### SQL to TMDL Type Mapping (Complete Example)
```python
# Source: https://learn.microsoft.com/en-us/analysis-services/tabular-models/data-types-supported-ssas-tabular
from enum import StrEnum

class TmdlDataType(StrEnum):
    """Data types in TMDL tabular models.

    Based on Analysis Services tabular model data types.
    """
    INT64 = "int64"          # Whole Number (64-bit integer)
    DOUBLE = "double"         # Decimal Number (64-bit real)
    BOOLEAN = "boolean"       # Boolean (true/false)
    STRING = "string"         # Text (Unicode strings)
    DATETIME = "dateTime"     # Date (dates and times)
    DECIMAL = "decimal"       # Currency (fixed precision)
    BINARY = "binary"         # Binary (unstructured data)

# Mapping from SQL Server types (Fabric warehouse) to TMDL types
SQL_TO_TMDL_TYPE: dict[str, TmdlDataType] = {
    # Integer types
    "bit": TmdlDataType.BOOLEAN,
    "smallint": TmdlDataType.INT64,
    "int": TmdlDataType.INT64,
    "bigint": TmdlDataType.INT64,
    # Decimal types
    "decimal": TmdlDataType.DECIMAL,
    "numeric": TmdlDataType.DECIMAL,
    "float": TmdlDataType.DOUBLE,
    "real": TmdlDataType.DOUBLE,
    # Character types
    "char": TmdlDataType.STRING,
    "varchar": TmdlDataType.STRING,
    # Date/time types
    "date": TmdlDataType.DATETIME,
    "datetime2": TmdlDataType.DATETIME,
    "time": TmdlDataType.DATETIME,
    # Binary types
    "varbinary": TmdlDataType.BINARY,
    "uniqueidentifier": TmdlDataType.BINARY,
}

def map_sql_type_to_tmdl(sql_type: str) -> TmdlDataType:
    """Map Microsoft Fabric warehouse SQL type to TMDL data type.

    Args:
        sql_type: SQL Server data type name (case-insensitive)

    Returns:
        Corresponding TMDL data type

    Raises:
        ValueError: If SQL type is not supported

    Example:
        >>> map_sql_type_to_tmdl("varchar")
        <TmdlDataType.STRING: 'string'>
    """
    normalized = sql_type.lower().strip()

    if normalized not in SQL_TO_TMDL_TYPE:
        supported = ", ".join(sorted(SQL_TO_TMDL_TYPE.keys()))
        raise ValueError(
            f"Unsupported SQL type: '{sql_type}'. "
            f"Supported types: {supported}"
        )

    return SQL_TO_TMDL_TYPE[normalized]
```

### TMDL Identifier Quoting (Complete Example)
```python
# Source: https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview
import re

def quote_tmdl_identifier(identifier: str) -> str:
    """Quote TMDL identifier if it contains special characters.

    TMDL requires single quotes around identifiers containing:
    - Whitespace
    - Dot (.)
    - Equals (=)
    - Colon (:)
    - Single quote (')

    Internal single quotes are escaped by doubling them.

    Args:
        identifier: Object name to potentially quote

    Returns:
        Quoted identifier if needed, otherwise unchanged

    Raises:
        ValueError: If identifier is empty

    Examples:
        >>> quote_tmdl_identifier("Sales")
        'Sales'
        >>> quote_tmdl_identifier("Product Name")
        "'Product Name'"
        >>> quote_tmdl_identifier("Customer's Choice")
        "'Customer''s Choice'"
    """
    if not identifier:
        raise ValueError("Identifier cannot be empty")

    # Check if quoting is needed (whitespace or special TMDL characters)
    needs_quotes = bool(re.search(r"[\s.=:']", identifier))

    if needs_quotes:
        # Escape internal single quotes by doubling them
        escaped = identifier.replace("'", "''")
        return f"'{escaped}'"

    return identifier

def unquote_tmdl_identifier(quoted: str) -> str:
    """Remove TMDL quotes and unescape internal quotes.

    Args:
        quoted: Potentially quoted identifier

    Returns:
        Unquoted identifier with escaped quotes restored

    Example:
        >>> unquote_tmdl_identifier("'Customer''s Choice'")
        "Customer's Choice"
    """
    if quoted.startswith("'") and quoted.endswith("'"):
        # Remove outer quotes
        unquoted = quoted[1:-1]
        # Unescape internal quotes
        return unquoted.replace("''", "'")

    return quoted
```

### TMDL Whitespace Validation (Complete Example)
```python
# Source: https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview
from typing import NamedTuple

class IndentationError(NamedTuple):
    """TMDL indentation validation error."""
    line_number: int
    message: str
    line_content: str

def validate_tmdl_indentation(content: str) -> list[IndentationError]:
    """Validate TMDL uses tab indentation (not spaces).

    TMDL requires:
    - Tab characters for indentation (not spaces)
    - Consistent tab usage throughout

    Args:
        content: TMDL file content to validate

    Returns:
        List of indentation errors (empty if valid)

    Example:
        >>> tmdl = "table Sales\\n    column Name"  # Spaces!
        >>> errors = validate_tmdl_indentation(tmdl)
        >>> len(errors)
        1
    """
    errors: list[IndentationError] = []
    lines = content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        # Skip empty lines and lines with only whitespace
        if not line.strip():
            continue

        # Check for leading spaces
        if line and line[0] == " ":
            # Count consecutive leading spaces
            space_count = len(line) - len(line.lstrip(" "))
            errors.append(
                IndentationError(
                    line_number=line_num,
                    message=f"Found {space_count} leading space(s); TMDL requires tabs",
                    line_content=line[:50]  # First 50 chars for context
                )
            )

    return errors

def indent_tmdl(level: int) -> str:
    """Generate TMDL indentation string for specified level.

    Args:
        level: Indentation level (0 = no indent, 1 = one tab, etc.)

    Returns:
        Tab characters for indentation

    Example:
        >>> indent_tmdl(0)
        ''
        >>> indent_tmdl(2)
        '\\t\\t'
    """
    if level < 0:
        raise ValueError(f"Indentation level must be >= 0, got {level}")

    return "\t" * level
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `class MyEnum(str, Enum)` mixin | `class MyEnum(StrEnum)` | Python 3.11 | Cleaner syntax, no mixin confusion, direct string comparison |
| Dataclasses without slots | `@dataclass(slots=True)` | Python 3.10 | Significant memory savings, faster attribute access |
| Manual `__setattr__` for immutability | `@dataclass(frozen=True)` | Python 3.7+ | Less boilerplate, mypy integration, automatic hashability |
| uuid3 (MD5) | uuid5 (SHA-1) | RFC 4122 (2005) | Stronger hash function, better collision resistance |
| Type mapping in business logic | Centralized dict/enum | Modern Python patterns | Single source of truth, easier testing |

**Deprecated/outdated:**
- **String/Enum mixin pattern**: Python 3.11's `StrEnum` replaces `class MyType(str, Enum)` pattern
- **Dataclasses without frozen for value objects**: Modern practice uses `frozen=True` for immutable semantics
- **uuid3 for new projects**: uuid5 (SHA-1) preferred over uuid3 (MD5) for deterministic UUIDs

## Open Questions

1. **Namespace UUID selection**
   - What we know: uuid5 requires a namespace UUID to partition the UUID generation space
   - What's unclear: Should we generate a project-specific namespace UUID (via uuid4) or use a well-known namespace?
   - Recommendation: Generate project-specific namespace UUID once, commit to code as constant. Avoids collisions with other systems using same names. Document in code comment.

2. **SQL type mapping completeness**
   - What we know: Microsoft Fabric warehouse supports subset of SQL Server types
   - What's unclear: Are there edge cases (e.g., money/smallmoney alternatives) we need to handle?
   - Recommendation: Start with documented Fabric warehouse types. Add handling for common SQL Server types mapped to Fabric equivalents. Document unsupported types and raise clear errors.

3. **TMDL identifier case sensitivity**
   - What we know: TMDL syntax uses identifiers that may be case-sensitive
   - What's unclear: Does TMDL treat identifiers case-sensitively? Should normalization preserve case?
   - Recommendation: Preserve original casing from source schema by default. If case-insensitive comparison needed, handle at lookup level, not normalization level.

4. **Validation error handling**
   - What we know: Whitespace validation can return list of errors
   - What's unclear: Should utilities raise exceptions or return error lists?
   - Recommendation: Pure utilities return error lists (composable, testable). Calling code decides whether to raise/log/collect errors.

## Sources

### Primary (HIGH confidence)
- [Python dataclasses documentation](https://docs.python.org/3/library/dataclasses.html) - Frozen dataclasses, slots, field defaults
- [Python uuid documentation](https://docs.python.org/3/library/uuid.html) - uuid5, namespaces, deterministic generation
- [Python enum documentation](https://docs.python.org/3/library/enum.html) - StrEnum (Python 3.11+)
- [TMDL Overview - Microsoft Learn](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview) - Identifier quoting, indentation rules, syntax specification
- [Data types in Analysis Services tabular models](https://learn.microsoft.com/en-us/analysis-services/tabular-models/data-types-supported-ssas-tabular) - Complete TMDL data type list
- [Microsoft Fabric warehouse data types](https://learn.microsoft.com/en-us/fabric/data-warehouse/data-types) - SQL types supported in Fabric

### Secondary (MEDIUM confidence)
- [Statically enforcing frozen data classes in Python | Redowan's Reflections](https://rednafi.com/python/statically-enforcing-frozen-dataclasses/) - Mypy integration patterns
- [Using mutable dataclass best practice | codereview.doctor](https://codereview.doctor/features/python/best-practice/frozen-dataclass-immutable) - Immutability patterns
- [Generating Deterministic UUIDs in Python](https://pablosanjose.com/generating-deterministic-uuids-in-python) - uuid5 best practices
- [When should I use UUID v5 for deterministic ID generation? | Inventive HQ](https://inventivehq.com/blog/when-to-use-uuid-v5-deterministic-id-generation) - uuid5 use cases
- [The case for StrEnum in Python 3.11 - tsak.dev](https://tsak.dev/posts/python-enum/) - StrEnum benefits and migration

### Tertiary (LOW confidence - general guidance)
- [Dataclasses vs Pydantic vs TypedDict vs NamedTuple in Python | Medium](https://hevalhazalkurt.medium.com/dataclasses-vs-pydantic-vs-typeddict-vs-namedtuple-in-python-85b8c03402ad) - Type pattern comparison
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/) - General Python style guidance (tabs/spaces)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib, official Python docs verified
- Architecture: HIGH - Frozen dataclasses and pure functions are well-established patterns
- Type mapping: HIGH - Both SQL Server and TMDL types documented in official Microsoft Learn
- Identifier quoting: HIGH - TMDL syntax specification is explicit and detailed
- Whitespace validation: HIGH - TMDL indentation rules clearly specified (tabs only)
- Pitfalls: MEDIUM - Based on common dataclass/uuid5 gotchas from community sources and documentation caveats

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (30 days - stable domain, stdlib features unlikely to change)
