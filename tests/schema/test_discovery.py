"""Tests for schema discovery from INFORMATION_SCHEMA."""

from unittest.mock import Mock

from semantic_model_generator.schema.discovery import discover_tables


class TestDiscoverTables:
    """Test INFORMATION_SCHEMA discovery with mocked database cursor."""

    def test_single_table_with_columns(self):
        """Single schema with one table and two columns."""
        # Mock connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Simulate INFORMATION_SCHEMA query results
        # Columns: TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE,
        #          ORDINAL_POSITION, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
        mock_cursor.fetchall.return_value = [
            ("dbo", "DimCustomer", "SK_CustomerID", "bigint", "NO", 1, None, 19, 0),
            ("dbo", "DimCustomer", "Name", "varchar", "YES", 2, 100, None, None),
        ]

        result = discover_tables(mock_conn, ["dbo"])

        # Verify result structure
        assert len(result) == 1
        table = result[0]
        assert table.schema_name == "dbo"
        assert table.table_name == "DimCustomer"
        assert len(table.columns) == 2

        # Verify column 1
        col1 = table.columns[0]
        assert col1.name == "SK_CustomerID"
        assert col1.sql_type == "bigint"
        assert col1.is_nullable is False
        assert col1.ordinal_position == 1
        assert col1.max_length is None
        assert col1.numeric_precision == 19
        assert col1.numeric_scale == 0

        # Verify column 2
        col2 = table.columns[1]
        assert col2.name == "Name"
        assert col2.sql_type == "varchar"
        assert col2.is_nullable is True
        assert col2.ordinal_position == 2
        assert col2.max_length == 100
        assert col2.numeric_precision is None
        assert col2.numeric_scale is None

    def test_multiple_tables_same_schema(self):
        """Two tables in same schema."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            ("dbo", "DimCustomer", "CustomerID", "bigint", "NO", 1, None, 19, 0),
            ("dbo", "DimProduct", "ProductID", "bigint", "NO", 1, None, 19, 0),
            ("dbo", "DimProduct", "ProductName", "varchar", "YES", 2, 200, None, None),
        ]

        result = discover_tables(mock_conn, ["dbo"])

        assert len(result) == 2
        # Tables should be returned (order may vary)
        table_names = {table.table_name for table in result}
        assert table_names == {"DimCustomer", "DimProduct"}

        # Find DimProduct and verify it has 2 columns
        dim_product = next(t for t in result if t.table_name == "DimProduct")
        assert len(dim_product.columns) == 2

    def test_tables_across_multiple_schemas(self):
        """Tables in different schemas."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            ("dbo", "DimCustomer", "CustomerID", "bigint", "NO", 1, None, 19, 0),
            ("staging", "StageOrders", "OrderID", "bigint", "NO", 1, None, 19, 0),
        ]

        result = discover_tables(mock_conn, ["dbo", "staging"])

        assert len(result) == 2
        schemas = {table.schema_name for table in result}
        assert schemas == {"dbo", "staging"}

    def test_query_contains_base_table_filter(self):
        """Query filters for TABLE_TYPE = 'BASE TABLE' to exclude views."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        discover_tables(mock_conn, ["dbo"])

        # Verify the query was executed
        assert mock_cursor.execute.called
        query = mock_cursor.execute.call_args[0][0]

        # Verify critical query components
        assert "TABLE_TYPE = 'BASE TABLE'" in query
        assert "INFORMATION_SCHEMA.TABLES" in query
        assert "INFORMATION_SCHEMA.COLUMNS" in query
        assert "INNER JOIN" in query or "JOIN" in query

    def test_schema_filtering_parameterized(self):
        """Query uses parameterized schema list."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        schemas = ["dbo", "staging", "analytics"]
        discover_tables(mock_conn, schemas)

        # Verify execute was called with schemas as parameters
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]  # Second argument should be the parameters
        assert params == ["dbo", "staging", "analytics"]

    def test_columns_preserve_ordinal_order(self):
        """Columns are ordered by ORDINAL_POSITION."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Return rows in non-ordinal order to test sorting
        mock_cursor.fetchall.return_value = [
            ("dbo", "Test", "Col3", "int", "NO", 3, None, 10, 0),
            ("dbo", "Test", "Col1", "int", "NO", 1, None, 10, 0),
            ("dbo", "Test", "Col2", "int", "NO", 2, None, 10, 0),
        ]

        result = discover_tables(mock_conn, ["dbo"])

        # Verify columns are in ordinal order
        table = result[0]
        assert table.columns[0].ordinal_position == 1
        assert table.columns[1].ordinal_position == 2
        assert table.columns[2].ordinal_position == 3

    def test_empty_result_set(self):
        """No tables found returns empty tuple."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        result = discover_tables(mock_conn, ["dbo"])

        assert result == ()
        assert isinstance(result, tuple)

    def test_nullable_mapping(self):
        """IS_NULLABLE 'YES'/'NO' maps to True/False."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            ("dbo", "Test", "Col1", "int", "YES", 1, None, 10, 0),
            ("dbo", "Test", "Col2", "int", "NO", 2, None, 10, 0),
        ]

        result = discover_tables(mock_conn, ["dbo"])

        table = result[0]
        assert table.columns[0].is_nullable is True
        assert table.columns[1].is_nullable is False

    def test_null_values_in_optional_fields(self):
        """NULL max_length/numeric_precision/numeric_scale map to None."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            ("dbo", "Test", "Col1", "varchar", "YES", 1, None, None, None),
        ]

        result = discover_tables(mock_conn, ["dbo"])

        col = result[0].columns[0]
        assert col.max_length is None
        assert col.numeric_precision is None
        assert col.numeric_scale is None

    def test_return_type_is_immutable_tuple(self):
        """Returns tuple[TableMetadata, ...] (immutable)."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            ("dbo", "Test", "Col1", "int", "NO", 1, None, 10, 0),
        ]

        result = discover_tables(mock_conn, ["dbo"])

        assert isinstance(result, tuple)
        assert isinstance(result[0].columns, tuple)

    def test_empty_schema_list_returns_empty_tuple(self):
        """Empty schema list returns empty tuple without querying."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        result = discover_tables(mock_conn, [])

        assert result == ()
        # Should not execute query if no schemas provided
        assert not mock_cursor.execute.called
