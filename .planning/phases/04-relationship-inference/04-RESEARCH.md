# Phase 4: Relationship Inference - Research

**Researched:** 2026-02-09
**Domain:** Star schema relationship inference, role-playing dimension detection, tabular model relationship properties
**Confidence:** HIGH

## Summary

Phase 4 requires inferring many-to-one relationships between fact and dimension tables by matching key columns, detecting role-playing dimensions when the same dimension is referenced multiple times from a fact table, marking the first relationship active and subsequent ones inactive, and supporting exact-match prefixes that bypass role-playing detection. The research confirms this is a well-established pattern in dimensional modeling with clear detection heuristics.

Star schema relationships follow a consistent pattern: fact tables contain foreign key columns that reference dimension table primary keys, creating many-to-one relationships. Role-playing dimensions occur when a single dimension table is referenced multiple times from the same fact table with different semantic meanings (e.g., OrderDate, ShipDate, DeliveryDate all referencing the same Date dimension). Power BI tabular models enforce a single active relationship between any two tables, with additional relationships marked inactive and accessed via DAX's USERELATIONSHIP function.

The key technical challenges are: (1) matching foreign key columns in facts to primary key columns in dimensions based on name patterns and key prefix rules, (2) detecting when multiple foreign keys in the same fact reference the same dimension (role-playing), (3) applying the active/inactive marking rule (first active, subsequent inactive), and (4) handling exact-match bypass where a column name exactly matches a prefix without any suffix.

**Primary recommendation:** Use pure functional Python with frozen dataclasses to represent relationships, implement column matching with prefix-stripping logic to detect role-playing patterns, apply deterministic ordering for active/inactive marking, and handle exact-match bypass as a special case before prefix stripping. No external dependencies needed beyond Python standard library.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python standard library | 3.11+ | dataclasses, collections, itertools | Project uses frozen dataclasses pattern, functional style, no external deps for relationship logic |
| uuid (stdlib) | - | Deterministic relationship IDs | Existing project pattern via uuid_gen.py, REQ-12 requires deterministic UUIDs |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| N/A | - | - | No external libraries needed for relationship inference |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure Python logic | NetworkX graph library | NetworkX adds dependency for simple many-to-one matching; star schema relationships are trees, not complex graphs |
| Manual matching | ML-based FK detection | ML approaches (research exists) require training data and add complexity; name-based matching sufficient for prefix-driven warehouse schemas |
| Custom data structures | pandas DataFrame | pandas adds heavy dependency; immutable dataclasses align with project patterns and are sufficient |

**Installation:**
No additional dependencies required. All relationship inference uses Python standard library.

## Architecture Patterns

### Recommended Project Structure
```
src/semantic_model_generator/
├── schema/                     # Existing from Phase 3
│   ├── discovery.py            # Existing - schema metadata
│   ├── classification.py       # Existing - fact/dimension classification
│   └── relationships.py        # NEW - relationship inference
├── domain/
│   └── types.py                # Extend with Relationship dataclass
└── utils/
    └── uuid_gen.py             # Existing - deterministic UUIDs
```

### Pattern 1: Relationship Dataclass (Immutable Domain Type)
**What:** Frozen dataclass representing a single inferred relationship with TMDL properties
**When to use:** Every relationship inference operation returns these
**Example:**
```python
from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True, slots=True)
class Relationship:
    """Immutable inferred relationship between tables.

    Properties map directly to TMDL/TOM relationship object.
    """
    id: UUID  # Deterministic from generate_deterministic_uuid()
    from_table: str  # Schema-qualified: "dbo.FactSales"
    from_column: str  # Column name: "FK_CustomerID"
    to_table: str  # Schema-qualified: "dbo.DimCustomer"
    to_column: str  # Column name: "SK_CustomerID"
    is_active: bool  # True for first role-playing, False for subsequent
    cross_filtering_behavior: str = "oneDirection"  # Standard for facts->dims
    from_cardinality: str = "many"  # Fact side is always many
    to_cardinality: str = "one"  # Dimension side is always one
```

