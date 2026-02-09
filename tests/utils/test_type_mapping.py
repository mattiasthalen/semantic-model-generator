"""Tests for SQL-to-TMDL type mapping."""

import pytest
from semantic_model_generator.utils.type_mapping import (
    SQL_TO_TMDL_TYPE,
    map_sql_type_to_tmdl,
)

from semantic_model_generator.domain.types import TmdlDataType


class TestExactMappings:
    """Test exact SQL type to TMDL type mappings."""

    @pytest.mark.parametrize(
        ("sql_type", "expected_tmdl_type"),
        [
            ("bit", TmdlDataType.BOOLEAN),
            ("smallint", TmdlDataType.INT64),
            ("int", TmdlDataType.INT64),
            ("bigint", TmdlDataType.INT64),
            ("decimal", TmdlDataType.DECIMAL),
            ("numeric", TmdlDataType.DECIMAL),
            ("float", TmdlDataType.DOUBLE),
            ("real", TmdlDataType.DOUBLE),
            ("char", TmdlDataType.STRING),
            ("varchar", TmdlDataType.STRING),
            ("date", TmdlDataType.DATETIME),
            ("datetime2", TmdlDataType.DATETIME),
            ("time", TmdlDataType.DATETIME),
            ("varbinary", TmdlDataType.BINARY),
            ("uniqueidentifier", TmdlDataType.BINARY),
        ],
    )
    def test_sql_type_maps_to_tmdl_type(
        self, sql_type: str, expected_tmdl_type: TmdlDataType
    ) -> None:
        """Each SQL type should map to the correct TMDL type."""
        result = map_sql_type_to_tmdl(sql_type)
        assert result == expected_tmdl_type


class TestCaseInsensitivity:
    """Test case-insensitive SQL type handling."""

    def test_uppercase_varchar(self) -> None:
        """VARCHAR (uppercase) should map to STRING."""
        assert map_sql_type_to_tmdl("VARCHAR") == TmdlDataType.STRING

    def test_mixed_case_int(self) -> None:
        """Int (mixed case) should map to INT64."""
        assert map_sql_type_to_tmdl("Int") == TmdlDataType.INT64

    def test_uppercase_bigint(self) -> None:
        """BIGINT (uppercase) should map to INT64."""
        assert map_sql_type_to_tmdl("BIGINT") == TmdlDataType.INT64


class TestWhitespaceHandling:
    """Test whitespace handling in SQL type input."""

    def test_leading_trailing_spaces_varchar(self) -> None:
        """' varchar ' (with spaces) should map to STRING."""
        assert map_sql_type_to_tmdl(" varchar ") == TmdlDataType.STRING

    def test_leading_trailing_spaces_int(self) -> None:
        """'  int  ' (with spaces) should map to INT64."""
        assert map_sql_type_to_tmdl("  int  ") == TmdlDataType.INT64


class TestErrorCases:
    """Test error handling for unsupported types."""

    def test_unsupported_type_raises_value_error(self) -> None:
        """Unsupported type should raise ValueError."""
        with pytest.raises(ValueError):
            map_sql_type_to_tmdl("unsupported_type")

    def test_empty_string_raises_value_error(self) -> None:
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError):
            map_sql_type_to_tmdl("")

    def test_error_message_contains_supported_types(self) -> None:
        """ValueError message should list supported types."""
        with pytest.raises(ValueError, match="Supported types:"):
            map_sql_type_to_tmdl("unsupported_type")

    def test_error_message_shows_unsupported_type(self) -> None:
        """ValueError message should show the unsupported type."""
        with pytest.raises(ValueError, match="unsupported_type"):
            map_sql_type_to_tmdl("unsupported_type")


class TestSqlToTmdlTypeDict:
    """Test SQL_TO_TMDL_TYPE dictionary."""

    def test_dict_has_exactly_15_entries(self) -> None:
        """SQL_TO_TMDL_TYPE should have exactly 15 entries."""
        assert len(SQL_TO_TMDL_TYPE) == 15

    def test_all_values_are_tmdl_data_type(self) -> None:
        """All values in SQL_TO_TMDL_TYPE should be TmdlDataType members."""
        for value in SQL_TO_TMDL_TYPE.values():
            assert isinstance(value, TmdlDataType)
