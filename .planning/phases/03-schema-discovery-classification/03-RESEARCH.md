# Phase 3: Schema Discovery & Classification - Research

**Researched:** 2026-02-09
**Domain:** Database connectivity (Microsoft Fabric warehouse), schema metadata discovery, star schema classification
**Confidence:** HIGH

## Summary

Phase 3 requires connecting to a Microsoft Fabric warehouse using token-based authentication, reading schema metadata from INFORMATION_SCHEMA views, filtering tables, and classifying them as fact or dimension based on key column counts. The research confirms that pyodbc with ODBC Driver 18 is the standard choice for Fabric warehouse connectivity with Microsoft Entra ID authentication, while frozen dataclasses align perfectly with the project's existing patterns for representing immutable schema metadata.

Token authentication in pyodbc requires encoding tokens from azure-identity's DefaultAzureCredential, passing them via the SQL_COPT_SS_ACCESS_TOKEN attribute. INFORMATION_SCHEMA.COLUMNS and INFORMATION_SCHEMA.TABLES provide standard SQL metadata access with permission-based filtering. Table classification heuristics are straightforward: dimension tables typically have a single primary key column, while fact tables have composite keys (multiple foreign key columns referencing dimensions).

**Primary recommendation:** Use pyodbc with ODBC Driver 18, azure-identity for token acquisition, frozen dataclasses for schema metadata, and functional patterns for filtering and classification logic. Add tenacity for transient failure retry logic.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pyodbc | 5.x | ODBC database connectivity | Microsoft-recommended driver for Azure/Fabric SQL with token auth support |
| azure-identity | 1.19+ | Microsoft Entra ID authentication | Official Azure SDK for token acquisition, supports DefaultAzureCredential |
| ODBC Driver 18 for SQL Server | 18+ | System ODBC driver | Required by Microsoft Fabric (ODBC 18+ mandatory), provides modern security features |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tenacity | 9.1+ | Retry logic for transient failures | Handling token expiration, network issues, and transient SQL errors |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pyodbc | pymssql | pymssql lacks token authentication support and has SSL/encryption limitations for Azure SQL |
| pyodbc | SQLAlchemy + pyodbc | SQLAlchemy adds ORM overhead; direct pyodbc is lighter for metadata queries |
| azure-identity | Manual token handling | azure-identity handles token lifecycle, credential chains, and refresh automatically |

**Installation:**
```bash
pip install pyodbc azure-identity tenacity
```

**System dependency:**
- ODBC Driver 18 for SQL Server (varies by OS: apt/brew/chocolatey/manual installer)

## Architecture Patterns

### Recommended Project Structure
```
src/semantic_model_generator/
├── schema/                    # New for Phase 3
│   ├── connection.py          # Connection factory with token auth
│   ├── discovery.py           # INFORMATION_SCHEMA queries
│   ├── filtering.py           # Include/exclude list filtering
│   └── classification.py      # Fact/dimension classification logic
├── domain/
│   └── types.py               # Extend with SchemaMetadata, TableClassification
└── utils/                     # From Phase 2
```

### Pattern 1: Token-Based Connection Factory
**What:** Acquire token from azure-identity, encode it for pyodbc, and establish connection with proper error handling
**When to use:** Every database connection to Fabric warehouse
**Example:**
```python
# Source: https://debruyn.dev/2023/connect-to-fabric-lakehouses-warehouses-from-python-code/
# and https://learn.microsoft.com/en-us/fabric/data-warehouse/connectivity
from azure.identity import DefaultAzureCredential
import struct
from itertools import chain, repeat
import pyodbc

def create_connection(sql_endpoint: str, database: str) -> pyodbc.Connection:
    """Create authenticated connection to Fabric warehouse."""
    credential = DefaultAzureCredential()
    token_object = credential.get_token("https://database.windows.net//.default")

    # Encode token as UTF-16-LE for ODBC driver
    token_as_bytes = bytes(token_object.token, "UTF-8")
    encoded_bytes = bytes(chain.from_iterable(zip(token_as_bytes, repeat(0))))
    token_bytes = struct.pack("<i", len(encoded_bytes)) + encoded_bytes

    # SQL_COPT_SS_ACCESS_TOKEN = 1256
    attrs_before = {1256: token_bytes}

    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={sql_endpoint},1433;"
        f"Database={database};"
        f"Encrypt=Yes;"
        f"TrustServerCertificate=No"
    )

    return pyodbc.connect(connection_string, attrs_before=attrs_before)
```