### Pattern 2: Column Name Matching with Prefix Stripping
**What:** Match fact table foreign keys to dimension table primary keys by stripping prefixes and comparing base names
**When to use:** Core relationship inference logic
**Example:**
```python
def strip_prefix(column_name: str, key_prefixes: Sequence[str]) -> str | None:
    """Strip the first matching prefix from column name, return base name.

    Args:
        column_name: e.g., "FK_CustomerID"
        key_prefixes: e.g., ["SK_", "FK_"]

    Returns:
        Base name without prefix (e.g., "CustomerID"), or None if no prefix matches
    """
    for prefix in key_prefixes:
        if column_name.startswith(prefix):
            return column_name[len(prefix):]
    return None

def matches_key_column(
    fact_col: str,
    dim_col: str,
    key_prefixes: Sequence[str]
) -> bool:
    """Check if fact column and dimension column refer to the same key.

    Example:
        FK_CustomerID (fact) matches SK_CustomerID (dim) -> True
        Both strip to "CustomerID"
    """
    fact_base = strip_prefix(fact_col, key_prefixes)
    dim_base = strip_prefix(dim_col, key_prefixes)

    if fact_base is None or dim_base is None:
        return False

    return fact_base == dim_base
```

### Pattern 3: Exact-Match Bypass Detection
**What:** Handle columns whose names exactly match a prefix (e.g., column named "SK_" with prefix "SK_") - bypass role-playing detection
**When to use:** Before role-playing pattern matching (REQ-09)
**Example:**
```python
def is_exact_match(column_name: str, key_prefixes: Sequence[str]) -> bool:
    """Check if column name exactly matches any prefix (no suffix).

    Per REQ-09: exact matches bypass role-playing detection.

    Example:
        column_name="SK_", key_prefixes=["SK_", "FK_"] -> True
        column_name="SK_CustomerID", key_prefixes=["SK_"] -> False
    """
    return column_name in key_prefixes

# In relationship inference:
if is_exact_match(fact_column, key_prefixes):
    # Bypass role-playing detection, treat as simple 1:1 match
    # These relationships are always marked active
    pass
else:
    # Apply normal prefix-stripping and role-playing logic
    pass
```

### Pattern 4: Role-Playing Dimension Detection
**What:** Detect when a fact table has multiple foreign keys referencing the same dimension table
**When to use:** After matching fact columns to dimension tables, group by target dimension
**Example:**
```python
from collections import defaultdict
from typing import Sequence

def detect_role_playing(
    relationships: Sequence[Relationship]
) -> Sequence[Relationship]:
    """Mark first relationship to each dimension active, subsequent ones inactive.

    Groups relationships by (from_table, to_table) pair. For each group:
    - First relationship: is_active=True
    - Subsequent relationships: is_active=False

    Ordering is deterministic (sort by from_column name) per REQ-08.
    """
    # Group by (from_table, to_table)
    grouped: dict[tuple[str, str], list[Relationship]] = defaultdict(list)
    for rel in relationships:
        key = (rel.from_table, rel.to_table)
        grouped[key].append(rel)

    result = []
    for (from_table, to_table), rels in grouped.items():
        if len(rels) == 1:
            # Single relationship - always active
            result.append(rels[0])
        else:
            # Multiple relationships (role-playing dimension)
            # Sort by from_column for deterministic ordering
            sorted_rels = sorted(rels, key=lambda r: r.from_column)

            # First one active, rest inactive
            result.append(sorted_rels[0])  # is_active=True
            for rel in sorted_rels[1:]:
                # Replace with inactive version
                inactive_rel = Relationship(
                    id=rel.id,
                    from_table=rel.from_table,
                    from_column=rel.from_column,
                    to_table=rel.to_table,
                    to_column=rel.to_column,
                    is_active=False,  # Mark inactive
                    cross_filtering_behavior=rel.cross_filtering_behavior,
                    from_cardinality=rel.from_cardinality,
                    to_cardinality=rel.to_cardinality,
                )
                result.append(inactive_rel)

    return tuple(result)
```

