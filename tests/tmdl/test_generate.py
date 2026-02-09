"""Tests for TMDL generation functions."""

from semantic_model_generator.domain.types import (
    ColumnMetadata,
    TableClassification,
    TableMetadata,
)
from semantic_model_generator.tmdl.generate import (
    generate_column_tmdl,
    generate_database_tmdl,
    generate_expressions_tmdl,
    generate_model_tmdl,
    generate_partition_tmdl,
    generate_table_tmdl,
)
from semantic_model_generator.utils.identifiers import quote_tmdl_identifier
from semantic_model_generator.utils.whitespace import validate_tmdl_indentation


# Helper functions to create test fixtures (same pattern as test_relationships.py)
def make_column(
    name: str,
    sql_type: str = "varchar",
    ordinal: int = 1,
    is_nullable: bool = True,
) -> ColumnMetadata:
    """Create a minimal ColumnMetadata for testing."""
    return ColumnMetadata(
        name=name,
        sql_type=sql_type,
        is_nullable=is_nullable,
        ordinal_position=ordinal,
    )


def make_table(schema: str, table: str, columns: list[ColumnMetadata]) -> TableMetadata:
    """Create a TableMetadata for testing."""
    return TableMetadata(schema_name=schema, table_name=table, columns=tuple(columns))


# generate_database_tmdl tests
def test_generate_database_tmdl_contains_database_header() -> None:
    """Database TMDL contains 'database' as first line."""
    output = generate_database_tmdl()
    lines = output.split("\n")
    assert lines[0] == "database"


def test_generate_database_tmdl_contains_compatibility_level() -> None:
    """Database TMDL contains compatibilityLevel: 1604."""
    output = generate_database_tmdl()
    assert "\tcompatibilityLevel: 1604" in output


def test_generate_database_tmdl_passes_whitespace_validation() -> None:
    """Database TMDL passes whitespace validation (tabs only)."""
    output = generate_database_tmdl()
    errors = validate_tmdl_indentation(output)
    assert len(errors) == 0, f"Validation errors: {errors}"


# generate_model_tmdl tests
def test_generate_model_tmdl_starts_with_model_header() -> None:
    """Model TMDL starts with 'model Model'."""
    output = generate_model_tmdl("TestModel", [], {})
    lines = output.split("\n")
    assert lines[0] == "model Model"


def test_generate_model_tmdl_contains_culture_en_us() -> None:
    """Model TMDL contains culture: en-US."""
    output = generate_model_tmdl("TestModel", [], {})
    assert "\tculture: en-US" in output


def test_generate_model_tmdl_contains_default_powerbi_datasource_version() -> None:
    """Model TMDL contains defaultPowerBIDataSourceVersion: powerBI_V3."""
    output = generate_model_tmdl("TestModel", [], {})
    assert "\tdefaultPowerBIDataSourceVersion: powerBI_V3" in output


def test_generate_model_tmdl_contains_discourage_implicit_measures() -> None:
    """Model TMDL contains discourageImplicitMeasures."""
    output = generate_model_tmdl("TestModel", [], {})
    assert "\tdiscourageImplicitMeasures" in output


def test_generate_model_tmdl_contains_ref_table_lines() -> None:
    """Model TMDL contains ref table lines for each table."""
    table_names = ["dbo.DimCustomer", "dbo.FactSales"]
    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }
    output = generate_model_tmdl("TestModel", table_names, classifications)

    assert "\tref table DimCustomer" in output
    assert "\tref table FactSales" in output


def test_generate_model_tmdl_dimensions_before_facts() -> None:
    """Model TMDL lists dimension tables before fact tables."""
    table_names = ["dbo.FactSales", "dbo.DimCustomer", "dbo.DimProduct"]
    classifications = {
        ("dbo", "FactSales"): TableClassification.FACT,
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "DimProduct"): TableClassification.DIMENSION,
    }
    output = generate_model_tmdl("TestModel", table_names, classifications)

    # Find positions of ref table lines
    dim_customer_pos = output.find("ref table DimCustomer")
    dim_product_pos = output.find("ref table DimProduct")
    fact_sales_pos = output.find("ref table FactSales")

    # Dimensions should appear before facts
    assert dim_customer_pos < fact_sales_pos
    assert dim_product_pos < fact_sales_pos