### Pattern 2: INFORMATION_SCHEMA Queries with Permission-Aware Results
**What:** Query INFORMATION_SCHEMA views to read table and column metadata, filter by schema names and table types
**When to use:** Schema discovery step
**Example:**
```python
# Source: https://learn.microsoft.com/en-us/sql/relational-databases/system-information-schema-views/columns-transact-sql
def read_table_columns(
    conn: pyodbc.Connection,
    schemas: list[str]
) -> list[dict[str, any]]:
    """Read columns for BASE TABLEs in specified schemas."""
    schema_list = ", ".join(f"'{s}'" for s in schemas)

    query = f"""
    SELECT
        c.TABLE_SCHEMA,
        c.TABLE_NAME,
        c.COLUMN_NAME,
        c.DATA_TYPE,
        c.IS_NULLABLE,
        c.ORDINAL_POSITION,
        c.CHARACTER_MAXIMUM_LENGTH,
        c.NUMERIC_PRECISION,
        c.NUMERIC_SCALE
    FROM INFORMATION_SCHEMA.COLUMNS c
    INNER JOIN INFORMATION_SCHEMA.TABLES t
        ON c.TABLE_SCHEMA = t.TABLE_SCHEMA
        AND c.TABLE_NAME = t.TABLE_NAME
    WHERE t.TABLE_TYPE = 'BASE TABLE'
        AND t.TABLE_SCHEMA IN ({schema_list})
    ORDER BY c.TABLE_SCHEMA, c.TABLE_NAME, c.ORDINAL_POSITION
    """

    cursor = conn.cursor()
    cursor.execute(query)
    return [dict(zip([col[0] for col in cursor.description], row))
            for row in cursor.fetchall()]
```

### Pattern 3: Frozen Dataclass for Schema Metadata (Existing Pattern)
**What:** Use frozen dataclasses with slots for immutable schema metadata objects
**When to use:** Representing discovered schema metadata (already established in Phase 2)
**Example:**
```python
# Source: Existing project pattern from domain/types.py
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class TableMetadata:
    """Immutable metadata for a warehouse table."""
    schema_name: str
    table_name: str
    columns: tuple[ColumnMetadata, ...]
    table_type: str  # 'dimension' or 'fact'
```

### Pattern 4: Functional Table Filtering
**What:** Pure functions to filter tables by include/exclude lists
**When to use:** Applying user-specified table filtering rules
**Example:**
```python
def filter_tables(
    tables: list[TableMetadata],
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None
) -> list[TableMetadata]:
    """Filter tables by include/exclude lists.

    - If include_patterns specified: only tables matching at least one pattern
    - If exclude_patterns specified: tables matching any pattern are removed
    - Both can be combined: include first, then exclude
    """
    result = tables

    if include_patterns:
        result = [t for t in result
                  if any(pattern_matches(t.table_name, p) for p in include_patterns)]

    if exclude_patterns:
        result = [t for t in result
                  if not any(pattern_matches(t.table_name, p) for p in exclude_patterns)]

    return result
```

### Pattern 5: Retry Logic with Tenacity
**What:** Use tenacity decorator for retry logic on transient database errors
**When to use:** Connection establishment and query execution
**Example:**
```python
# Source: https://tenacity.readthedocs.io/
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import pyodbc

@retry(
    retry=retry_if_exception_type((pyodbc.OperationalError, pyodbc.Error)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def execute_metadata_query(conn: pyodbc.Connection, query: str) -> list[any]:
    """Execute query with retry logic for transient failures."""
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()
```

### Anti-Patterns to Avoid
- **String interpolation in SQL queries:** Always use parameterization for values, though schema/table names must be validated via allowlists (INFORMATION_SCHEMA inherently safe since we control schema names)
- **fetchall() for large result sets:** Use fetchmany() with cursor.arraysize for memory efficiency, though metadata queries are typically small
- **Ignoring connection context managers:** Always use `with connection:` or explicit close to prevent connection leaks
- **Hardcoded connection timeouts:** Token lifetime is ~24 hours, but connections should be short-lived for metadata queries
- **Not filtering views:** INFORMATION_SCHEMA.TABLES includes views; always filter to `TABLE_TYPE = 'BASE TABLE'` per REQ-29

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token acquisition and refresh | Custom OAuth flow | azure-identity.DefaultAzureCredential | Handles credential chains (CLI, managed identity, environment variables), token caching, and refresh automatically |
| Retry logic with backoff | Custom retry loops | tenacity library | Provides exponential backoff, jitter, selective retry by exception type, async support |
| Token encoding for ODBC | Manual byte manipulation | Standard pattern (UTF-16-LE + struct.pack) | Well-documented pattern, edge cases handled (multibyte characters, padding) |
| Connection pooling | Custom pool implementation | pyodbc + ODBC driver pooling | ODBC driver manager handles pooling at system level; application-level pooling adds complexity |