### Pattern 5: Deterministic Relationship ID Generation
**What:** Generate stable UUIDs for relationships based on from/to table and column names
**When to use:** Every relationship creation (existing project pattern)
**Example:**
```python
from semantic_model_generator.utils.uuid_gen import generate_deterministic_uuid

def create_relationship_id(
    from_table: str,
    from_column: str,
    to_table: str,
    to_column: str
) -> UUID:
    """Generate deterministic UUID for relationship.

    Uses existing project pattern from uuid_gen.py.
    Object type is "relationship", object name is composite key.
    """
    # Composite name includes all four relationship endpoints
    object_name = f"{from_table}.{from_column}->{to_table}.{to_column}"
    return generate_deterministic_uuid("relationship", object_name)
```

### Anti-Patterns to Avoid
- **Mutable relationship objects:** Use frozen dataclasses per project convention; relationships should be immutable after inference
- **Non-deterministic ordering:** Always sort before applying active/inactive marking to ensure reproducible results per REQ-33
- **Complex graph algorithms:** Star schema relationships are simple trees (facts point to dimensions); no need for graph libraries or cycle detection
- **Ignoring exact-match bypass:** REQ-09 requires special handling when column name exactly matches a prefix; must check before prefix stripping
- **Case-insensitive matching:** Per Phase 3 research, key prefix matching is case-sensitive; maintain consistency in relationship inference

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Deterministic UUID generation | Custom hashing or random IDs | Existing uuid_gen.py with uuid5 | Already established in Phase 2, REQ-12 compliance, stable across regenerations |
| Dataclass equality/hashing | Manual __eq__ and __hash__ | frozen=True, slots=True dataclasses | Python generates correct implementations, memory efficient, immutable |
| Schema-qualified names | String concatenation | Consistent pattern from existing code | Phase 3 established "schema.table" format; maintain consistency |

**Key insight:** Relationship inference is fundamentally a filtering and grouping problem over tabular data. Pure functional Python with immutable dataclasses is sufficient and aligns with project patterns. External libraries (NetworkX, pandas) add dependency weight without benefit for this simple domain.

## Common Pitfalls

### Pitfall 1: Non-Deterministic Active/Inactive Marking
**What goes wrong:** Different runs produce different active/inactive assignments when multiple relationships exist to same dimension
**Why it happens:** Python dict iteration order or unsorted list traversal before marking
**How to avoid:** Always sort relationships by from_column name before applying first=active, rest=inactive rule
**Warning signs:** Integration tests produce different TMDL output on repeated runs, git diffs show relationship isActive flips

### Pitfall 2: Forgetting Exact-Match Bypass
**What goes wrong:** Column named exactly like a prefix (e.g., "SK_") gets incorrectly stripped to empty string, causing matching failures
**Why it happens:** Prefix stripping logic applied before exact-match check
**How to avoid:** Check `column_name in key_prefixes` before attempting to strip prefix; exact matches bypass normal matching
**Warning signs:** REQ-09 tests fail, relationships with exact-match columns are missing or incorrectly classified

### Pitfall 3: Self-Referencing Relationships
**What goes wrong:** Fact table has a foreign key to itself (e.g., hierarchical fact), incorrectly detected as role-playing dimension
**Why it happens:** Not checking if from_table == to_table before classifying as dimension relationship
**How to avoid:** Filter out relationships where from_table equals to_table; star schema relationships are always fact-to-dimension (different tables)
**Warning signs:** Unexpected inactive relationships within a single table, role-playing detection triggers incorrectly

### Pitfall 4: Missing Cross-Table Validation
**What goes wrong:** Infer relationship between two fact tables or two dimension tables (invalid in star schema)
**Why it happens:** Not checking table classifications before creating relationships
**How to avoid:** Only create relationships from FACT tables to DIMENSION tables using classification results from Phase 3
**Warning signs:** Invalid relationship patterns in output, downstream TMDL generation errors