def test_generate_model_tmdl_alphabetical_within_classification() -> None:
    """Model TMDL sorts tables alphabetically within same classification."""
    table_names = ["dbo.DimProduct", "dbo.DimCustomer"]
    classifications = {
        ("dbo", "DimProduct"): TableClassification.DIMENSION,
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
    }
    output = generate_model_tmdl("TestModel", table_names, classifications)

    dim_customer_pos = output.find("ref table DimCustomer")
    dim_product_pos = output.find("ref table DimProduct")

    # DimCustomer should appear before DimProduct (alphabetical)
    assert dim_customer_pos < dim_product_pos


def test_generate_model_tmdl_quotes_special_characters() -> None:
    """Model TMDL quotes table names with special characters."""
    table_names = ["dbo.Dim Customer"]  # Space in name
    classifications = {("dbo", "Dim Customer"): TableClassification.DIMENSION}
    output = generate_model_tmdl("TestModel", table_names, classifications)

    quoted_name = quote_tmdl_identifier("Dim Customer")
    assert f"ref table {quoted_name}" in output


def test_generate_model_tmdl_passes_whitespace_validation() -> None:
    """Model TMDL passes whitespace validation."""
    table_names = ["dbo.DimCustomer"]
    classifications = {("dbo", "DimCustomer"): TableClassification.DIMENSION}
    output = generate_model_tmdl("TestModel", table_names, classifications)

    errors = validate_tmdl_indentation(output)
    assert len(errors) == 0, f"Validation errors: {errors}"


# generate_expressions_tmdl tests
def test_generate_expressions_tmdl_contains_directlake_expression() -> None:
    """Expressions TMDL contains DirectLake expression with catalog name."""
    catalog_name = "my_warehouse"
    output = generate_expressions_tmdl(catalog_name)

    assert f"expression 'DirectLake - {catalog_name}'" in output


def test_generate_expressions_tmdl_contains_azure_storage_datalake() -> None:
    """Expressions TMDL contains AzureStorage.DataLake reference."""
    output = generate_expressions_tmdl("test_catalog")
    assert "AzureStorage.DataLake" in output


def test_generate_expressions_tmdl_contains_lineage_tag() -> None:
    """Expressions TMDL contains lineageTag UUID."""
    output = generate_expressions_tmdl("test_catalog")
    assert "lineageTag:" in output


def test_generate_expressions_tmdl_contains_pbi_annotation() -> None:
    """Expressions TMDL contains PBI_IncludeFutureArtifacts annotation."""
    output = generate_expressions_tmdl("test_catalog")
    assert "annotation PBI_IncludeFutureArtifacts = False" in output


def test_generate_expressions_tmdl_uses_en_us_locale() -> None:
    """Expressions TMDL uses en-US locale (Source, not Swedish Kalla)."""
    output = generate_expressions_tmdl("test_catalog")
    # Should use English "Source" variable name, not Swedish
    assert "Source = AzureStorage.DataLake" in output
    assert "Kalla" not in output  # Swedish word should not appear


def test_generate_expressions_tmdl_passes_whitespace_validation() -> None:
    """Expressions TMDL passes whitespace validation."""
    output = generate_expressions_tmdl("test_catalog")
    errors = validate_tmdl_indentation(output)
    assert len(errors) == 0, f"Validation errors: {errors}"


# generate_column_tmdl tests
def test_generate_column_tmdl_starts_with_column_header() -> None:
    """Column TMDL starts with 'column' and identifier."""
    column = make_column("CustomerName", sql_type="varchar")
    output = generate_column_tmdl(column, "dbo.DimCustomer")

    assert "\tcolumn CustomerName" in output


def test_generate_column_tmdl_contains_data_type() -> None:
    """Column TMDL contains dataType property."""
    column = make_column("Amount", sql_type="decimal")
    output = generate_column_tmdl(column, "dbo.FactSales")

    # Should map decimal -> TmdlDataType.DECIMAL
    assert "\t\tdataType: decimal" in output


def test_generate_column_tmdl_contains_lineage_tag() -> None:
    """Column TMDL contains deterministic lineageTag."""
    column = make_column("CustomerID", sql_type="bigint")
    output = generate_column_tmdl(column, "dbo.DimCustomer")

    assert "\t\tlineageTag:" in output


