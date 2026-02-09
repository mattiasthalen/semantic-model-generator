"""TMDL generation functions for database, model, expressions, and table components."""

from collections.abc import Sequence

from semantic_model_generator.domain.types import (
    ColumnMetadata,
    TableClassification,
    TableMetadata,
)


def generate_database_tmdl() -> str:
    """Generate database.tmdl file content.

    Returns:
        TMDL database definition with compatibilityLevel 1604.
    """
    raise NotImplementedError("generate_database_tmdl not yet implemented")


def generate_model_tmdl(
    model_name: str,
    table_names: Sequence[str],
    classifications: dict[tuple[str, str], TableClassification],
) -> str:
    """Generate model.tmdl file content.

    Args:
        model_name: Name of the semantic model.
        table_names: Sorted list of fully qualified table names (schema.table).
        classifications: Map of (schema_name, table_name) to TableClassification.

    Returns:
        TMDL model definition with culture, ref table lines, dimensions sorted before facts.
    """
    raise NotImplementedError("generate_model_tmdl not yet implemented")


def generate_expressions_tmdl(catalog_name: str) -> str:
    """Generate expressions.tmdl file content.

    Args:
        catalog_name: Fabric catalog name for DirectLake expression.

    Returns:
        TMDL expressions with DirectLake expression template and en-US locale.
    """
    raise NotImplementedError("generate_expressions_tmdl not yet implemented")


def generate_column_tmdl(column: ColumnMetadata, table_qualified_name: str) -> str:
    """Generate TMDL for a single column.

    Args:
        column: Column metadata from schema discovery.
        table_qualified_name: Fully qualified table name (schema.table).

    Returns:
        TMDL column definition with dataType, lineageTag, summarizeBy, sourceColumn.
    """
    raise NotImplementedError("generate_column_tmdl not yet implemented")


def generate_partition_tmdl(table: TableMetadata, partition_name: str, catalog_name: str) -> str:
    """Generate TMDL for a DirectLake partition.

    Args:
        table: Table metadata containing schema and table name.
        partition_name: Name for the partition.
        catalog_name: Fabric catalog name for expressionSource reference.

    Returns:
        TMDL partition definition with mode:directLake and source references.
    """
    raise NotImplementedError("generate_partition_tmdl not yet implemented")


def generate_table_tmdl(
    table: TableMetadata,
    classification: TableClassification,
    key_prefixes: Sequence[str],
    catalog_name: str,
) -> str:
    """Generate complete TMDL for a table.

    Args:
        table: Table metadata with columns.
        classification: Table classification (dimension/fact).
        key_prefixes: Prefixes identifying key columns (e.g., ["ID_"]).
        catalog_name: Fabric catalog name for partition reference.

    Returns:
        Complete TMDL table definition with columns and partition.
    """
    raise NotImplementedError("generate_table_tmdl not yet implemented")
