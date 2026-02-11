"""Tests for TMDL generation functions."""

import json
import uuid

from semantic_model_generator.domain.types import (
    ColumnMetadata,
    Relationship,
    TableClassification,
    TableMetadata,
)
from semantic_model_generator.tmdl.generate import (
    generate_all_tmdl,
    generate_column_tmdl,
    generate_database_tmdl,
    generate_expressions_tmdl,
    generate_model_tmdl,
    generate_partition_tmdl,
    generate_relationships_tmdl,
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


def make_relationship(
    from_table: str,
    from_column: str,
    to_table: str,
    to_column: str,
    is_active: bool = True,
) -> Relationship:
    """Create a Relationship for testing."""
    rel_id = uuid.uuid4()
    return Relationship(
        id=rel_id,
        from_table=from_table,
        from_column=from_column,
        to_table=to_table,
        to_column=to_column,
        is_active=is_active,
    )


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

    assert "\nref table DimCustomer" in output
    assert "\nref table FactSales" in output


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


# generate_relationships_tmdl tests
def test_generate_relationships_tmdl_single_active_relationship() -> None:
    """Relationships TMDL with single active relationship contains correct syntax."""
    rel = make_relationship(
        "dbo.FactSales", "ID_Customer", "dbo.DimCustomer", "ID_Customer", is_active=True
    )
    output = generate_relationships_tmdl([rel])

    # Should contain relationship UUID
    assert f"relationship {rel.id}" in output
    # Should contain fromColumn with quoted table name and unquoted column
    assert "fromColumn: 'FactSales'.ID_Customer" in output
    # Should contain toColumn with quoted table name and unquoted column
    assert "toColumn: 'DimCustomer'.ID_Customer" in output
    # Active relationships should NOT have isActive line (default is true)
    assert "isActive" not in output


def test_generate_relationships_tmdl_inactive_relationship() -> None:
    """Relationships TMDL with inactive relationship contains isActive: false."""
    rel = make_relationship(
        "dbo.FactSales", "ID_Customer", "dbo.DimCustomer", "ID_Customer", is_active=False
    )
    output = generate_relationships_tmdl([rel])

    assert "isActive: false" in output


def test_generate_relationships_tmdl_multiple_relationships_sorted() -> None:
    """Relationships TMDL sorts relationships: active first, then by table/column names."""
    rel1 = make_relationship(
        "dbo.FactSales", "ID_Product", "dbo.DimProduct", "ID_Product", is_active=False
    )
    rel2 = make_relationship(
        "dbo.FactSales", "ID_Customer", "dbo.DimCustomer", "ID_Customer", is_active=True
    )
    rel3 = make_relationship(
        "dbo.FactSales", "ID_Store", "dbo.DimStore", "ID_Store", is_active=True
    )

    output = generate_relationships_tmdl([rel1, rel2, rel3])

    # Find positions
    pos_customer = output.find(f"relationship {rel2.id}")
    pos_store = output.find(f"relationship {rel3.id}")
    pos_product = output.find(f"relationship {rel1.id}")

    # Active relationships (rel2, rel3) should appear before inactive (rel1)
    assert pos_customer < pos_product
    assert pos_store < pos_product

    # Within active, sorted by (from_table, from_column, to_table, to_column)
    # ID_Customer comes before ID_Store alphabetically
    assert pos_customer < pos_store


def test_generate_relationships_tmdl_empty_list() -> None:
    """Relationships TMDL with empty list returns empty string."""
    output = generate_relationships_tmdl([])
    assert output == ""


def test_generate_relationships_tmdl_quotes_special_characters() -> None:
    """Relationships TMDL quotes table names with special characters."""
    rel = make_relationship("dbo.Fact Sales", "ID_Customer", "dbo.Dim Customer", "ID_Customer")
    output = generate_relationships_tmdl([rel])

    # Table names with spaces should be quoted
    assert "'Fact Sales'.ID_Customer" in output
    assert "'Dim Customer'.ID_Customer" in output


def test_generate_relationships_tmdl_passes_whitespace_validation() -> None:
    """Relationships TMDL passes whitespace validation."""
    rel = make_relationship("dbo.FactSales", "ID_Customer", "dbo.DimCustomer", "ID_Customer")
    output = generate_relationships_tmdl([rel])

    errors = validate_tmdl_indentation(output)
    assert len(errors) == 0, f"Validation errors: {errors}"


# generate_all_tmdl tests
def test_generate_all_tmdl_returns_all_required_file_paths() -> None:
    """generate_all_tmdl returns dict with all required file paths."""
    dim_table = make_table("dbo", "DimCustomer", [make_column("ID_Customer", ordinal=1)])
    fact_table = make_table("dbo", "FactSales", [make_column("ID_Customer", ordinal=1)])
    tables = [dim_table, fact_table]
    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }
    rel = make_relationship("dbo.FactSales", "ID_Customer", "dbo.DimCustomer", "ID_Customer")
    relationships = [rel]

    result = generate_all_tmdl(
        model_name="TestModel",
        tables=tables,
        classifications=classifications,
        relationships=relationships,
        key_prefixes=["ID_"],
        catalog_name="my_warehouse",
    )

    # Check all required file paths are present
    assert ".platform" in result
    assert "definition.pbism" in result
    assert "definition/database.tmdl" in result
    assert "definition/model.tmdl" in result
    assert "definition/expressions.tmdl" in result
    assert "definition/relationships.tmdl" in result
    assert "definition/tables/DimCustomer.tmdl" in result
    assert "definition/tables/FactSales.tmdl" in result
    assert "diagramLayout.json" in result


