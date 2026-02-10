"""Tests for TMDL metadata file generators."""

import json

from semantic_model_generator.domain.types import (
    ColumnMetadata,
    TableClassification,
    TableMetadata,
)
from semantic_model_generator.tmdl.metadata import (
    generate_definition_pbism_json,
    generate_diagram_layout_json,
    generate_platform_json,
)


# Helper functions
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


# generate_platform_json tests
def test_generate_platform_json_is_valid_json() -> None:
    """Platform JSON output is valid JSON."""
    output = generate_platform_json("TestModel")

    try:
        json.loads(output)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Output is not valid JSON: {e}") from e


def test_generate_platform_json_contains_schema() -> None:
    """Platform JSON contains $schema with fabric gitIntegration URL."""
    output = generate_platform_json("TestModel")
    data = json.loads(output)

    assert "$schema" in data
    assert "fabric/gitIntegration/platformProperties" in data["$schema"]


def test_generate_platform_json_contains_semantic_model_type() -> None:
    """Platform JSON metadata.type is SemanticModel."""
    output = generate_platform_json("TestModel")
    data = json.loads(output)

    assert "metadata" in data
    assert data["metadata"]["type"] == "SemanticModel"


def test_generate_platform_json_contains_display_name() -> None:
    """Platform JSON metadata.displayName matches model_name argument."""
    output = generate_platform_json("TestModel")
    data = json.loads(output)

    assert "metadata" in data
    assert data["metadata"]["displayName"] == "TestModel"


def test_generate_platform_json_contains_version() -> None:
    """Platform JSON config.version is 2.0."""
    output = generate_platform_json("TestModel")
    data = json.loads(output)

    assert "config" in data
    assert data["config"]["version"] == "2.0"


def test_generate_platform_json_contains_logical_id() -> None:
    """Platform JSON config.logicalId is a valid UUID string."""
    output = generate_platform_json("TestModel")
    data = json.loads(output)

    assert "config" in data
    assert "logicalId" in data["config"]

    # Check it's a valid UUID format
    logical_id = data["config"]["logicalId"]
    assert isinstance(logical_id, str)
    assert len(logical_id) == 36  # UUID format: 8-4-4-4-12 with dashes
    assert logical_id.count("-") == 4


def test_generate_platform_json_logical_id_is_deterministic() -> None:
    """Platform JSON logicalId is deterministic (same model_name produces same UUID)."""
    output1 = generate_platform_json("TestModel")
    output2 = generate_platform_json("TestModel")

    data1 = json.loads(output1)
    data2 = json.loads(output2)

    assert data1["config"]["logicalId"] == data2["config"]["logicalId"]


def test_generate_platform_json_is_deterministic() -> None:
    """Platform JSON output is deterministic (sort_keys ensures stable key order)."""
    output1 = generate_platform_json("TestModel")
    output2 = generate_platform_json("TestModel")

    assert output1 == output2


# generate_definition_pbism_json tests
def test_generate_definition_pbism_json_is_valid_json() -> None:
    """definition.pbism output is valid JSON."""
    output = generate_definition_pbism_json("TestModel")

    try:
        json.loads(output)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Output is not valid JSON: {e}") from e


def test_generate_definition_pbism_json_contains_schema() -> None:
    """definition.pbism contains $schema with fabric semanticModel URL."""
    output = generate_definition_pbism_json("TestModel")
    data = json.loads(output)

    assert "$schema" in data
    assert "fabric/item/semanticModel/definitionProperties" in data["$schema"]


def test_generate_definition_pbism_json_contains_version() -> None:
    """definition.pbism contains version field."""
    output = generate_definition_pbism_json("TestModel")
    data = json.loads(output)

    assert "version" in data
    # Version should be a string like "4.2"
    assert isinstance(data["version"], str)


def test_generate_definition_pbism_json_contains_name() -> None:
    """definition.pbism contains name field matching model_name argument."""
    output = generate_definition_pbism_json("TestModel")
    data = json.loads(output)

    assert "name" in data
    assert data["name"] == "TestModel"


def test_generate_definition_pbism_json_contains_description() -> None:
    """definition.pbism contains description field."""
    output = generate_definition_pbism_json("TestModel", description="Test description")
    data = json.loads(output)

    assert "description" in data
    assert data["description"] == "Test description"


def test_generate_definition_pbism_json_contains_author_when_provided() -> None:
    """definition.pbism contains author field when author argument is provided."""
    output = generate_definition_pbism_json("TestModel", author="Test Author")
    data = json.loads(output)

    assert "author" in data
    assert data["author"] == "Test Author"


def test_generate_definition_pbism_json_contains_created_at_timestamp() -> None:
    """definition.pbism contains createdAt timestamp field."""
    output = generate_definition_pbism_json("TestModel")
    data = json.loads(output)

    assert "createdAt" in data
    # Check it's a valid ISO 8601 timestamp string
    assert isinstance(data["createdAt"], str)
    assert "T" in data["createdAt"]  # ISO format has T separator


def test_generate_definition_pbism_json_contains_modified_at_timestamp() -> None:
    """definition.pbism contains modifiedAt timestamp field."""
    output = generate_definition_pbism_json("TestModel")
    data = json.loads(output)

    assert "modifiedAt" in data
    # Check it's a valid ISO 8601 timestamp string
    assert isinstance(data["modifiedAt"], str)
    assert "T" in data["modifiedAt"]