**Key insight:** Microsoft Fabric authentication and database connectivity have specific encoding requirements and transient failure modes. Established libraries (azure-identity, tenacity) handle these edge cases that are easy to miss in custom implementations.

## Common Pitfalls

### Pitfall 1: Token Expiration in Long-Running Processes
**What goes wrong:** Token acquired once at startup expires after ~24 hours, causing authentication failures mid-run
**Why it happens:** Managed identity tokens cached for 24 hours, no automatic refresh in connection object
**How to avoid:** Acquire fresh token per connection, keep connections short-lived (close after metadata query completes)
**Warning signs:** pyodbc.OperationalError after long idle periods, "token expired" in error messages

### Pitfall 2: Connection String Must Exclude Auth Parameters for Token Auth
**What goes wrong:** Including `Authentication=`, `UID=`, or `PWD=` in connection string causes FA005 error when using token
**Why it happens:** Token authentication (attrs_before with SQL_COPT_SS_ACCESS_TOKEN) conflicts with connection string auth
**How to avoid:** Connection string must only have Driver, Server, Database, Encrypt, TrustServerCertificate when using token
**Warning signs:** FA005 error, "Attribute cannot be set" error messages

### Pitfall 3: Schema Name Case Sensitivity
**What goes wrong:** Filtering fails because user provides schema names with wrong case (e.g., 'DBO' vs 'dbo')
**Why it happens:** SQL Server schema names are case-insensitive, but INFORMATION_SCHEMA returns exact case
**How to avoid:** Normalize schema names (lowercase) before filtering, or use case-insensitive comparison
**Warning signs:** Zero tables discovered when tables definitely exist, empty result sets

### Pitfall 4: INFORMATION_SCHEMA Returns Only Accessible Objects
**What goes wrong:** Missing tables in results, assuming they don't exist
**Why it happens:** INFORMATION_SCHEMA views are permission-based; only returns objects current user can access
**How to avoid:** Document permission requirements (at minimum SELECT permission on target schemas), fail gracefully with clear error when schema is empty
**Warning signs:** Unexpectedly empty results, fewer tables than expected

### Pitfall 5: View vs Table Detection
**What goes wrong:** Views included in discovery, causing downstream relationship inference failures
**Why it happens:** INFORMATION_SCHEMA.COLUMNS returns both table and view columns without TABLE_TYPE
**How to avoid:** Join to INFORMATION_SCHEMA.TABLES and filter WHERE TABLE_TYPE = 'BASE TABLE' per REQ-29
**Warning signs:** Unexpected "tables" without proper key structure, views mixed with tables in output

### Pitfall 6: Key Column Detection Logic
**What goes wrong:** Classifying tables incorrectly when key prefix matching is too loose or too strict
**Why it happens:** Column names may contain key prefixes as substrings, not just at start
**How to avoid:** Use prefix matching (column_name.startswith(prefix)), not substring search; REQ-05 specifies user-supplied prefixes must be exact
**Warning signs:** Dimension tables classified as facts, or fact tables with single foreign key classified as dimensions

### Pitfall 7: Composite Key Handling in Classification
**What goes wrong:** Fact table with single composite key (multiple columns) misclassified as dimension
**Why it happens:** Counting columns that match ANY key prefix, not counting unique key column occurrences
**How to avoid:** Count distinct columns matching key prefixes; ≥2 key columns → fact, exactly 1 key column → dimension per REQ-04
**Warning signs:** Multi-column keyed fact tables classified as dimensions

## Code Examples

Verified patterns from official sources:

### Connection with Token Authentication
```python
# Source: https://debruyn.dev/2023/connect-to-fabric-lakehouses-warehouses-from-python-code/
from azure.identity import DefaultAzureCredential
import struct
from itertools import chain, repeat
import pyodbc

def get_fabric_connection(sql_endpoint: str, database: str) -> pyodbc.Connection:
    credential = DefaultAzureCredential()
    token_object = credential.get_token("https://database.windows.net//.default")
    token_as_bytes = bytes(token_object.token, "UTF-8")
    encoded_bytes = bytes(chain.from_iterable(zip(token_as_bytes, repeat(0))))
    token_bytes = struct.pack("<i", len(encoded_bytes)) + encoded_bytes
    attrs_before = {1256: token_bytes}  # SQL_COPT_SS_ACCESS_TOKEN

    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={sql_endpoint},1433;"
        f"Database={database};"
        f"Encrypt=Yes;"
        f"TrustServerCertificate=No"
    )

    return pyodbc.connect(connection_string, attrs_before=attrs_before)
```

