"""End-to-end integration tests for the semantic model generation pipeline.

These tests verify the complete pipeline from schema discovery through TMDL file generation
using representative warehouse schemas. The tests mock only the database connection layer
(mssql_python), exercising real filtering, classification, relationship inference, TMDL
generation, and folder writing code paths.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from semantic_model_generator import PipelineConfig, PipelineError, generate_semantic_model

# Test data representing a representative star schema
# Format: (TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION,
#          CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE)
STAR_SCHEMA_ROWS = [
    # DimCustomer (1 key = dimension)
    ("dbo", "DimCustomer", "SK_Customer", "bigint", "NO", 1, None, 19, 0),
    ("dbo", "DimCustomer", "CustomerName", "varchar", "YES", 2, 100, None, None),
    ("dbo", "DimCustomer", "Email", "varchar", "YES", 3, 200, None, None),
    # DimProduct (1 key = dimension)
    ("dbo", "DimProduct", "SK_Product", "bigint", "NO", 1, None, 19, 0),
    ("dbo", "DimProduct", "ProductName", "varchar", "YES", 2, 150, None, None),
    ("dbo", "DimProduct", "Category", "varchar", "YES", 3, 50, None, None),
    # FactSales (3 keys = fact, references both dims + role-playing customer)
    ("dbo", "FactSales", "SK_Customer", "bigint", "NO", 1, None, 19, 0),
    ("dbo", "FactSales", "SK_Customer_ShipTo", "bigint", "NO", 2, None, 19, 0),
    ("dbo", "FactSales", "SK_Product", "bigint", "NO", 3, None, 19, 0),
    ("dbo", "FactSales", "Amount", "decimal", "NO", 4, None, 18, 2),
    ("dbo", "FactSales", "Quantity", "int", "NO", 5, None, 10, 0),
]


@pytest.fixture
def mock_connection():
    """Fixture providing a mocked database connection with star schema test data.

    Patches semantic_model_generator.schema.connection.mssql_python and returns a mock
    connection whose cursor returns STAR_SCHEMA_ROWS.
    """
    with patch("semantic_model_generator.schema.connection.mssql_python") as mock_mssql:
        # Create mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Configure cursor to return star schema test data
        mock_cursor.fetchall.return_value = STAR_SCHEMA_ROWS

        # Wire up the mock chain: connect() -> connection -> cursor() -> cursor
        mock_conn.cursor.return_value = mock_cursor
        mock_mssql.connect.return_value = mock_conn

        yield mock_mssql


class TestEndToEndFolderOutput:
    """Integration tests for end-to-end pipeline with folder output mode."""

    def test_full_pipeline_creates_tmdl_folder(
        self, mock_connection: MagicMock, tmp_path: Path
    ) -> None:
        """Complete pipeline creates folder with all expected TMDL files."""
        config = PipelineConfig(
            sql_endpoint="test-endpoint.fabric.microsoft.com",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="TestModel",
            catalog_name="test_catalog",
            output_mode="folder",
            output_path=tmp_path,
        )

        result = generate_semantic_model(config)

        # Verify result structure
        assert result["mode"] == "folder"
        assert result["output_path"].exists()

        # Verify key files exist
        output_dir = result["output_path"]
        assert (output_dir / ".platform").exists()
        assert (output_dir / "definition.pbism").exists()
        assert (output_dir / "definition" / "database.tmdl").exists()
        assert (output_dir / "definition" / "model.tmdl").exists()
        assert (output_dir / "definition" / "expressions.tmdl").exists()
        assert (output_dir / "definition" / "relationships.tmdl").exists()
        assert (output_dir / "definition" / "tables" / "DimCustomer.tmdl").exists()
        assert (output_dir / "definition" / "tables" / "DimProduct.tmdl").exists()
        assert (output_dir / "definition" / "tables" / "FactSales.tmdl").exists()
        assert (output_dir / "diagramLayout.json").exists()

    def test_dimension_classification_correct(
        self, mock_connection: MagicMock, tmp_path: Path
    ) -> None:
        """Dimension tables classified correctly in generated TMDL."""
        config = PipelineConfig(
            sql_endpoint="test-endpoint.fabric.microsoft.com",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="TestModel",
            catalog_name="test_catalog",
            output_mode="folder",
            output_path=tmp_path,
        )

        result = generate_semantic_model(config)
        output_dir = result["output_path"]

        # Read dimension table files and verify they contain table definitions
        dim_customer = (output_dir / "definition" / "tables" / "DimCustomer.tmdl").read_text()
        dim_product = (output_dir / "definition" / "tables" / "DimProduct.tmdl").read_text()

        assert "table DimCustomer" in dim_customer
        assert "table DimProduct" in dim_product

    def test_fact_classification_correct(self, mock_connection: MagicMock, tmp_path: Path) -> None:
        """Fact table classified correctly in generated TMDL."""
        config = PipelineConfig(
            sql_endpoint="test-endpoint.fabric.microsoft.com",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="TestModel",
            catalog_name="test_catalog",
            output_mode="folder",
            output_path=tmp_path,
        )

        result = generate_semantic_model(config)
        output_dir = result["output_path"]

        # Read fact table file and verify it contains table definition
        fact_sales = (output_dir / "definition" / "tables" / "FactSales.tmdl").read_text()
        assert "table FactSales" in fact_sales

    def test_relationships_generated(self, mock_connection: MagicMock, tmp_path: Path) -> None:
        """Relationships inferred and written to relationships.tmdl."""
        config = PipelineConfig(
            sql_endpoint="test-endpoint.fabric.microsoft.com",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="TestModel",
            catalog_name="test_catalog",
            output_mode="folder",
            output_path=tmp_path,
        )

        result = generate_semantic_model(config)
        output_dir = result["output_path"]

        # Read relationships file and verify it contains expected relationships
        relationships = (output_dir / "definition" / "relationships.tmdl").read_text()

        # Should have relationships for SK_Customer and SK_Product
        assert "SK_Customer" in relationships
        assert "SK_Product" in relationships

    def test_role_playing_dimension_detected(
        self, mock_connection: MagicMock, tmp_path: Path
    ) -> None:
        """Role-playing dimension creates both active and inactive relationships."""
        config = PipelineConfig(
            sql_endpoint="test-endpoint.fabric.microsoft.com",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="TestModel",
            catalog_name="test_catalog",
            output_mode="folder",
            output_path=tmp_path,
        )

        result = generate_semantic_model(config)
        output_dir = result["output_path"]

        # Read relationships file
        relationships = (output_dir / "definition" / "relationships.tmdl").read_text()

        # Should have both customer relationships (one active, one inactive)
        assert "SK_Customer_ShipTo" in relationships
        # Inactive relationship should have isActive: false
        assert "isActive: false" in relationships

    def test_dev_mode_creates_timestamped_folder(
        self, mock_connection: MagicMock, tmp_path: Path
    ) -> None:
        """Dev mode appends timestamp to folder name."""
        config = PipelineConfig(
            sql_endpoint="test-endpoint.fabric.microsoft.com",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="TestModel",
            catalog_name="test_catalog",
            output_mode="folder",
            output_path=tmp_path,
            dev_mode=True,
        )

        result = generate_semantic_model(config)

        # Output path should contain underscore followed by timestamp
        output_name = result["output_path"].name
        assert "_" in output_name
        assert output_name.startswith("TestModel_")

    def test_write_summary_reports_all_files(
        self, mock_connection: MagicMock, tmp_path: Path
    ) -> None:
        """WriteSummary contains all written files."""
        config = PipelineConfig(
            sql_endpoint="test-endpoint.fabric.microsoft.com",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="TestModel",
            catalog_name="test_catalog",
            output_mode="folder",
            output_path=tmp_path,
        )

        result = generate_semantic_model(config)
        summary = result["summary"]

        # Summary should have written files
        assert len(summary.written) > 0
        # Should have at least the 3 table files plus base files
        assert len(summary.written) >= 10


class TestEndToEndWithFiltering:
    """Integration tests for table filtering."""

    def test_include_filter_limits_tables(self, mock_connection: MagicMock, tmp_path: Path) -> None:
        """include_tables limits output to specified tables."""
        config = PipelineConfig(
            sql_endpoint="test-endpoint.fabric.microsoft.com",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="TestModel",
            catalog_name="test_catalog",
            output_mode="folder",
            output_path=tmp_path,
            include_tables=("DimCustomer", "FactSales"),
        )

        result = generate_semantic_model(config)
        output_dir = result["output_path"]

        # Should have DimCustomer and FactSales
        assert (output_dir / "definition" / "tables" / "DimCustomer.tmdl").exists()
        assert (output_dir / "definition" / "tables" / "FactSales.tmdl").exists()
        # Should NOT have DimProduct
        assert not (output_dir / "definition" / "tables" / "DimProduct.tmdl").exists()

    def test_exclude_filter_removes_tables(
        self, mock_connection: MagicMock, tmp_path: Path
    ) -> None:
        """exclude_tables removes specified tables from output."""
        config = PipelineConfig(
            sql_endpoint="test-endpoint.fabric.microsoft.com",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="TestModel",
            catalog_name="test_catalog",
            output_mode="folder",
            output_path=tmp_path,
            exclude_tables=("DimProduct",),
        )

        result = generate_semantic_model(config)
        output_dir = result["output_path"]

        # Should have DimCustomer and FactSales
        assert (output_dir / "definition" / "tables" / "DimCustomer.tmdl").exists()
        assert (output_dir / "definition" / "tables" / "FactSales.tmdl").exists()
        # Should NOT have DimProduct
        assert not (output_dir / "definition" / "tables" / "DimProduct.tmdl").exists()


class TestEndToEndErrorPaths:
    """Integration tests for error handling."""

    def test_connection_failure_gives_pipeline_error(self, tmp_path: Path) -> None:
        """Connection failure produces PipelineError with stage=connection."""
        with patch("semantic_model_generator.schema.connection.mssql_python") as mock_mssql:
            # Make connection raise an exception
            mock_mssql.connect.side_effect = RuntimeError("Connection failed")

            config = PipelineConfig(
                sql_endpoint="test-endpoint.fabric.microsoft.com",
                database="test_db",
                schemas=("dbo",),
                key_prefixes=("SK_",),
                model_name="TestModel",
                catalog_name="test_catalog",
                output_mode="folder",
                output_path=tmp_path,
            )

            with pytest.raises(PipelineError) as exc_info:
                generate_semantic_model(config)

            assert exc_info.value.stage == "connection"

    def test_empty_schema_result_handled(self, mock_connection: MagicMock, tmp_path: Path) -> None:
        """Empty schema result handled gracefully."""
        # Override mock to return empty result
        mock_connection.connect.return_value.cursor.return_value.fetchall.return_value = []

        config = PipelineConfig(
            sql_endpoint="test-endpoint.fabric.microsoft.com",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="TestModel",
            catalog_name="test_catalog",
            output_mode="folder",
            output_path=tmp_path,
        )

        result = generate_semantic_model(config)

        # Should complete successfully with no table files
        assert result["mode"] == "folder"
        tables_dir = result["output_path"] / "definition" / "tables"
        if tables_dir.exists():
            table_files = list(tables_dir.glob("*.tmdl"))
            assert len(table_files) == 0


class TestPublicApiImports:
    """Test public API exports from top-level package."""

    def test_import_generate_semantic_model(self) -> None:
        """Can import generate_semantic_model from top-level package."""
        from semantic_model_generator import generate_semantic_model

        assert callable(generate_semantic_model)

    def test_import_pipeline_config(self) -> None:
        """Can import PipelineConfig from top-level package."""
        from semantic_model_generator import PipelineConfig

        assert PipelineConfig is not None

    def test_import_pipeline_error(self) -> None:
        """Can import PipelineError from top-level package."""
        from semantic_model_generator import PipelineError

        assert issubclass(PipelineError, Exception)