def test_generate_column_tmdl_contains_summarize_by_none() -> None:
    """Column TMDL contains summarizeBy: none."""
    column = make_column("Amount", sql_type="decimal")
    output = generate_column_tmdl(column, "dbo.FactSales")

    assert "\t\tsummarizeBy: none" in output


def test_generate_column_tmdl_contains_source_column() -> None:
    """Column TMDL contains sourceColumn with original name."""
    column = make_column("CustomerName", sql_type="varchar")
    output = generate_column_tmdl(column, "dbo.DimCustomer")

    assert "\t\tsourceColumn: CustomerName" in output


def test_generate_column_tmdl_quotes_names_with_spaces() -> None:
    """Column TMDL quotes column names containing spaces."""
    column = make_column("Customer Name", sql_type="varchar")
    output = generate_column_tmdl(column, "dbo.DimCustomer")

    quoted_name = quote_tmdl_identifier("Customer Name")
    assert f"\tcolumn {quoted_name}" in output


def test_generate_column_tmdl_no_quotes_for_simple_names() -> None:
    """Column TMDL doesn't quote simple column names."""
    column = make_column("CustomerID", sql_type="bigint")
    output = generate_column_tmdl(column, "dbo.DimCustomer")

    # Simple name should not be quoted
    assert "\tcolumn CustomerID" in output
    assert "'" not in output.split("\n")[0]  # First line has no quotes


def test_generate_column_tmdl_passes_whitespace_validation() -> None:
    """Column TMDL passes whitespace validation."""
    column = make_column("CustomerName", sql_type="varchar")
    output = generate_column_tmdl(column, "dbo.DimCustomer")

    errors = validate_tmdl_indentation(output)
    assert len(errors) == 0, f"Validation errors: {errors}"


# generate_partition_tmdl tests
def test_generate_partition_tmdl_contains_partition_header() -> None:
    """Partition TMDL contains partition header with name."""
    table = make_table("dbo", "DimCustomer", [make_column("ID")])
    output = generate_partition_tmdl(table, "DimCustomer", "my_warehouse")

    assert "\tpartition DimCustomer" in output or "\tpartition 'DimCustomer'" in output


def test_generate_partition_tmdl_contains_mode_directlake() -> None:
    """Partition TMDL contains mode: directLake."""
    table = make_table("dbo", "DimCustomer", [make_column("ID")])
    output = generate_partition_tmdl(table, "DimCustomer", "my_warehouse")

    assert "\t\tmode: directLake" in output


def test_generate_partition_tmdl_contains_entity_name() -> None:
    """Partition TMDL contains entityName with table name."""
    table = make_table("dbo", "DimCustomer", [make_column("ID")])
    output = generate_partition_tmdl(table, "DimCustomer", "my_warehouse")

    assert "\t\t\tentityName: DimCustomer" in output


def test_generate_partition_tmdl_contains_schema_name() -> None:
    """Partition TMDL contains schemaName with schema name."""
    table = make_table("sales", "Customer", [make_column("ID")])
    output = generate_partition_tmdl(table, "Customer", "my_warehouse")

    assert "\t\t\tschemaName: sales" in output


def test_generate_partition_tmdl_contains_expression_source() -> None:
    """Partition TMDL contains expressionSource reference."""
    table = make_table("dbo", "DimCustomer", [make_column("ID")])
    output = generate_partition_tmdl(table, "DimCustomer", "my_warehouse")

    assert "\t\t\texpressionSource: 'DirectLake - my_warehouse'" in output


def test_generate_partition_tmdl_passes_whitespace_validation() -> None:
    """Partition TMDL passes whitespace validation."""
    table = make_table("dbo", "DimCustomer", [make_column("ID")])
    output = generate_partition_tmdl(table, "DimCustomer", "my_warehouse")

    errors = validate_tmdl_indentation(output)
    assert len(errors) == 0, f"Validation errors: {errors}"


# generate_table_tmdl tests
def test_generate_table_tmdl_starts_with_table_header() -> None:
    """Table TMDL starts with 'table' and identifier."""
    table = make_table("dbo", "DimCustomer", [make_column("ID")])
    output = generate_table_tmdl(table, TableClassification.DIMENSION, ["ID_"], "my_warehouse")

    assert output.startswith("table ")