### Pitfall 5: Case Sensitivity Mismatch
**What goes wrong:** Key prefix matching works (case-sensitive from Phase 3) but relationship inference uses case-insensitive comparison
**Why it happens:** Inconsistent use of .lower() or case-insensitive comparisons
**How to avoid:** Use exact string comparison throughout; Phase 3 established case-sensitive matching, maintain consistency
**Warning signs:** Relationships inferred differently than table classification expects, test failures on mixed-case column names

### Pitfall 6: Many-to-Many Cardinality Assumption
**What goes wrong:** Star schema relationships are always many-to-one (fact to dimension), but code allows many-to-many
**Why it happens:** Not enforcing cardinality constraints in dataclass or validation
**How to avoid:** Hardcode from_cardinality="many", to_cardinality="one" per star schema definition; facts are always the many side
**Warning signs:** Incorrect relationship direction, TMDL generation creates invalid relationships

### Pitfall 7: Schema-Qualified Name Inconsistency
**What goes wrong:** Sometimes use "table_name", sometimes use "schema.table", causing UUID generation mismatches
**Why it happens:** Mixing qualified and unqualified names in relationship inference
**How to avoid:** Establish clear pattern: from_table and to_table are always schema-qualified ("dbo.FactSales"), never bare table names
**Warning signs:** Relationship UUIDs change between runs, non-deterministic output per REQ-33

## Code Examples

Verified patterns from official sources and project conventions:

### Complete Relationship Inference Function
```python
from collections.abc import Sequence
from semantic_model_generator.domain.types import (
    TableMetadata,
    TableClassification,
    Relationship
)

def infer_relationships(
    tables: Sequence[TableMetadata],
    classifications: dict[tuple[str, str], TableClassification],
    key_prefixes: Sequence[str]
) -> tuple[Relationship, ...]:
    """Infer star-schema relationships from classified tables.

    Per REQ-06: Match fact FK columns to dimension PK columns
    Per REQ-07: Detect role-playing dimensions (multiple FKs to same dim)
    Per REQ-08: First role-playing relationship active, rest inactive
    Per REQ-09: Exact-match prefixes bypass role-playing detection

    Args:
        tables: All discovered tables with column metadata
        classifications: Table classifications from Phase 3
        key_prefixes: User-supplied key prefixes (e.g., ["SK_", "FK_"])

    Returns:
        Tuple of inferred relationships, deterministically ordered
    """
    # Separate facts and dimensions based on classification
    facts = [
        t for t in tables
        if classifications.get((t.schema_name, t.table_name)) == TableClassification.FACT
    ]
    dimensions = [
        t for t in tables
        if classifications.get((t.schema_name, t.table_name)) == TableClassification.DIMENSION
    ]

    # Infer relationships: for each fact, match its key columns to dimensions
    relationships = []

    for fact in facts:
        fact_qualified_name = f"{fact.schema_name}.{fact.table_name}"

        # Find all key columns in fact (2+ by definition of fact)
        fact_key_cols = [
            col for col in fact.columns
            if any(col.name.startswith(prefix) for prefix in key_prefixes)
        ]

        # Match each fact key column to a dimension
        for fact_col in fact_key_cols:
            # Check exact-match bypass (REQ-09)
            if fact_col.name in key_prefixes:
                # Exact match - bypass role-playing, always active
                # This is a degenerate case; unclear which dimension to match
                # Skip or handle specially based on requirements clarification
                continue

            # Strip prefix from fact column
            fact_base = strip_prefix(fact_col.name, key_prefixes)
            if fact_base is None:
                continue

            # Find matching dimension column
            for dim in dimensions:
                dim_qualified_name = f"{dim.schema_name}.{dim.table_name}"

                # Dimensions have exactly 1 key column (by definition)
                dim_key_cols = [
                    col for col in dim.columns
                    if any(col.name.startswith(prefix) for prefix in key_prefixes)
                ]

                if len(dim_key_cols) != 1:
                    # Should not happen if classification is correct
                    continue

                dim_col = dim_key_cols[0]
                dim_base = strip_prefix(dim_col.name, key_prefixes)

                if dim_base is None:
                    continue

                # Match: base names are equal
                if fact_base == dim_base:
                    rel_id = create_relationship_id(
                        fact_qualified_name,
                        fact_col.name,
                        dim_qualified_name,
                        dim_col.name
                    )

                    rel = Relationship(
                        id=rel_id,
                        from_table=fact_qualified_name,
                        from_column=fact_col.name,
                        to_table=dim_qualified_name,
                        to_column=dim_col.name,
                        is_active=True,  # Initially all active
                        cross_filtering_behavior="oneDirection",
                        from_cardinality="many",
                        to_cardinality="one"
                    )
                    relationships.append(rel)
                    break  # Found match for this fact column

    # Apply role-playing dimension detection and active/inactive marking
    relationships_with_roles = detect_role_playing(relationships)

    # Sort for deterministic output (REQ-33)
    sorted_relationships = sorted(
        relationships_with_roles,
        key=lambda r: (r.from_table, r.from_column, r.to_table, r.to_column)
    )

    return tuple(sorted_relationships)
```

