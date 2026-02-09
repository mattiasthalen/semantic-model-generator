"""Tests for relationship inference."""

import uuid

from semantic_model_generator.domain.types import (
    ColumnMetadata,
    Relationship,
    TableClassification,
    TableMetadata,
)
from semantic_model_generator.schema.relationships import (
    infer_relationships,
    is_exact_match,
    strip_prefix,
)


# Helper function to create column metadata (same pattern as test_classification.py)
def make_column(name: str, ordinal: int = 1) -> ColumnMetadata:
    """Create a minimal ColumnMetadata for testing."""
    return ColumnMetadata(
        name=name,
        sql_type="bigint",
        is_nullable=False,
        ordinal_position=ordinal,
    )


def make_table(schema: str, table: str, columns: list[ColumnMetadata]) -> TableMetadata:
    """Create a TableMetadata for testing."""
    return TableMetadata(schema_name=schema, table_name=table, columns=tuple(columns))


# Relationship dataclass tests
def test_relationship_is_frozen() -> None:
    """Relationship dataclass is frozen (immutable)."""
    rel = Relationship(
        id=uuid.uuid4(),
        from_table="dbo.FactSales",
        from_column="FK_CustomerID",
        to_table="dbo.DimCustomer",
        to_column="SK_CustomerID",
        is_active=True,
    )
    try:
        rel.is_active = False  # type: ignore[misc]
        msg = "Should not be able to modify frozen dataclass"
        raise AssertionError(msg)
    except AttributeError:
        pass  # Expected


def test_relationship_has_correct_defaults() -> None:
    """Relationship has correct default values for cardinalities and filtering."""
    rel = Relationship(
        id=uuid.uuid4(),
        from_table="dbo.FactSales",
        from_column="FK_CustomerID",
        to_table="dbo.DimCustomer",
        to_column="SK_CustomerID",
        is_active=True,
    )
    assert rel.cross_filtering_behavior == "oneDirection"
    assert rel.from_cardinality == "many"
    assert rel.to_cardinality == "one"


def test_relationship_fields_accessible() -> None:
    """Relationship fields are accessible."""
    test_id = uuid.uuid4()
    rel = Relationship(
        id=test_id,
        from_table="dbo.FactSales",
        from_column="FK_CustomerID",
        to_table="dbo.DimCustomer",
        to_column="SK_CustomerID",
        is_active=True,
    )
    assert rel.id == test_id
    assert rel.from_table == "dbo.FactSales"
    assert rel.from_column == "FK_CustomerID"
    assert rel.to_table == "dbo.DimCustomer"
    assert rel.to_column == "SK_CustomerID"
    assert rel.is_active is True


# strip_prefix tests
def test_strip_prefix_fk_prefix() -> None:
    """strip_prefix removes FK_ prefix."""
    result = strip_prefix("FK_CustomerID", ["SK_", "FK_"])
    assert result == "CustomerID"


def test_strip_prefix_sk_prefix() -> None:
    """strip_prefix removes SK_ prefix."""
    result = strip_prefix("SK_ProductID", ["SK_", "FK_"])
    assert result == "ProductID"


def test_strip_prefix_no_match_returns_none() -> None:
    """strip_prefix returns None when no prefix matches."""
    result = strip_prefix("Name", ["SK_", "FK_"])
    assert result is None


def test_strip_prefix_exact_match_returns_empty() -> None:
    """strip_prefix returns empty string for exact prefix match."""
    result = strip_prefix("FK_", ["FK_"])
    assert result == ""


def test_strip_prefix_first_matching_wins() -> None:
    """strip_prefix uses first matching prefix."""
    result = strip_prefix("SK_FK_Data", ["SK_", "FK_"])
    assert result == "FK_Data"


# is_exact_match tests
def test_is_exact_match_sk() -> None:
    """is_exact_match returns True for SK_ prefix."""
    result = is_exact_match("SK_", ["SK_", "FK_"])
    assert result is True


def test_is_exact_match_fk() -> None:
    """is_exact_match returns True for FK_ prefix."""
    result = is_exact_match("FK_", ["FK_"])
    assert result is True


def test_is_exact_match_column_with_suffix_returns_false() -> None:
    """is_exact_match returns False for column with suffix after prefix."""
    result = is_exact_match("SK_CustomerID", ["SK_", "FK_"])
    assert result is False


def test_is_exact_match_no_match_returns_false() -> None:
    """is_exact_match returns False when column name not in prefixes."""
    result = is_exact_match("Name", ["SK_", "FK_"])
    assert result is False


