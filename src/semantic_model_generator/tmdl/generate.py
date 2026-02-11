"""TMDL generation functions for database, model, expressions, and table components."""

from collections.abc import Sequence

from semantic_model_generator.domain.types import (
    ColumnMetadata,
    Relationship,
    TableClassification,
    TableMetadata,
)
from semantic_model_generator.utils.identifiers import quote_tmdl_identifier
from semantic_model_generator.utils.type_mapping import map_sql_type_to_tmdl
from semantic_model_generator.utils.uuid_gen import generate_deterministic_uuid
from semantic_model_generator.utils.whitespace import indent_tmdl, validate_tmdl_indentation


def generate_database_tmdl() -> str:
    """Generate database.tmdl file content.

    Returns:
        TMDL database definition with compatibilityLevel 1604.
    """
    content = f"database\n{indent_tmdl(1)}compatibilityLevel: 1604\n"

    # Validate before returning
    errors = validate_tmdl_indentation(content)
    if errors:
        error_msgs = [f"Line {e.line_number}: {e.message}" for e in errors]
        error_text = "\n".join(error_msgs)
        raise ValueError(f"Generated database.tmdl has indentation errors:\n{error_text}")

    return content


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
    indent1 = indent_tmdl(1)

    # Parse and sort tables: dimensions first, then facts, then unclassified
    # Within each group, sort by (schema_name, table_name)
    def parse_qualified_name(qualified_name: str) -> tuple[str, str]:
        """Parse 'schema.table' into (schema, table)."""
        parts = qualified_name.split(".", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return "", parts[0]

    def sort_key(qualified_name: str) -> tuple[int, str, str]:
        """Generate sort key for table: (classification_order, schema, table)."""
        schema, table = parse_qualified_name(qualified_name)
        classification = classifications.get((schema, table), TableClassification.UNCLASSIFIED)

        # Primary sort: dimension=0, fact=1, unclassified=2
        classification_order = {
            TableClassification.DIMENSION: 0,
            TableClassification.FACT: 1,
            TableClassification.UNCLASSIFIED: 2,
        }

        return (classification_order[classification], schema, table)

    sorted_tables = sorted(table_names, key=sort_key)

    # Build model content
    lines = ["model Model"]
    lines.append(f"{indent1}culture: en-US")
    lines.append(f"{indent1}defaultPowerBIDataSourceVersion: powerBI_V3")
    lines.append(f"{indent1}discourageImplicitMeasures")

    # Add ref table lines at root level (no indent) separated by blank line
    lines.append("")
    for qualified_name in sorted_tables:
        _, table_name = parse_qualified_name(qualified_name)
        quoted_table = quote_tmdl_identifier(table_name)
        lines.append(f"ref table {quoted_table}")

    content = "\n".join(lines) + "\n"

    # Validate before returning
    errors = validate_tmdl_indentation(content)
    if errors:
        error_msgs = [f"Line {e.line_number}: {e.message}" for e in errors]
        error_text = "\n".join(error_msgs)
        raise ValueError(f"Generated model.tmdl has indentation errors:\n{error_text}")

    return content


def generate_expressions_tmdl(catalog_name: str) -> str:
    """Generate expressions.tmdl file content.

    Args:
        catalog_name: Fabric catalog name for DirectLake expression.

    Returns:
        TMDL expressions with DirectLake expression template and en-US locale.
    """
    indent1 = indent_tmdl(1)
    indent2 = indent_tmdl(2)
    indent3 = indent_tmdl(3)

    # Generate deterministic UUID for expression
    lineage_tag = generate_deterministic_uuid("expression", catalog_name)

    # Use en-US locale with English "Source" variable name (not Swedish "Kalla")
    content = f"""expression 'DirectLake - {catalog_name}' =
{indent2}let
{indent3}Source = AzureStorage.DataLake("", [HierarchicalNavigation=true])
{indent2}in
{indent3}Source
{indent1}lineageTag: {lineage_tag}

{indent1}annotation PBI_IncludeFutureArtifacts = False
"""

    # Validate before returning
    errors = validate_tmdl_indentation(content)
    if errors:
        error_msgs = [f"Line {e.line_number}: {e.message}" for e in errors]
        error_text = "\n".join(error_msgs)
        raise ValueError(f"Generated expressions.tmdl has indentation errors:\n{error_text}")

    return content


def generate_column_tmdl(column: ColumnMetadata, table_qualified_name: str) -> str:
    """Generate TMDL for a single column.

    Args:
        column: Column metadata from schema discovery.
        table_qualified_name: Fully qualified table name (schema.table).

    Returns:
        TMDL column definition with dataType, lineageTag, summarizeBy, sourceColumn.
    """
    indent1 = indent_tmdl(1)
    indent2 = indent_tmdl(2)

    # Quote column name if needed
    quoted_name = quote_tmdl_identifier(column.name)

    # Map SQL type to TMDL type
    tmdl_type = map_sql_type_to_tmdl(column.sql_type)

    # Generate deterministic UUID for column
    lineage_tag = generate_deterministic_uuid("column", f"{table_qualified_name}.{column.name}")

    # Build column definition
    lines = [f"{indent1}column {quoted_name}"]
    lines.append(f"{indent2}dataType: {tmdl_type.value}")
    lines.append(f"{indent2}lineageTag: {lineage_tag}")
    lines.append(f"{indent2}summarizeBy: none")
    lines.append(f"{indent2}sourceColumn: {column.name}")
    lines.append("")
    lines.append(f"{indent2}annotation SummarizationSetBy = Automatic")

    content = "\n".join(lines) + "\n"

    # Validate before returning
    errors = validate_tmdl_indentation(content)
    if errors:
        error_msgs = [f"Line {e.line_number}: {e.message}" for e in errors]
        error_text = "\n".join(error_msgs)
        raise ValueError(f"Generated column TMDL has indentation errors:\n{error_text}")

    return content


def generate_partition_tmdl(table: TableMetadata, partition_name: str, catalog_name: str) -> str:
    """Generate TMDL for a DirectLake partition.

    Args:
        table: Table metadata containing schema and table name.
        partition_name: Name for the partition.
        catalog_name: Fabric catalog name for expressionSource reference.

    Returns:
        TMDL partition definition with mode:directLake and source references.
    """
    indent1 = indent_tmdl(1)
    indent2 = indent_tmdl(2)
    indent3 = indent_tmdl(3)

    # Quote partition name if needed
    quoted_partition = quote_tmdl_identifier(partition_name)

    # Build partition definition
    content = f"""{indent1}partition {quoted_partition} = entity
{indent2}mode: directLake
{indent2}source
{indent3}entityName: {table.table_name}
{indent3}schemaName: {table.schema_name}
{indent3}expressionSource: 'DirectLake - {catalog_name}'
"""

    # Validate before returning
    errors = validate_tmdl_indentation(content)
    if errors:
        error_msgs = [f"Line {e.line_number}: {e.message}" for e in errors]
        error_text = "\n".join(error_msgs)
        raise ValueError(f"Generated partition TMDL has indentation errors:\n{error_text}")

    return content


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
    indent1 = indent_tmdl(1)

    # Quote table name if needed
    quoted_table = quote_tmdl_identifier(table.table_name)

    # Generate deterministic UUID for table
    lineage_tag = generate_deterministic_uuid("table", f"{table.schema_name}.{table.table_name}")

    # Sort columns: key columns first, then alphabetically by name
    key_columns = [
        col for col in table.columns if any(col.name.startswith(prefix) for prefix in key_prefixes)
    ]
    non_key_columns = [col for col in table.columns if col not in key_columns]

    # Sort each group alphabetically
    sorted_key_columns = sorted(key_columns, key=lambda c: c.name)
    sorted_non_key_columns = sorted(non_key_columns, key=lambda c: c.name)

    all_columns = sorted_key_columns + sorted_non_key_columns

    # Generate column sections
    table_qualified_name = f"{table.schema_name}.{table.table_name}"
    column_sections = [generate_column_tmdl(col, table_qualified_name) for col in all_columns]

    # Generate partition section
    partition_section = generate_partition_tmdl(table, table.table_name, catalog_name)

    # Compose table TMDL
    content = f"""table {quoted_table}
{indent1}lineageTag: {lineage_tag}

{partition_section}
{"".join(column_sections)}"""

    # Validate before returning
    errors = validate_tmdl_indentation(content)
    if errors:
        error_msgs = [f"Line {e.line_number}: {e.message}" for e in errors]
        error_text = "\n".join(error_msgs)
        raise ValueError(f"Generated table TMDL has indentation errors:\n{error_text}")

    return content


def generate_relationships_tmdl(relationships: Sequence[Relationship]) -> str:
    """Generate relationships.tmdl file content.

    Args:
        relationships: Sequence of inferred relationships.

    Returns:
        TMDL relationships definitions with active/inactive, fromColumn, toColumn.
    """
    if not relationships:
        return ""

    indent1 = indent_tmdl(1)

    # Sort relationships: active first (is_active=True), then by table/column names
    def sort_key(rel: Relationship) -> tuple[bool, str, str, str, str]:
        # Primary sort: active (False) before inactive (True) - inverted bool for sorting
        # Secondary sort: (from_table, from_column, to_table, to_column)
        return (not rel.is_active, rel.from_table, rel.from_column, rel.to_table, rel.to_column)

    sorted_relationships = sorted(relationships, key=sort_key)

    # Build relationship sections
    sections = []
    for rel in sorted_relationships:
        # Extract table name from schema-qualified "schema.table"
        from_table_name = rel.from_table.split(".", 1)[-1]
        to_table_name = rel.to_table.split(".", 1)[-1]

        # Per TMDL relationship syntax: table names are ALWAYS single-quoted
        # Format: 'TableName'.ColumnName (table always quoted, column not quoted)
        # Escape internal single quotes by doubling them if present
        from_table_escaped = from_table_name.replace("'", "''")
        to_table_escaped = to_table_name.replace("'", "''")

        lines = [f"relationship {rel.id}"]

        # Add isActive: false only for inactive relationships
        if not rel.is_active:
            lines.append(f"{indent1}isActive: false")

        # Add fromColumn and toColumn with always-quoted table names
        lines.append(f"{indent1}fromColumn: '{from_table_escaped}'.{rel.from_column}")
        lines.append(f"{indent1}toColumn: '{to_table_escaped}'.{rel.to_column}")

        sections.append("\n".join(lines))

    # Join all sections with blank line separator
    content = "\n\n".join(sections) + "\n"

    # Validate before returning
    errors = validate_tmdl_indentation(content)
    if errors:
        error_msgs = [f"Line {e.line_number}: {e.message}" for e in errors]
        error_text = "\n".join(error_msgs)
        raise ValueError(f"Generated relationships.tmdl has indentation errors:\n{error_text}")

    return content


def generate_all_tmdl(
    model_name: str,
    tables: Sequence[TableMetadata],
    classifications: dict[tuple[str, str], TableClassification],
    relationships: Sequence[Relationship],
    key_prefixes: Sequence[str],
    catalog_name: str,
) -> dict[str, str]:
    """Generate complete TMDL semantic model as a dict of file paths to content.

    Args:
        model_name: Name of the semantic model.
        tables: All tables in the model.
        classifications: Map of (schema, table) to TableClassification.
        relationships: All inferred relationships.
        key_prefixes: Prefixes identifying key columns.
        catalog_name: Fabric catalog name for DirectLake expression.

    Returns:
        Dict mapping relative file paths to their content strings.
        Example keys: ".platform", "definition.pbism", "definition/database.tmdl",
        "definition/model.tmdl", "definition/expressions.tmdl",
        "definition/relationships.tmdl", "definition/tables/Customer.tmdl",
        "diagramLayout.json"
    """
    # Import metadata generators
    from semantic_model_generator.tmdl.metadata import (
        generate_definition_pbism_json,
        generate_diagram_layout_json,
        generate_platform_json,
    )

    # Sort tables: dimensions first, then facts, within each by (schema, table)
    def sort_key(table: TableMetadata) -> tuple[int, str, str]:
        classification = classifications.get(
            (table.schema_name, table.table_name), TableClassification.UNCLASSIFIED
        )
        classification_order = {
            TableClassification.DIMENSION: 0,
            TableClassification.FACT: 1,
            TableClassification.UNCLASSIFIED: 2,
        }
        return (classification_order[classification], table.schema_name, table.table_name)

    sorted_tables = sorted(tables, key=sort_key)

    # Build qualified table names for model.tmdl
    table_qualified_names = [f"{t.schema_name}.{t.table_name}" for t in sorted_tables]

    # Build the output dict
    output: dict[str, str] = {}

    # Metadata files
    output[".platform"] = generate_platform_json(model_name)
    output["definition.pbism"] = generate_definition_pbism_json()

    # TMDL definition files
    output["definition/database.tmdl"] = generate_database_tmdl()
    output["definition/model.tmdl"] = generate_model_tmdl(
        model_name, table_qualified_names, classifications
    )
    output["definition/expressions.tmdl"] = generate_expressions_tmdl(catalog_name)
    output["definition/relationships.tmdl"] = generate_relationships_tmdl(relationships)

    # Table files
    for table in sorted_tables:
        classification = classifications.get(
            (table.schema_name, table.table_name), TableClassification.UNCLASSIFIED
        )
        table_path = f"definition/tables/{table.table_name}.tmdl"
        output[table_path] = generate_table_tmdl(table, classification, key_prefixes, catalog_name)

    # Diagram layout
    output["diagramLayout.json"] = generate_diagram_layout_json(tables, classifications)

    return output