### Schema Discovery with View Filtering
```python
# Source: https://learn.microsoft.com/en-us/sql/relational-databases/system-information-schema-views/
def discover_tables_and_columns(
    conn: pyodbc.Connection,
    schemas: list[str]
) -> dict[str, list[dict]]:
    """Discover BASE TABLEs and their columns for specified schemas."""
    # Build parameterized WHERE clause (schemas are validated input, not user strings)
    schema_placeholders = ", ".join("?" * len(schemas))

    query = f"""
    SELECT
        t.TABLE_SCHEMA,
        t.TABLE_NAME,
        c.COLUMN_NAME,
        c.DATA_TYPE,
        c.IS_NULLABLE,
        c.ORDINAL_POSITION,
        c.CHARACTER_MAXIMUM_LENGTH,
        c.NUMERIC_PRECISION,
        c.NUMERIC_SCALE
    FROM INFORMATION_SCHEMA.TABLES t
    INNER JOIN INFORMATION_SCHEMA.COLUMNS c
        ON t.TABLE_SCHEMA = c.TABLE_SCHEMA
        AND t.TABLE_NAME = c.TABLE_NAME
    WHERE t.TABLE_TYPE = 'BASE TABLE'
        AND t.TABLE_SCHEMA IN ({schema_placeholders})
    ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION
    """

    cursor = conn.cursor()
    cursor.execute(query, schemas)

    results = {}
    for row in cursor.fetchall():
        key = (row[0], row[1])  # (schema, table)
        if key not in results:
            results[key] = []
        results[key].append({
            "column_name": row[2],
            "data_type": row[3],
            "is_nullable": row[4] == "YES",
            "ordinal_position": row[5],
            "max_length": row[6],
            "numeric_precision": row[7],
            "numeric_scale": row[8]
        })

    return results
```

### Table Classification by Key Count
```python
# Source: Star schema patterns from
# https://learn.microsoft.com/en-us/power-bi/guidance/star-schema
def classify_table(
    columns: list[ColumnMetadata],
    key_prefixes: list[str]
) -> str:
    """Classify table as 'dimension' or 'fact' based on key column count.

    Per REQ-04:
    - Exactly 1 key column → dimension (single primary key)
    - 2+ key columns → fact (composite key from multiple foreign keys)
    - 0 key columns → unclassified (not dimension or fact)
    """
    key_columns = [
        col for col in columns
        if any(col.name.startswith(prefix) for prefix in key_prefixes)
    ]

    key_count = len(key_columns)

    if key_count == 1:
        return "dimension"
    elif key_count >= 2:
        return "fact"
    else:
        # No key columns - neither dimension nor fact
        # This might be a staging table or invalid structure
        return "unclassified"
```