# REQ-06: Basic relationship inference tests
def test_single_relationship() -> None:
    """One fact with one key column to one dimension creates one active relationship."""
    dim = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    fact = make_table("dbo", "FactSales", [make_column("ID_Customer", 1)])

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    result = infer_relationships([dim, fact], classifications, ["ID_"])

    assert len(result) == 1
    rel = result[0]
    assert rel.from_table == "dbo.FactSales"
    assert rel.from_column == "ID_Customer"
    assert rel.to_table == "dbo.DimCustomer"
    assert rel.to_column == "ID_Customer"
    assert rel.is_active is True
    assert rel.from_cardinality == "many"
    assert rel.to_cardinality == "one"


def test_multiple_dimensions() -> None:
    """Fact with two key columns to two dimensions creates two active relationships."""
    dim_customer = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    dim_product = make_table("dbo", "DimProduct", [make_column("ID_Product", 1)])
    fact = make_table(
        "dbo",
        "FactSales",
        [make_column("ID_Customer", 1), make_column("ID_Product", 2)],
    )

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "DimProduct"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    result = infer_relationships([dim_customer, dim_product, fact], classifications, ["ID_"])

    assert len(result) == 2
    # Both should be active
    assert all(rel.is_active for rel in result)

    # Check one relationship to each dimension
    from_columns = {rel.from_column for rel in result}
    to_tables = {rel.to_table for rel in result}
    assert from_columns == {"ID_Customer", "ID_Product"}
    assert to_tables == {"dbo.DimCustomer", "dbo.DimProduct"}


def test_no_match_returns_empty() -> None:
    """Fact key that doesn't match any dimension returns empty tuple."""
    dim = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    fact = make_table("dbo", "FactSales", [make_column("ID_Order", 1)])

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    result = infer_relationships([dim, fact], classifications, ["ID_"])

    assert len(result) == 0


def test_unclassified_ignored() -> None:
    """Unclassified tables produce no relationships."""
    dim = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    unclass = make_table("dbo", "SomeTable", [make_column("ID_Customer", 1)])

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "SomeTable"): TableClassification.UNCLASSIFIED,
    }

    result = infer_relationships([dim, unclass], classifications, ["ID_"])

    assert len(result) == 0


def test_empty_input() -> None:
    """Empty tables list returns empty tuple."""
    result = infer_relationships([], {}, ["ID_"])
    assert result == ()


def test_fact_to_fact_no_relationship() -> None:
    """Two facts don't create relationships between each other."""
    fact1 = make_table("dbo", "FactSales", [make_column("ID_Customer", 1)])
    fact2 = make_table("dbo", "FactOrders", [make_column("ID_Customer", 1)])

    classifications = {
        ("dbo", "FactSales"): TableClassification.FACT,
        ("dbo", "FactOrders"): TableClassification.FACT,
    }

    result = infer_relationships([fact1, fact2], classifications, ["ID_"])

    assert len(result) == 0


def test_cross_schema_relationship() -> None:
    """Fact in one schema can match dimension in another schema."""
    dim = make_table("dim", "DimCustomer", [make_column("ID_Customer", 1)])
    fact = make_table("fact", "FactSales", [make_column("ID_Customer", 1)])

    classifications = {
        ("dim", "DimCustomer"): TableClassification.DIMENSION,
        ("fact", "FactSales"): TableClassification.FACT,
    }

    result = infer_relationships([dim, fact], classifications, ["ID_"])

    assert len(result) == 1
    rel = result[0]
    assert rel.from_table == "fact.FactSales"
    assert rel.to_table == "dim.DimCustomer"


# REQ-07: Role-playing dimension tests
def test_role_playing_detected() -> None:
    """Multiple fact columns matching same dimension via startswith matching."""
    dim = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    fact = make_table(
        "dbo",
        "FactSales",
        [
            make_column("ID_Customer", 1),
            make_column("ID_Customer_BillTo", 2),
        ],
    )

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    result = infer_relationships([dim, fact], classifications, ["ID_"])

    # Should have 2 relationships to same dimension
    assert len(result) == 2
    assert all(rel.to_table == "dbo.DimCustomer" for rel in result)
    assert all(rel.from_table == "dbo.FactSales" for rel in result)


