"""Tests for table classification by key column count."""

from semantic_model_generator.schema.classification import classify_table, classify_tables

from semantic_model_generator.domain.types import (
    ColumnMetadata,
    TableClassification,
    TableMetadata,
)


# Helper function to create column metadata
def make_column(name: str, ordinal: int = 1) -> ColumnMetadata:
    """Create a minimal ColumnMetadata for testing."""
    return ColumnMetadata(
        name=name,
        sql_type="bigint",
        is_nullable=False,
        ordinal_position=ordinal,
    )


# TableClassification enum tests
def test_table_classification_has_three_members() -> None:
    """TableClassification enum has exactly 3 members."""
    assert len(TableClassification) == 3


def test_table_classification_values() -> None:
    """TableClassification members have correct string values."""
    assert TableClassification.DIMENSION == "dimension"
    assert TableClassification.FACT == "fact"
    assert TableClassification.UNCLASSIFIED == "unclassified"


def test_table_classification_is_strenum() -> None:
    """TableClassification is a StrEnum subclass."""
    from enum import StrEnum

    assert issubclass(TableClassification, StrEnum)


# classify_table tests - single table classification
def test_classify_table_one_key_is_dimension() -> None:
    """Table with 1 key column is classified as DIMENSION."""
    columns = [
        make_column("SK_CustomerID", 1),
        make_column("Name", 2),
        make_column("Email", 3),
    ]
    result = classify_table(columns, key_prefixes=["SK_", "FK_"])
    assert result == TableClassification.DIMENSION


def test_classify_table_two_keys_is_fact() -> None:
    """Table with 2 key columns is classified as FACT."""
    columns = [
        make_column("SK_SalesID", 1),
        make_column("FK_CustomerID", 2),
        make_column("FK_ProductID", 3),
        make_column("Amount", 4),
    ]
    result = classify_table(columns, key_prefixes=["SK_", "FK_"])
    assert result == TableClassification.FACT


def test_classify_table_three_keys_is_fact() -> None:
    """Table with 3+ key columns is classified as FACT."""
    columns = [
        make_column("SK_SalesID", 1),
        make_column("FK_CustomerID", 2),
        make_column("FK_ProductID", 3),
        make_column("FK_DateID", 4),
    ]
    result = classify_table(columns, key_prefixes=["SK_", "FK_"])
    assert result == TableClassification.FACT


def test_classify_table_zero_keys_is_unclassified() -> None:
    """Table with 0 key columns is classified as UNCLASSIFIED."""
    columns = [
        make_column("Name", 1),
        make_column("Value", 2),
        make_column("Description", 3),
    ]
    result = classify_table(columns, key_prefixes=["SK_", "FK_"])
    assert result == TableClassification.UNCLASSIFIED


def test_classify_table_exactly_two_keys_is_fact() -> None:
    """Table with exactly 2 key columns is classified as FACT."""
    columns = [
        make_column("FK_CustomerID", 1),
        make_column("FK_ProductID", 2),
    ]
    result = classify_table(columns, key_prefixes=["FK_"])
    assert result == TableClassification.FACT


def test_classify_table_case_sensitive_prefix_matching() -> None:
    """Key prefix matching is case-sensitive."""
    columns = [
        make_column("sk_CustomerID", 1),  # lowercase 'sk'
        make_column("Name", 2),
    ]
    result = classify_table(columns, key_prefixes=["SK_"])  # uppercase 'SK_'
    assert result == TableClassification.UNCLASSIFIED  # Should not match


def test_classify_table_multiple_prefixes() -> None:
    """Multiple prefixes can be used, any match counts as a key."""
    columns = [
        make_column("PK_ID", 1),
        make_column("FK_CustID", 2),
    ]
    result = classify_table(columns, key_prefixes=["PK_", "FK_"])
    assert result == TableClassification.FACT  # 2 keys


def test_classify_table_single_prefix_one_key() -> None:
    """Single prefix with one matching column is DIMENSION."""
    columns = [
        make_column("FK_CustID", 1),
        make_column("Name", 2),
    ]
    result = classify_table(columns, key_prefixes=["FK_"])
    assert result == TableClassification.DIMENSION


def test_classify_table_empty_key_prefixes() -> None:
    """Empty key_prefixes list results in UNCLASSIFIED."""
    columns = [
        make_column("SK_CustomerID", 1),
        make_column("Name", 2),
    ]
    result = classify_table(columns, key_prefixes=[])
    assert result == TableClassification.UNCLASSIFIED


def test_classify_table_empty_columns() -> None:
    """Empty columns tuple is UNCLASSIFIED."""
    result = classify_table([], key_prefixes=["SK_", "FK_"])
    assert result == TableClassification.UNCLASSIFIED


# classify_tables tests - batch classification
def test_classify_tables_mixed_classifications() -> None:
    """Classify a mix of dimension, fact, and unclassified tables."""
    tables = [
        TableMetadata(
            schema_name="dbo",
            table_name="DimCustomer",
            columns=(
                make_column("SK_CustomerID", 1),
                make_column("Name", 2),
            ),
        ),
        TableMetadata(
            schema_name="dbo",
            table_name="FactSales",
            columns=(
                make_column("SK_SalesID", 1),
                make_column("FK_CustomerID", 2),
                make_column("FK_ProductID", 3),
            ),
        ),
        TableMetadata(
            schema_name="staging",
            table_name="TempData",
            columns=(
                make_column("Name", 1),
                make_column("Value", 2),
            ),
        ),
    ]
    result = classify_tables(tables, key_prefixes=["SK_", "FK_"])

    assert len(result) == 3
    assert result[("dbo", "DimCustomer")] == TableClassification.DIMENSION
    assert result[("dbo", "FactSales")] == TableClassification.FACT
    assert result[("staging", "TempData")] == TableClassification.UNCLASSIFIED


def test_classify_tables_empty_input() -> None:
    """Empty input returns empty dict."""
    result = classify_tables([], key_prefixes=["SK_", "FK_"])
    assert result == {}


def test_classify_tables_key_is_schema_and_table_tuple() -> None:
    """Dict key is (schema_name, table_name) tuple."""
    tables = [
        TableMetadata(
            schema_name="sales",
            table_name="DimProduct",
            columns=(make_column("SK_ProductID", 1),),
        ),
        TableMetadata(
            schema_name="hr",
            table_name="DimEmployee",
            columns=(make_column("SK_EmployeeID", 1),),
        ),
    ]
    result = classify_tables(tables, key_prefixes=["SK_"])

    assert ("sales", "DimProduct") in result
    assert ("hr", "DimEmployee") in result
    assert result[("sales", "DimProduct")] == TableClassification.DIMENSION
    assert result[("hr", "DimEmployee")] == TableClassification.DIMENSION


def test_classify_tables_same_table_name_different_schemas() -> None:
    """Same table name in different schemas get unique keys."""
    tables = [
        TableMetadata(
            schema_name="schema1",
            table_name="Data",
            columns=(make_column("SK_ID", 1),),
        ),
        TableMetadata(
            schema_name="schema2",
            table_name="Data",
            columns=(
                make_column("FK_ID1", 1),
                make_column("FK_ID2", 2),
            ),
        ),
    ]
    result = classify_tables(tables, key_prefixes=["SK_", "FK_"])

    assert len(result) == 2
    assert result[("schema1", "Data")] == TableClassification.DIMENSION
    assert result[("schema2", "Data")] == TableClassification.FACT