def test_generate_all_tmdl_all_tmdl_files_pass_validation() -> None:
    """generate_all_tmdl produces TMDL files that pass whitespace validation."""
    dim_table = make_table("dbo", "DimCustomer", [make_column("ID_Customer", ordinal=1)])
    tables = [dim_table]
    classifications = {("dbo", "DimCustomer"): TableClassification.DIMENSION}

    result = generate_all_tmdl(
        model_name="TestModel",
        tables=tables,
        classifications=classifications,
        relationships=[],
        key_prefixes=["ID_"],
        catalog_name="my_warehouse",
    )

    # Validate all TMDL files
    for path, content in result.items():
        if path.endswith(".tmdl"):
            errors = validate_tmdl_indentation(content)
            assert len(errors) == 0, f"{path} has indentation errors: {errors}"


def test_generate_all_tmdl_json_files_are_valid_json() -> None:
    """generate_all_tmdl produces valid JSON for .platform, definition.pbism, diagramLayout.json."""
    dim_table = make_table("dbo", "DimCustomer", [make_column("ID_Customer", ordinal=1)])
    tables = [dim_table]
    classifications = {("dbo", "DimCustomer"): TableClassification.DIMENSION}

    result = generate_all_tmdl(
        model_name="TestModel",
        tables=tables,
        classifications=classifications,
        relationships=[],
        key_prefixes=["ID_"],
        catalog_name="my_warehouse",
    )

    # Validate JSON files
    json_files = [".platform", "definition.pbism", "diagramLayout.json"]
    for json_file in json_files:
        content = result[json_file]
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            raise AssertionError(f"{json_file} is not valid JSON: {e}") from e


def test_generate_all_tmdl_is_deterministic() -> None:
    """generate_all_tmdl produces identical output for same inputs."""
    dim_table = make_table("dbo", "DimCustomer", [make_column("ID_Customer", ordinal=1)])
    fact_table = make_table("dbo", "FactSales", [make_column("ID_Customer", ordinal=1)])
    tables = [dim_table, fact_table]
    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }
    rel = make_relationship("dbo.FactSales", "ID_Customer", "dbo.DimCustomer", "ID_Customer")
    relationships = [rel]

    result1 = generate_all_tmdl(
        model_name="TestModel",
        tables=tables,
        classifications=classifications,
        relationships=relationships,
        key_prefixes=["ID_"],
        catalog_name="my_warehouse",
    )

    result2 = generate_all_tmdl(
        model_name="TestModel",
        tables=tables,
        classifications=classifications,
        relationships=relationships,
        key_prefixes=["ID_"],
        catalog_name="my_warehouse",
    )

    # Compare all keys and values
    assert result1.keys() == result2.keys()
    for key in result1.keys():
        assert result1[key] == result2[key], f"Mismatch in {key}"


def test_generate_all_tmdl_with_two_dimensions_and_one_fact() -> None:
    """generate_all_tmdl handles multiple dimensions and facts."""
    dim_customer = make_table("dbo", "DimCustomer", [make_column("ID_Customer", ordinal=1)])
    dim_product = make_table("dbo", "DimProduct", [make_column("ID_Product", ordinal=1)])
    fact_sales = make_table(
        "dbo",
        "FactSales",
        [
            make_column("ID_Customer", ordinal=1),
            make_column("ID_Product", ordinal=2),
        ],
    )
    tables = [dim_customer, dim_product, fact_sales]
    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "DimProduct"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }
    rel1 = make_relationship("dbo.FactSales", "ID_Customer", "dbo.DimCustomer", "ID_Customer")
    rel2 = make_relationship("dbo.FactSales", "ID_Product", "dbo.DimProduct", "ID_Product")
    relationships = [rel1, rel2]

    result = generate_all_tmdl(
        model_name="TestModel",
        tables=tables,
        classifications=classifications,
        relationships=relationships,
        key_prefixes=["ID_"],
        catalog_name="my_warehouse",
    )

    # Should have table files for all three tables
    assert "definition/tables/DimCustomer.tmdl" in result
    assert "definition/tables/DimProduct.tmdl" in result
    assert "definition/tables/FactSales.tmdl" in result

    # Should have two relationships in relationships.tmdl
    relationships_content = result["definition/relationships.tmdl"]
    assert f"relationship {rel1.id}" in relationships_content
    assert f"relationship {rel2.id}" in relationships_content