# REQ-08: Active/inactive marking tests
def test_first_role_playing_active_rest_inactive() -> None:
    """When role-playing detected, first (by sorted column name) is active, rest inactive."""
    dim = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    fact = make_table(
        "dbo",
        "FactSales",
        [
            make_column("ID_Customer_BillTo", 1),
            make_column("ID_Customer", 2),  # Should be first when sorted
        ],
    )

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    result = infer_relationships([dim, fact], classifications, ["ID_"])

    assert len(result) == 2

    # Sort result by from_column to match deterministic output
    sorted_result = sorted(result, key=lambda r: r.from_column)

    # ID_Customer comes before ID_Customer_BillTo alphabetically
    assert sorted_result[0].from_column == "ID_Customer"
    assert sorted_result[0].is_active is True

    assert sorted_result[1].from_column == "ID_Customer_BillTo"
    assert sorted_result[1].is_active is False


def test_single_relationship_always_active() -> None:
    """Non-role-playing relationship is always active."""
    dim = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    fact = make_table("dbo", "FactSales", [make_column("ID_Customer", 1)])

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    result = infer_relationships([dim, fact], classifications, ["ID_"])

    assert len(result) == 1
    assert result[0].is_active is True


def test_deterministic_ordering() -> None:
    """Same inputs produce same active/inactive assignment."""
    dim = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    fact = make_table(
        "dbo",
        "FactSales",
        [
            make_column("ID_Customer_ShipTo", 1),
            make_column("ID_Customer_BillTo", 2),
            make_column("ID_Customer", 3),
        ],
    )

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    # Run twice
    result1 = infer_relationships([dim, fact], classifications, ["ID_"])
    result2 = infer_relationships([dim, fact], classifications, ["ID_"])

    # Results should be identical
    assert len(result1) == len(result2) == 3

    for r1, r2 in zip(result1, result2, strict=True):
        assert r1.from_column == r2.from_column
        assert r1.is_active == r2.is_active


# REQ-09: Exact-match bypass tests
def test_exact_match_produces_no_relationship() -> None:
    """Column named exactly as a prefix produces no relationship."""
    dim = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    fact = make_table("dbo", "FactSales", [make_column("ID_", 1), make_column("ID_Customer", 2)])

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    result = infer_relationships([dim, fact], classifications, ["ID_"])

    # Only ID_Customer should match, ID_ should be skipped
    assert len(result) == 1
    assert result[0].from_column == "ID_Customer"


def test_exact_match_excluded_from_role_playing_grouping() -> None:
    """Exact-match column doesn't count in role-playing grouping."""
    dim = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    fact = make_table(
        "dbo",
        "FactSales",
        [
            make_column("ID_", 1),  # Exact match - excluded
            make_column("ID_Customer", 2),
            make_column("ID_Customer_BillTo", 3),
        ],
    )

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    result = infer_relationships([dim, fact], classifications, ["ID_"])

    # Should have 2 relationships (ID_ excluded)
    assert len(result) == 2

    # First should be active, second inactive (role-playing pair)
    sorted_result = sorted(result, key=lambda r: r.from_column)
    assert sorted_result[0].from_column == "ID_Customer"
    assert sorted_result[0].is_active is True
    assert sorted_result[1].from_column == "ID_Customer_BillTo"
    assert sorted_result[1].is_active is False


# Deterministic output tests
def test_relationships_sorted_deterministically() -> None:
    """Output tuple is sorted by (from_table, from_column, to_table, to_column)."""
    dim1 = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    dim2 = make_table("dbo", "DimProduct", [make_column("ID_Product", 1)])
    fact = make_table(
        "dbo",
        "FactSales",
        [make_column("ID_Product", 1), make_column("ID_Customer", 2)],
    )

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "DimProduct"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    result = infer_relationships([dim1, dim2, fact], classifications, ["ID_"])

    assert len(result) == 2

    # Should be sorted by from_column (Customer < Product)
    assert result[0].from_column == "ID_Customer"
    assert result[1].from_column == "ID_Product"


def test_relationship_ids_are_deterministic() -> None:
    """Same inputs produce same UUID IDs via uuid_gen."""
    dim = make_table("dbo", "DimCustomer", [make_column("ID_Customer", 1)])
    fact = make_table("dbo", "FactSales", [make_column("ID_Customer", 1)])

    classifications = {
        ("dbo", "DimCustomer"): TableClassification.DIMENSION,
        ("dbo", "FactSales"): TableClassification.FACT,
    }

    # Run twice
    result1 = infer_relationships([dim, fact], classifications, ["ID_"])
    result2 = infer_relationships([dim, fact], classifications, ["ID_"])

    assert len(result1) == len(result2) == 1
    assert result1[0].id == result2[0].id