### Retry Logic for Transient Errors
```python
# Source: https://tenacity.readthedocs.io/
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import pyodbc

@retry(
    retry=retry_if_exception_type((pyodbc.OperationalError, pyodbc.InterfaceError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def query_with_retry(conn: pyodbc.Connection, query: str, params: tuple = ()) -> list:
    """Execute query with automatic retry on transient errors."""
    cursor = conn.cursor()
    cursor.execute(query, params)
    return cursor.fetchall()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pymssql | pyodbc with ODBC Driver 18 | 2023+ (Fabric launch) | Token auth support, better Azure integration, ODBC 18 mandatory for Fabric |
| SQL authentication | Microsoft Entra ID (token) | 2023 (Fabric requirement) | No SQL auth supported in Fabric, token-based only |
| Manual token management | azure-identity library | 2020+ (Azure SDK v2) | Standardized credential chains, automatic refresh handling |
| Connection string auth | Token via attrs_before | ODBC Driver 17+ | Token passed separately from connection string, cleaner security model |
| Manual retry loops | tenacity library | 2015+ (library mature) | Declarative retry logic, less boilerplate, fewer bugs |

**Deprecated/outdated:**
- **pymssql for Fabric:** No token auth support, SSL issues with Azure
- **SQL authentication:** Not supported in Fabric warehouses (Entra ID only)
- **ODBC Driver 17 or older:** Fabric requires ODBC Driver 18+
- **Manual credential acquisition:** azure-identity.DefaultAzureCredential is the standard pattern

## Open Questions

1. **Schema-level permissions vs database-level permissions**
   - What we know: INFORMATION_SCHEMA returns only accessible objects
   - What's unclear: Minimum permission required (SELECT vs CONTROL vs VIEW DEFINITION)
   - Recommendation: Document that user needs SELECT permission on target schemas; test with minimal permissions during implementation

2. **Token lifetime in Fabric vs standard Azure SQL**
   - What we know: Managed identity tokens ~24 hour lifetime
   - What's unclear: Whether Fabric has different token expiration policies
   - Recommendation: Assume standard 24-hour lifetime, design for short-lived connections (no pooling)

3. **INFORMATION_SCHEMA performance on large schemas**
   - What we know: Standard SQL queries, should be fast
   - What's unclear: Performance characteristics with 1000+ table schemas
   - Recommendation: Use fetchmany() pattern for memory safety, measure in integration tests

4. **Key prefix matching: case sensitivity**
   - What we know: REQ-05 says user-supplied prefixes, no specification of case handling
   - What's unclear: Should prefix matching be case-sensitive or case-insensitive?
   - Recommendation: Make it case-sensitive (exact match) for consistency with SQL Server column names, document in function signature

5. **Multiple schema handling**
   - What we know: REQ-02 says "user-specified schemas" (plural)
   - What's unclear: Should we merge results across schemas, or keep them separate?
   - Recommendation: Merge into single metadata collection, qualified by schema_name field (existing pattern in TableMetadata)

## Sources

### Primary (HIGH confidence)
- [Microsoft Learn: Fabric Data Warehouse Connectivity](https://learn.microsoft.com/en-us/fabric/data-warehouse/connectivity) - Authentication methods, connection requirements
- [Microsoft Learn: How to Connect to Fabric Warehouse](https://learn.microsoft.com/en-us/fabric/data-warehouse/how-to-connect) - Connection string format, endpoint structure
- [Microsoft Learn: INFORMATION_SCHEMA.COLUMNS](https://learn.microsoft.com/en-us/sql/relational-databases/system-information-schema-views/columns-transact-sql) - Standard metadata query structure
- [Microsoft Learn: Star Schema in Power BI](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema) - Fact/dimension patterns
- [Sam Debruyn: Connect to Fabric Lakehouses & Warehouses from Python](https://debruyn.dev/2023/connect-to-fabric-lakehouses-warehouses-from-python-code/) - Token encoding pattern, complete code example
- [Tenacity Documentation](https://tenacity.readthedocs.io/) - Retry patterns and decorator usage
- [pyodbc Wiki: Cursor](https://github.com/mkleehammer/pyodbc/wiki/Cursor) - fetchmany vs fetchall patterns
- [Python Documentation: dataclasses](https://docs.python.org/3/library/dataclasses.html) - frozen, slots configuration

### Secondary (MEDIUM confidence)
- [Microsoft Community Hub: Azure SQL with Managed Identity and Python ODBC](https://techcommunity.microsoft.com/blog/azuredbsupport/lessons-learned-534-azure-sql-database-connections-with-managed-identity-and-pyt/4439061) - Token handling edge cases
- [OWASP: SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html) - Parameterization best practices
- [Kimball Group: Dimensional Modeling Techniques](https://www.kimballgroup.com/wp-content/uploads/2013/08/2013.09-Kimball-Dimensional-Modeling-Techniques11.pdf) - Star schema classification heuristics
- [Medium: Connect to Fabric Warehouse using SQLAlchemy](https://medium.com/@mariusz_kujawski/connect-to-microsoft-fabric-warehouse-using-python-and-sqlalchemy-1e1179855037) - Alternative approaches (SQLAlchemy not recommended for this use case)

### Tertiary (LOW confidence)
- [Various StackOverflow/Medium articles on pyodbc patterns] - Cross-verified with official docs before including

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official Microsoft docs confirm pyodbc + azure-identity + ODBC Driver 18 as the standard pattern
- Architecture: HIGH - Patterns verified from Microsoft Learn and established community examples (Sam Debruyn blog widely referenced)
- Pitfalls: MEDIUM-HIGH - Token expiration and connection string conflicts verified in official docs; classification pitfalls based on star schema best practices

**Research date:** 2026-02-09
**Valid until:** 2026-04-09 (60 days - stable domain, Microsoft Fabric 1+ year old, patterns mature)
