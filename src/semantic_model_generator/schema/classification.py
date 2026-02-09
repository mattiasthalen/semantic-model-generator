"""Table classification by key column count.

Classifies warehouse tables as dimension, fact, or unclassified
based on the number of columns matching user-supplied key prefixes.

Per REQ-04:
- 1 key column -> dimension (single primary/surrogate key)
- 2+ key columns -> fact (composite foreign keys)
- 0 key columns -> unclassified
"""

from collections.abc import Sequence

from semantic_model_generator.domain.types import (
    ColumnMetadata,
    TableClassification,
    TableMetadata,
)


def classify_table(
    columns: Sequence[ColumnMetadata],
    key_prefixes: Sequence[str],
) -> TableClassification:
    """Classify a single table by counting key columns.

    Key columns are those whose name starts with any of the given prefixes.
    Matching is case-sensitive (per research recommendation).

    Args:
        columns: Sequence of column metadata for the table
        key_prefixes: List of prefixes to identify key columns (case-sensitive)

    Returns:
        TableClassification: DIMENSION (1 key), FACT (2+ keys), or UNCLASSIFIED (0 keys)
    """
    key_count = sum(
        1 for col in columns if any(col.name.startswith(prefix) for prefix in key_prefixes)
    )

    if key_count == 1:
        return TableClassification.DIMENSION
    elif key_count >= 2:
        return TableClassification.FACT
    else:
        return TableClassification.UNCLASSIFIED


def classify_tables(
    tables: Sequence[TableMetadata],
    key_prefixes: Sequence[str],
) -> dict[tuple[str, str], TableClassification]:
    """Classify multiple tables, returning a mapping of (schema, table) -> classification.

    Args:
        tables: Sequence of table metadata to classify
        key_prefixes: List of prefixes to identify key columns (case-sensitive)

    Returns:
        Dictionary mapping (schema_name, table_name) tuples to their classification
    """
    return {(t.schema_name, t.table_name): classify_table(t.columns, key_prefixes) for t in tables}
