"""Schema discovery from Fabric warehouse INFORMATION_SCHEMA.

Reads INFORMATION_SCHEMA.TABLES and INFORMATION_SCHEMA.COLUMNS to
discover BASE TABLEs and their column metadata. Views are excluded
per REQ-29.
"""

from collections import defaultdict
from collections.abc import Sequence

import pyodbc

from semantic_model_generator.domain.types import ColumnMetadata, TableMetadata


def discover_tables(
    conn: pyodbc.Connection,
    schemas: Sequence[str],
) -> tuple[TableMetadata, ...]:
    """Discover BASE TABLEs and columns for specified schemas.

    Joins INFORMATION_SCHEMA.TABLES with COLUMNS, filtering to
    TABLE_TYPE = 'BASE TABLE' to exclude views (REQ-29).

    Args:
        conn: Authenticated pyodbc connection to Fabric warehouse
        schemas: Schema names to discover (e.g., ["dbo", "staging"])

    Returns:
        Tuple of TableMetadata, one per discovered table, with columns
        ordered by ORDINAL_POSITION.
    """
    if not schemas:
        return ()

    schema_placeholders = ", ".join("?" for _ in schemas)

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
    cursor.execute(query, list(schemas))
    rows = cursor.fetchall()

    # Group rows by (schema, table)
    table_columns: dict[tuple[str, str], list[ColumnMetadata]] = defaultdict(list)

    for row in rows:
        table_key = (row[0], row[1])
        col = ColumnMetadata(
            name=row[2],
            sql_type=row[3],
            is_nullable=row[4] == "YES",
            ordinal_position=row[5],
            max_length=row[6],
            numeric_precision=row[7],
            numeric_scale=row[8],
        )
        table_columns[table_key].append(col)

    return tuple(
        TableMetadata(
            schema_name=schema,
            table_name=table,
            columns=tuple(cols),
        )
        for (schema, table), cols in table_columns.items()
    )
