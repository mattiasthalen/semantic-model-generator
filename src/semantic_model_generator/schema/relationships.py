"""Relationship inference for star schema models."""

from collections.abc import Sequence

from semantic_model_generator.domain.types import (
    Relationship,
    TableClassification,
    TableMetadata,
)


def strip_prefix(column_name: str, key_prefixes: Sequence[str]) -> str | None:
    """Strip first matching key prefix from column name.

    Args:
        column_name: Column name to strip prefix from.
        key_prefixes: Ordered sequence of key prefixes to try.

    Returns:
        Base name after stripping first matching prefix, or None if no prefix matches.
        Returns empty string if column name exactly matches a prefix.
    """
    raise NotImplementedError


def is_exact_match(column_name: str, key_prefixes: Sequence[str]) -> bool:
    """Check if column name exactly matches any key prefix.

    Args:
        column_name: Column name to check.
        key_prefixes: Sequence of key prefixes.

    Returns:
        True if column_name is in key_prefixes, False otherwise.
    """
    raise NotImplementedError


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
    raise NotImplementedError
