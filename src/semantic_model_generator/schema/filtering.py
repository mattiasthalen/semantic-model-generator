"""Table filtering by include and exclude lists."""

from collections.abc import Sequence

from semantic_model_generator.domain.types import TableMetadata


def filter_tables(
    tables: Sequence[TableMetadata],
    include: Sequence[str] | None = None,
    exclude: Sequence[str] | None = None,
) -> list[TableMetadata]:
    """Filter tables by include and/or exclude lists.

    - If include is not None: only tables whose table_name is in include are kept
    - If exclude is not None: tables whose table_name is in exclude are removed
    - Both can be combined: include is applied first, then exclude
    - If both are None: all tables are returned unchanged

    Args:
        tables: Sequence of table metadata to filter
        include: Optional list of table names to include (exact match, case-sensitive)
        exclude: Optional list of table names to exclude (exact match, case-sensitive)

    Returns:
        Filtered list of table metadata objects
    """
    result: Sequence[TableMetadata] = tables

    if include is not None:
        include_set = set(include)
        result = [t for t in result if t.table_name in include_set]

    if exclude is not None:
        exclude_set = set(exclude)
        result = [t for t in result if t.table_name not in exclude_set]

    return list(result)
