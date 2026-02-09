"""Relationship inference for star schema models."""

from collections.abc import Sequence

from semantic_model_generator.domain.types import (
    Relationship,
    TableClassification,
    TableMetadata,
)
from semantic_model_generator.utils.uuid_gen import generate_deterministic_uuid


def strip_prefix(column_name: str, key_prefixes: Sequence[str]) -> str | None:
    """Strip first matching key prefix from column name.

    Args:
        column_name: Column name to strip prefix from.
        key_prefixes: Ordered sequence of key prefixes to try.

    Returns:
        Base name after stripping first matching prefix, or None if no prefix matches.
        Returns empty string if column name exactly matches a prefix.
    """
    for prefix in key_prefixes:
        if column_name.startswith(prefix):
            return column_name[len(prefix) :]
    return None


def is_exact_match(column_name: str, key_prefixes: Sequence[str]) -> bool:
    """Check if column name exactly matches any key prefix.

    Args:
        column_name: Column name to check.
        key_prefixes: Sequence of key prefixes.

    Returns:
        True if column_name is in key_prefixes, False otherwise.
    """
    return column_name in key_prefixes


def infer_relationships(
    tables: Sequence[TableMetadata],
    classifications: dict[tuple[str, str], TableClassification],
    key_prefixes: Sequence[str],
) -> tuple[Relationship, ...]:
    """Infer star-schema relationships between fact and dimension tables.

    Matching is done by checking if fact column names START WITH dimension column names.
    Both fact and dimension columns use the same key prefixes.

    Example:
        - Dimension column: ID_Customer
        - Fact exact match: ID_Customer (same name)
        - Fact role-playing: ID_Customer_BillTo (starts with ID_Customer)

    Args:
        tables: Sequence of table metadata.
        classifications: Dict mapping (schema, table) to TableClassification.
        key_prefixes: Sequence of key column prefixes for matching.

    Returns:
        Tuple of Relationship objects, sorted deterministically.
    """
    if not tables:
        return ()

    # Separate tables into facts and dimensions
    facts: list[TableMetadata] = []
    dimensions: list[TableMetadata] = []

    for table in tables:
        classification = classifications.get((table.schema_name, table.table_name))
        if classification == TableClassification.FACT:
            facts.append(table)
        elif classification == TableClassification.DIMENSION:
            dimensions.append(table)

    # Build dimension lookup: dim_column_name -> (qualified_name, key_column_name)
    # We keep the full column name with prefix, NO stripping
    dim_lookup: dict[str, tuple[str, str]] = {}

    for dim in dimensions:
        # Find dimension's key column (should be exactly one)
        # A key column is one that starts with any of the key prefixes
        dim_key_cols = [
            col
            for col in dim.columns
            if any(col.name.startswith(prefix) for prefix in key_prefixes)
            and not is_exact_match(col.name, key_prefixes)
        ]

        if len(dim_key_cols) == 1:
            dim_key_col = dim_key_cols[0]
            qualified_name = f"{dim.schema_name}.{dim.table_name}"
            # Store the FULL column name, not stripped
            dim_lookup[dim_key_col.name] = (qualified_name, dim_key_col.name)

    # Infer relationships from facts to dimensions
    relationships: list[Relationship] = []

    for fact in facts:
        fact_qualified = f"{fact.schema_name}.{fact.table_name}"

        # Get all key columns from fact (columns starting with any key prefix)
        fact_key_cols = [
            col
            for col in fact.columns
            if any(col.name.startswith(prefix) for prefix in key_prefixes)
        ]

        for fact_col in fact_key_cols:
            # Skip exact-match columns (REQ-09)
            if is_exact_match(fact_col.name, key_prefixes):
                continue

            # Check if fact column starts with any dimension column
            # This handles both exact match and role-playing cases
            for dim_col_name, (dim_qualified, dim_col) in dim_lookup.items():
                if fact_col.name.startswith(dim_col_name):
                    # For role-playing, require underscore boundary
                    # If fact column equals dim column exactly, it's a direct match
                    # If fact column is longer, next char must be underscore
                    if fact_col.name == dim_col_name or (
                        len(fact_col.name) > len(dim_col_name)
                        and fact_col.name[len(dim_col_name)] == "_"
                    ):
                        rel_id = generate_deterministic_uuid(
                            "relationship",
                            f"{fact_qualified}.{fact_col.name}->{dim_qualified}.{dim_col}",
                        )
                        relationships.append(
                            Relationship(
                                id=rel_id,
                                from_table=fact_qualified,
                                from_column=fact_col.name,
                                to_table=dim_qualified,
                                to_column=dim_col,
                                is_active=True,
                            )
                        )
                        break  # Only match first dimension

    # Apply role-playing detection: mark inactive relationships
    # Group by (from_table, to_table)
    from collections import defaultdict

    groups: defaultdict[tuple[str, str], list[Relationship]] = defaultdict(list)
    for rel in relationships:
        groups[(rel.from_table, rel.to_table)].append(rel)

    # Process each group
    final_relationships: list[Relationship] = []
    for group_rels in groups.values():
        if len(group_rels) == 1:
            # Single relationship - always active
            final_relationships.append(group_rels[0])
        else:
            # Multiple relationships (role-playing)
            # Sort by from_column to determine which is active
            sorted_rels = sorted(group_rels, key=lambda r: r.from_column)

            # First is active, rest are inactive
            final_relationships.append(sorted_rels[0])

            for rel in sorted_rels[1:]:
                # Create new relationship with is_active=False (frozen dataclass)
                inactive_rel = Relationship(
                    id=rel.id,
                    from_table=rel.from_table,
                    from_column=rel.from_column,
                    to_table=rel.to_table,
                    to_column=rel.to_column,
                    is_active=False,
                    cross_filtering_behavior=rel.cross_filtering_behavior,
                    from_cardinality=rel.from_cardinality,
                    to_cardinality=rel.to_cardinality,
                )
                final_relationships.append(inactive_rel)

    # Sort deterministically by (from_table, from_column, to_table, to_column)
    final_relationships.sort(key=lambda r: (r.from_table, r.from_column, r.to_table, r.to_column))

    return tuple(final_relationships)
