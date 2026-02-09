"""Tests for table filtering by include and exclude lists."""

import pytest
from semantic_model_generator.schema.filtering import filter_tables

from semantic_model_generator.domain.types import ColumnMetadata, TableMetadata


@pytest.fixture
def sample_tables() -> list[TableMetadata]:
    """Create a list of sample tables for testing."""
    return [
        TableMetadata(
            schema_name="dbo",
            table_name="DimCustomer",
            columns=(
                ColumnMetadata(
                    name="SK_CustomerID",
                    sql_type="bigint",
                    is_nullable=False,
                    ordinal_position=1,
                ),
                ColumnMetadata(
                    name="Name",
                    sql_type="nvarchar",
                    is_nullable=True,
                    ordinal_position=2,
                    max_length=100,
                ),
            ),
        ),
        TableMetadata(
            schema_name="dbo",
            table_name="DimProduct",
            columns=(
                ColumnMetadata(
                    name="SK_ProductID",
                    sql_type="bigint",
                    is_nullable=False,
                    ordinal_position=1,
                ),
            ),
        ),
        TableMetadata(
            schema_name="dbo",
            table_name="FactSales",
            columns=(
                ColumnMetadata(
                    name="SK_SalesID",
                    sql_type="bigint",
                    is_nullable=False,
                    ordinal_position=1,
                ),
            ),
        ),
        TableMetadata(
            schema_name="dbo",
            table_name="FactOrders",
            columns=(
                ColumnMetadata(
                    name="SK_OrderID",
                    sql_type="bigint",
                    is_nullable=False,
                    ordinal_position=1,
                ),
            ),
        ),
        TableMetadata(
            schema_name="staging",
            table_name="StagingTemp",
            columns=(
                ColumnMetadata(
                    name="TempID",
                    sql_type="bigint",
                    is_nullable=False,
                    ordinal_position=1,
                ),
            ),
        ),
    ]


# Include-only filtering tests
def test_include_only_keeps_specified_tables(sample_tables: list[TableMetadata]) -> None:
    """Include list with 2 tables keeps only those 2 tables."""
    result = filter_tables(sample_tables, include=["DimCustomer", "FactSales"])
    assert len(result) == 2
    assert result[0].table_name == "DimCustomer"
    assert result[1].table_name == "FactSales"


def test_include_only_single_table(sample_tables: list[TableMetadata]) -> None:
    """Include list with 1 table keeps only that table."""
    result = filter_tables(sample_tables, include=["DimCustomer"])
    assert len(result) == 1
    assert result[0].table_name == "DimCustomer"


def test_include_nonexistent_returns_empty(sample_tables: list[TableMetadata]) -> None:
    """Include list with non-existent table returns empty list."""
    result = filter_tables(sample_tables, include=["NonExistent"])
    assert len(result) == 0


def test_include_empty_list_returns_empty(sample_tables: list[TableMetadata]) -> None:
    """Empty include list returns empty list (no tables match)."""
    result = filter_tables(sample_tables, include=[])
    assert len(result) == 0


# Exclude-only filtering tests
def test_exclude_only_removes_specified_table(sample_tables: list[TableMetadata]) -> None:
    """Exclude list removes specified table, keeps others."""
    result = filter_tables(sample_tables, exclude=["StagingTemp"])
    assert len(result) == 4
    table_names = [t.table_name for t in result]
    assert "StagingTemp" not in table_names
    assert "DimCustomer" in table_names


def test_exclude_only_removes_multiple_tables(sample_tables: list[TableMetadata]) -> None:
    """Exclude list removes multiple tables, keeps others."""
    result = filter_tables(sample_tables, exclude=["DimCustomer", "FactSales"])
    assert len(result) == 3
    table_names = [t.table_name for t in result]
    assert "DimCustomer" not in table_names
    assert "FactSales" not in table_names
    assert "DimProduct" in table_names
    assert "FactOrders" in table_names
    assert "StagingTemp" in table_names


def test_exclude_nonexistent_returns_all(sample_tables: list[TableMetadata]) -> None:
    """Exclude list with non-existent table returns all tables."""
    result = filter_tables(sample_tables, exclude=["NonExistent"])
    assert len(result) == 5
    assert result == sample_tables


def test_exclude_empty_list_returns_all(sample_tables: list[TableMetadata]) -> None:
    """Empty exclude list returns all tables."""
    result = filter_tables(sample_tables, exclude=[])
    assert len(result) == 5
    assert result == sample_tables


# Combined include + exclude tests
def test_combined_include_then_exclude(sample_tables: list[TableMetadata]) -> None:
    """Include is applied first, then exclude is applied to the result."""
    result = filter_tables(
        sample_tables,
        include=["DimCustomer", "DimProduct", "FactSales"],
        exclude=["DimProduct"],
    )
    assert len(result) == 2
    table_names = [t.table_name for t in result]
    assert "DimCustomer" in table_names
    assert "FactSales" in table_names
    assert "DimProduct" not in table_names


# No filtering tests
def test_no_filtering_returns_all_unchanged(sample_tables: list[TableMetadata]) -> None:
    """No include or exclude returns all tables unchanged."""
    result = filter_tables(sample_tables)
    assert len(result) == 5
    assert result == sample_tables


def test_no_filtering_preserves_order(sample_tables: list[TableMetadata]) -> None:
    """No filtering preserves input order."""
    result = filter_tables(sample_tables, include=None, exclude=None)
    assert result == sample_tables
    for i, table in enumerate(result):
        assert table.table_name == sample_tables[i].table_name


# Edge case tests
def test_empty_input_returns_empty(sample_tables: list[TableMetadata]) -> None:
    """Empty input list returns empty list regardless of include/exclude."""
    result = filter_tables([], include=["DimCustomer"])
    assert len(result) == 0

    result = filter_tables([], exclude=["DimCustomer"])
    assert len(result) == 0

    result = filter_tables([])
    assert len(result) == 0


def test_case_sensitive_matching(sample_tables: list[TableMetadata]) -> None:
    """Table name matching is case-sensitive."""
    result = filter_tables(sample_tables, include=["dimcustomer"])
    assert len(result) == 0  # Should not match "DimCustomer"

    result = filter_tables(sample_tables, include=["DimCustomer"])
    assert len(result) == 1  # Should match exact case
