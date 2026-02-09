"""Tests for domain types - TmdlDataType enum and frozen dataclasses."""

import dataclasses
from enum import StrEnum

import pytest

from semantic_model_generator.domain.types import ColumnMetadata, TableMetadata, TmdlDataType


class TestTmdlDataType:
    """Tests for TmdlDataType enum."""

    def test_is_str_enum(self) -> None:
        """TmdlDataType should be a StrEnum subclass."""
        assert issubclass(TmdlDataType, StrEnum)

    def test_int64_value(self) -> None:
        """TmdlDataType.INT64 should equal 'int64'."""
        assert TmdlDataType.INT64 == "int64"

    def test_double_value(self) -> None:
        """TmdlDataType.DOUBLE should equal 'double'."""
        assert TmdlDataType.DOUBLE == "double"

    def test_boolean_value(self) -> None:
        """TmdlDataType.BOOLEAN should equal 'boolean'."""
        assert TmdlDataType.BOOLEAN == "boolean"

    def test_string_value(self) -> None:
        """TmdlDataType.STRING should equal 'string'."""
        assert TmdlDataType.STRING == "string"

    def test_datetime_value(self) -> None:
        """TmdlDataType.DATETIME should equal 'dateTime' (camelCase)."""
        assert TmdlDataType.DATETIME == "dateTime"

    def test_decimal_value(self) -> None:
        """TmdlDataType.DECIMAL should equal 'decimal'."""
        assert TmdlDataType.DECIMAL == "decimal"

    def test_binary_value(self) -> None:
        """TmdlDataType.BINARY should equal 'binary'."""
        assert TmdlDataType.BINARY == "binary"

    def test_has_exactly_seven_members(self) -> None:
        """TmdlDataType should have exactly 7 members."""
        assert len(TmdlDataType) == 7


class TestColumnMetadata:
    """Tests for ColumnMetadata frozen dataclass."""

    def test_construction_with_required_fields(self) -> None:
        """Should construct with required fields."""
        col = ColumnMetadata(
            name="ProductName",
            sql_type="varchar",
            is_nullable=False,
            ordinal_position=1,
        )
        assert col.name == "ProductName"
        assert col.sql_type == "varchar"
        assert col.is_nullable is False
        assert col.ordinal_position == 1

    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields should default to None."""
        col = ColumnMetadata(
            name="ProductName",
            sql_type="varchar",
            is_nullable=False,
            ordinal_position=1,
        )
        assert col.max_length is None
        assert col.numeric_precision is None
        assert col.numeric_scale is None

    def test_frozen_cannot_assign_to_name(self) -> None:
        """Assigning to col.name should raise FrozenInstanceError."""
        col = ColumnMetadata(
            name="ProductName",
            sql_type="varchar",
            is_nullable=False,
            ordinal_position=1,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            col.name = "NewName"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Two instances with same values should be equal."""
        col1 = ColumnMetadata(
            name="ProductName",
            sql_type="varchar",
            is_nullable=False,
            ordinal_position=1,
        )
        col2 = ColumnMetadata(
            name="ProductName",
            sql_type="varchar",
            is_nullable=False,
            ordinal_position=1,
        )
        assert col1 == col2

    def test_hashable(self) -> None:
        """ColumnMetadata should be hashable and can be added to a set."""
        col1 = ColumnMetadata(
            name="ProductName",
            sql_type="varchar",
            is_nullable=False,
            ordinal_position=1,
        )
        col2 = ColumnMetadata(
            name="ProductID",
            sql_type="int",
            is_nullable=False,
            ordinal_position=2,
        )
        col_set = {col1, col2}
        assert len(col_set) == 2
        assert col1 in col_set

    def test_validation_empty_name_raises_value_error(self) -> None:
        """Empty name should raise ValueError."""
        with pytest.raises(ValueError, match="Column name cannot be empty"):
            ColumnMetadata(
                name="",
                sql_type="varchar",
                is_nullable=False,
                ordinal_position=1,
            )

    def test_validation_ordinal_position_less_than_1_raises_value_error(self) -> None:
        """Ordinal position < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="Ordinal position must be >= 1"):
            ColumnMetadata(
                name="ProductName",
                sql_type="varchar",
                is_nullable=False,
                ordinal_position=0,
            )


class TestTableMetadata:
    """Tests for TableMetadata frozen dataclass."""

    def test_construction_with_required_fields(self) -> None:
        """Should construct with required fields."""
        col = ColumnMetadata(
            name="ProductName",
            sql_type="varchar",
            is_nullable=False,
            ordinal_position=1,
        )
        table = TableMetadata(
            schema_name="dbo",
            table_name="Product",
            columns=(col,),
        )
        assert table.schema_name == "dbo"
        assert table.table_name == "Product"
        assert len(table.columns) == 1
        assert table.columns[0] == col

    def test_frozen_cannot_assign(self) -> None:
        """Assigning to table fields should raise FrozenInstanceError."""
        col = ColumnMetadata(
            name="ProductName",
            sql_type="varchar",
            is_nullable=False,
            ordinal_position=1,
        )
        table = TableMetadata(
            schema_name="dbo",
            table_name="Product",
            columns=(col,),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            table.table_name = "NewTable"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Two instances with same values should be equal."""
        col = ColumnMetadata(
            name="ProductName",
            sql_type="varchar",
            is_nullable=False,
            ordinal_position=1,
        )
        table1 = TableMetadata(
            schema_name="dbo",
            table_name="Product",
            columns=(col,),
        )
        table2 = TableMetadata(
            schema_name="dbo",
            table_name="Product",
            columns=(col,),
        )
        assert table1 == table2

    def test_hashable(self) -> None:
        """TableMetadata should be hashable."""
        col = ColumnMetadata(
            name="ProductName",
            sql_type="varchar",
            is_nullable=False,
            ordinal_position=1,
        )
        table = TableMetadata(
            schema_name="dbo",
            table_name="Product",
            columns=(col,),
        )
        table_set = {table}
        assert len(table_set) == 1
        assert table in table_set

    def test_columns_is_tuple(self) -> None:
        """Columns should be a tuple (not list) for immutability."""
        col = ColumnMetadata(
            name="ProductName",
            sql_type="varchar",
            is_nullable=False,
            ordinal_position=1,
        )
        table = TableMetadata(
            schema_name="dbo",
            table_name="Product",
            columns=(col,),
        )
        assert isinstance(table.columns, tuple)