def test_generate_table_tmdl_contains_lineage_tag() -> None:
    """Table TMDL contains deterministic lineageTag."""
    table = make_table("dbo", "DimCustomer", [make_column("ID")])
    output = generate_table_tmdl(table, TableClassification.DIMENSION, ["ID_"], "my_warehouse")

    assert "\tlineageTag:" in output


def test_generate_table_tmdl_contains_all_columns() -> None:
    """Table TMDL contains all column sections."""
    columns = [
        make_column("ID_Customer", sql_type="bigint", ordinal=1),
        make_column("Name", sql_type="varchar", ordinal=2),
        make_column("City", sql_type="varchar", ordinal=3),
    ]
    table = make_table("dbo", "DimCustomer", columns)
    output = generate_table_tmdl(table, TableClassification.DIMENSION, ["ID_"], "my_warehouse")

    assert "column ID_Customer" in output
    assert "column Name" in output
    assert "column City" in output


def test_generate_table_tmdl_contains_partition_section() -> None:
    """Table TMDL contains partition section."""
    table = make_table("dbo", "DimCustomer", [make_column("ID")])
    output = generate_table_tmdl(table, TableClassification.DIMENSION, ["ID_"], "my_warehouse")

    assert "partition" in output
    assert "mode: directLake" in output


def test_generate_table_tmdl_key_columns_first() -> None:
    """Table TMDL lists key columns before non-key columns."""
    columns = [
        make_column("Name", sql_type="varchar", ordinal=1),
        make_column("ID_Customer", sql_type="bigint", ordinal=2),
        make_column("City", sql_type="varchar", ordinal=3),
    ]
    table = make_table("dbo", "DimCustomer", columns)
    output = generate_table_tmdl(table, TableClassification.DIMENSION, ["ID_"], "my_warehouse")

    # Find positions of column definitions
    id_customer_pos = output.find("column ID_Customer")
    name_pos = output.find("column Name")
    city_pos = output.find("column City")

    # ID_Customer (key) should appear before Name and City (non-keys)
    assert id_customer_pos < name_pos
    assert id_customer_pos < city_pos


def test_generate_table_tmdl_non_key_columns_alphabetical() -> None:
    """Table TMDL sorts non-key columns alphabetically."""
    columns = [
        make_column("ID_Customer", sql_type="bigint", ordinal=1),
        make_column("Name", sql_type="varchar", ordinal=2),
        make_column("City", sql_type="varchar", ordinal=3),
    ]
    table = make_table("dbo", "DimCustomer", columns)
    output = generate_table_tmdl(table, TableClassification.DIMENSION, ["ID_"], "my_warehouse")

    # Find positions
    city_pos = output.find("column City")
    name_pos = output.find("column Name")

    # City should appear before Name (alphabetical)
    assert city_pos < name_pos


def test_generate_table_tmdl_passes_whitespace_validation() -> None:
    """Table TMDL passes whitespace validation."""
    columns = [make_column("ID", sql_type="bigint")]
    table = make_table("dbo", "DimCustomer", columns)
    output = generate_table_tmdl(table, TableClassification.DIMENSION, ["ID_"], "my_warehouse")

    errors = validate_tmdl_indentation(output)
    assert len(errors) == 0, f"Validation errors: {errors}"


# Determinism tests
def test_generate_table_tmdl_is_deterministic() -> None:
    """Table TMDL generation produces identical output for same inputs."""
    columns = [
        make_column("ID_Customer", sql_type="bigint", ordinal=1),
        make_column("Name", sql_type="varchar", ordinal=2),
    ]
    table = make_table("dbo", "DimCustomer", columns)

    output1 = generate_table_tmdl(table, TableClassification.DIMENSION, ["ID_"], "my_warehouse")
    output2 = generate_table_tmdl(table, TableClassification.DIMENSION, ["ID_"], "my_warehouse")

    assert output1 == output2


def test_generate_model_tmdl_is_deterministic() -> None:
    """Model TMDL generation produces identical output for same inputs."""
    table_names = ["dbo.DimCustomer", "dbo.FactSales"]
    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    output1 = generate_model_tmdl("TestModel", table_names, classifications)
    output2 = generate_model_tmdl("TestModel", table_names, classifications)

    assert output1 == output2
