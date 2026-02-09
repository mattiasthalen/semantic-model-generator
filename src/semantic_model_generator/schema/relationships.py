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

    # Build dimension lookup: dim_base -> (qualified_name, key_column_name)
    dim_lookup: dict[str, tuple[str, str]] = {}

    for dim in dimensions:
        # Find dimension's key column (should be exactly one)
        dim_key_cols = [
            col for col in dim.columns if strip_prefix(col.name, key_prefixes) is not None
        ]

        if len(dim_key_cols) == 1:
            dim_key_col = dim_key_cols[0]
            dim_base = strip_prefix(dim_key_col.name, key_prefixes)

            # Skip if exact match (empty base name)
            if dim_base and not is_exact_match(dim_key_col.name, key_prefixes):
                qualified_name = f"{dim.schema_name}.{dim.table_name}"
                dim_lookup[dim_base] = (qualified_name, dim_key_col.name)

    # Infer relationships from facts to dimensions
    relationships: list[Relationship] = []

    for fact in facts:
        fact_qualified = f"{fact.schema_name}.{fact.table_name}"

        # Get all key columns from fact
        fact_key_cols = [
            col for col in fact.columns if strip_prefix(col.name, key_prefixes) is not None
        ]

        for fact_col in fact_key_cols:
            # Skip exact-match columns (REQ-09)
            if is_exact_match(fact_col.name, key_prefixes):
                continue

            fact_base = strip_prefix(fact_col.name, key_prefixes)
            if fact_base is None:
                continue

            # Try exact base name match first
            if fact_base in dim_lookup:
                dim_qualified, dim_col = dim_lookup[fact_base]
                rel_id = generate_deterministic_uuid(
                    "relationship", f"{fact_qualified}.{fact_col.name}->{dim_qualified}.{dim_col}"
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
            else:
                # Try role-playing match: fact_base starts with dim_base
                for dim_base, (dim_qualified, dim_col) in dim_lookup.items():
                    # Check if fact_base starts with dim_base and has role suffix
                    if fact_base.startswith(dim_base):
                        # Verify the boundary: next char after dim_base should be underscore
                        if len(fact_base) > len(dim_base) and fact_base[len(dim_base)] == "_":
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