def test_generate_definition_pbism_json_empty_author_handling() -> None:
    """definition.pbism handles empty author string (includes key with empty value)."""
    output = generate_definition_pbism_json("TestModel", author="")
    data = json.loads(output)

    # With empty author, the key should still be present (for determinism)
    assert "author" in data


def test_generate_definition_pbism_json_is_deterministic_with_fixed_timestamp() -> None:
    """definition.pbism is deterministic when timestamp is provided."""
    fixed_timestamp = "2024-01-15T10:30:00Z"

    output1 = generate_definition_pbism_json("TestModel", timestamp=fixed_timestamp)
    output2 = generate_definition_pbism_json("TestModel", timestamp=fixed_timestamp)

    assert output1 == output2


# generate_diagram_layout_json tests
def test_generate_diagram_layout_json_is_valid_json() -> None:
    """diagramLayout output is valid JSON."""
    dim_table = make_table("dbo", "DimCustomer", [make_column("ID_Customer")])
    tables = [dim_table]
    classifications = {("dbo", "DimCustomer"): TableClassification.DIMENSION}

    output = generate_diagram_layout_json(tables, classifications)

    try:
        json.loads(output)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Output is not valid JSON: {e}") from e


def test_generate_diagram_layout_json_contains_tables_array() -> None:
    """diagramLayout contains tables array."""
    dim_table = make_table("dbo", "DimCustomer", [make_column("ID_Customer")])
    tables = [dim_table]
    classifications = {("dbo", "DimCustomer"): TableClassification.DIMENSION}

    output = generate_diagram_layout_json(tables, classifications)
    data = json.loads(output)

    assert "tables" in data
    assert isinstance(data["tables"], list)


def test_generate_diagram_layout_json_facts_positioned_in_left_column() -> None:
    """diagramLayout positions fact tables in a vertical column (same x coordinate)."""
    fact1 = make_table("dbo", "FactSales", [make_column("ID")])
    fact2 = make_table("dbo", "FactOrders", [make_column("ID")])
    tables = [fact1, fact2]
    classifications = {
        ("dbo", "FactSales"): TableClassification.FACT,
        ("dbo", "FactOrders"): TableClassification.FACT,
    }

    output = generate_diagram_layout_json(tables, classifications)
    data = json.loads(output)

    fact_tables = [t for t in data["tables"] if "Fact" in t["name"]]
    assert len(fact_tables) == 2

    # All fact tables should have the same x coordinate (vertical column)
    x_coords = [t["x"] for t in fact_tables]
    assert len(set(x_coords)) == 1, "All facts should have same x coordinate"


def test_generate_diagram_layout_json_dimensions_positioned_differently() -> None:
    """diagramLayout positions dimension tables with different x from facts column."""
    dim1 = make_table("dbo", "DimCustomer", [make_column("ID")])
    fact1 = make_table("dbo", "FactSales", [make_column("ID")])
    tables = [dim1, fact1]
    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    output = generate_diagram_layout_json(tables, classifications)
    data = json.loads(output)

    dim_tables = [t for t in data["tables"] if "Dim" in t["name"]]
    fact_tables = [t for t in data["tables"] if "Fact" in t["name"]]

    assert len(dim_tables) > 0
    assert len(fact_tables) > 0

    # Dimensions should have different x coordinate from facts
    dim_x = dim_tables[0]["x"]
    fact_x = fact_tables[0]["x"]
    assert dim_x != fact_x, "Dimensions and facts should be in different columns"


def test_generate_diagram_layout_json_each_table_has_required_fields() -> None:
    """diagramLayout table entries have name, x, y, width, height fields."""
    dim_table = make_table("dbo", "DimCustomer", [make_column("ID_Customer")])
    tables = [dim_table]
    classifications = {("dbo", "DimCustomer"): TableClassification.DIMENSION}

    output = generate_diagram_layout_json(tables, classifications)
    data = json.loads(output)

    for table_entry in data["tables"]:
        assert "name" in table_entry
        assert "x" in table_entry
        assert "y" in table_entry
        assert "width" in table_entry
        assert "height" in table_entry


def test_generate_diagram_layout_json_table_count_matches_input() -> None:
    """diagramLayout table count matches input table count (excluding unclassified)."""
    dim1 = make_table("dbo", "DimCustomer", [make_column("ID")])
    dim2 = make_table("dbo", "DimProduct", [make_column("ID")])
    fact1 = make_table("dbo", "FactSales", [make_column("ID")])
    tables = [dim1, dim2, fact1]
    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "DimProduct"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    output = generate_diagram_layout_json(tables, classifications)
    data = json.loads(output)

    # Should have 3 tables in layout
    assert len(data["tables"]) == 3


def test_generate_diagram_layout_json_is_deterministic() -> None:
    """diagramLayout is deterministic (same input produces same output)."""
    dim_table = make_table("dbo", "DimCustomer", [make_column("ID_Customer")])
    fact_table = make_table("dbo", "FactSales", [make_column("ID_Customer")])
    tables = [dim_table, fact_table]
    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    output1 = generate_diagram_layout_json(tables, classifications)
    output2 = generate_diagram_layout_json(tables, classifications)

    assert output1 == output2