### Relationship to TMDL String Conversion
```python
def relationship_to_tmdl(rel: Relationship) -> str:
    """Convert Relationship dataclass to TMDL syntax string.

    Based on TMSL relationship properties and TMDL indentation rules.
    Uses tabs for indentation per Phase 2 whitespace validation.
    """
    # TMDL uses lowercase for enum values
    is_active_str = "true" if rel.is_active else "false"
    cross_filter = rel.cross_filtering_behavior  # "oneDirection" or "bothDirections"

    return f"""relationship {rel.id}
\tfromColumn: {rel.from_table}.'{rel.from_column}'
\ttoColumn: {rel.to_table}.'{rel.to_column}'
\tisActive: {is_active_str}
\tcrossFilteringBehavior: {cross_filter}
"""

# Usage:
# relationships_tmdl = "\n".join(relationship_to_tmdl(r) for r in relationships)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Duplicate dimension tables for role-playing | Inactive relationships with USERELATIONSHIP | 2016+ (Power BI relationship model) | Single dimension table, multiple relationships, cleaner model |
| Manual relationship definition | Automated inference via naming conventions | Ongoing (tooling improvement) | Reduces manual work, enforces consistency |
| Random relationship IDs | Deterministic UUIDs via uuid5 | Modern best practice | Stable git diffs, reproducible output |
| Mutable relationship objects | Frozen dataclasses | Python 3.7+ (dataclasses) | Immutability guarantees, better type safety |

**Deprecated/outdated:**
- **Creating duplicate dimension tables:** Modern Power BI uses inactive relationships instead; duplicate tables bloat model size
- **Non-deterministic relationship IDs:** Random UUIDs cause unnecessary git churn; uuid5 solves this (REQ-12, REQ-33)
- **Manual relationship creation:** Name-based inference is standard in modern semantic modeling tools

## Open Questions

1. **Exact-match prefix handling for relationships**
   - What we know: REQ-09 says exact-match bypasses role-playing detection
   - What's unclear: If column is named exactly "SK_" (matches prefix exactly), which dimension does it reference? No base name to match against.
   - Recommendation: Clarify requirement during planning. Options: (a) skip these as invalid, (b) match to dimension with exact-match column of same name, (c) treat as special case requiring manual configuration

2. **Multi-column foreign keys (composite keys)**
   - What we know: Star schema typically uses surrogate keys (single column)
   - What's unclear: Should we handle fact tables with composite foreign keys (multiple columns referencing same dimension)?
   - Recommendation: Scope to single-column relationships for Phase 4; composite keys are rare in star schemas with surrogate keys. Defer to future enhancement.

3. **Cross-schema relationships**
   - What we know: Tables can be in different schemas (REQ-02 supports multiple schemas)
   - What's unclear: Should relationship inference work across schemas, or only within same schema?
   - Recommendation: Support cross-schema (e.g., dbo.FactSales -> reference.DimDate). Schema qualification in from_table/to_table makes this automatic.

4. **Cardinality validation**
   - What we know: Star schema relationships are many-to-one (fact to dimension)
   - What's unclear: Should we validate actual data cardinality, or trust schema structure?
   - Recommendation: Trust schema structure (classification + key count). Data cardinality validation requires querying rows, outside Phase 4 scope.

5. **Bi-directional filtering for certain dimensions**
   - What we know: Standard is oneDirection (dimension filters fact)
   - What's unclear: Some patterns use bothDirections (e.g., security tables). Should inference support this?
   - Recommendation: Default to oneDirection per star schema best practices. Expose as optional parameter for advanced users, but not auto-detected.

## Sources

### Primary (HIGH confidence)
- [Microsoft Learn: Active vs Inactive Relationship Guidance](https://learn.microsoft.com/en-us/power-bi/guidance/relationships-active-inactive) - Role-playing dimensions, active/inactive rules
- [Microsoft Learn: Relationships Object (TMSL)](https://learn.microsoft.com/en-us/analysis-services/tmsl/relationships-object-tmsl?view=sql-analysis-services-2025) - Complete relationship property definitions
- [Microsoft Learn: Tabular Model Definition Language (TMDL)](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025) - TMDL relationship syntax
- [Microsoft Learn: Star Schema in Power BI](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema) - Fact/dimension relationship patterns
- [Kimball Group: Role-Playing Dimension](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/role-playing-dimension/) - Role-playing dimension definition and patterns
- [Python Documentation: dataclasses](https://docs.python.org/3/library/dataclasses.html) - Frozen dataclass patterns
- [Tabular Editor: Relationship Class](https://docs.tabulareditor.com/api/TabularEditor.TOMWrapper.Relationship.html) - TOM relationship properties
- [Tabular Editor: SingleColumnRelationship Class](https://docs.tabulareditor.com/api/TabularEditor.TOMWrapper.SingleColumnRelationship.html) - Single-column relationship specifics

### Secondary (MEDIUM confidence)
- [RADACAD: UseRelationship or Role-Playing Dimension](https://radacad.com/userelationship-or-role-playing-dimension-dealing-with-inactive-relationships-in-power-bi/) - Practical role-playing patterns
- [Medium: Effective Relationship Management in Power BI](https://medium.com/@santhiyab/effective-relationship-management-in-power-bi-userelationship-vs-role-playing-dimensions-7108a9cedea6) - Role-playing vs USERELATIONSHIP tradeoffs
- [Prologika: Implementing Role-playing Dimensions in Power BI](https://prologika.com/implementing-role-playing-dimensions-in-power-bi/) - Implementation approaches
- [Erik Edin: Using AI to Automate Foreign Key Discovery](https://erikedin.com/2024/09/30/using-ai-to-automate-foreign-key-discovery/) - ML-based FK detection (not recommended for this project)
- [ResearchGate: A Machine Learning Approach to Foreign Key Discovery](https://www.researchgate.net/publication/221035501_A_Machine_Learning_Approach_to_Foreign_Key_Discovery) - Academic research on FK detection algorithms

### Tertiary (LOW confidence)
- Various Power BI Community forum discussions on role-playing dimensions - Cross-verified patterns with official docs before including

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Pure Python stdlib, aligns with project patterns (frozen dataclasses, functional style, uuid_gen)
- Architecture: HIGH - Patterns verified from Microsoft official docs (TMSL, TMDL, Power BI guidance) and existing project conventions
- Pitfalls: MEDIUM-HIGH - Role-playing detection and active/inactive marking well-documented in official sources; exact-match bypass needs requirement clarification

**Research date:** 2026-02-09
**Valid until:** 2026-04-09 (60 days - stable domain, TMDL and Power BI relationship model mature, patterns established)
