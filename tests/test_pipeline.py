"""Tests for pipeline orchestration module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from semantic_model_generator.domain.types import TableClassification, TableMetadata
from semantic_model_generator.output.watermark import WriteSummary
from semantic_model_generator.pipeline import PipelineConfig, PipelineError, generate_semantic_model


class TestPipelineConfig:
    """Test PipelineConfig validation."""

    def test_valid_folder_config(self) -> None:
        """Constructs valid folder mode config."""
        config = PipelineConfig(
            sql_endpoint="my-endpoint.fabric.microsoft.com",
            database="my_database",
            schemas=("dbo", "sales"),
            key_prefixes=("SK_", "ID_"),
            model_name="My Model",
            catalog_name="my_catalog",
            output_mode="folder",
            output_path=Path("/tmp/output"),
        )
        assert config.sql_endpoint == "my-endpoint.fabric.microsoft.com"
        assert config.database == "my_database"
        assert config.schemas == ("dbo", "sales")
        assert config.key_prefixes == ("SK_", "ID_")
        assert config.model_name == "My Model"
        assert config.catalog_name == "my_catalog"
        assert config.output_mode == "folder"
        assert config.output_path == Path("/tmp/output")

    def test_valid_fabric_config(self) -> None:
        """Constructs valid fabric mode config."""
        config = PipelineConfig(
            sql_endpoint="my-endpoint.fabric.microsoft.com",
            database="my_database",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="My Model",
            catalog_name="my_catalog",
            output_mode="fabric",
            workspace="my-workspace",
            lakehouse_or_warehouse="my-lakehouse",
        )
        assert config.output_mode == "fabric"
        assert config.workspace == "my-workspace"
        assert config.lakehouse_or_warehouse == "my-lakehouse"

    def test_schemas_cannot_be_empty(self) -> None:
        """Empty schemas tuple raises ValueError."""
        with pytest.raises(ValueError, match="schemas"):
            PipelineConfig(
                sql_endpoint="endpoint",
                database="db",
                schemas=(),
                key_prefixes=("SK_",),
                model_name="Model",
                catalog_name="catalog",
                output_path=Path("/tmp"),
            )

    def test_key_prefixes_cannot_be_empty(self) -> None:
        """Empty key_prefixes tuple raises ValueError."""
        with pytest.raises(ValueError, match="key_prefixes"):
            PipelineConfig(
                sql_endpoint="endpoint",
                database="db",
                schemas=("dbo",),
                key_prefixes=(),
                model_name="Model",
                catalog_name="catalog",
                output_path=Path("/tmp"),
            )

    def test_invalid_output_mode(self) -> None:
        """Invalid output_mode raises ValueError."""
        with pytest.raises(ValueError, match="output_mode"):
            PipelineConfig(
                sql_endpoint="endpoint",
                database="db",
                schemas=("dbo",),
                key_prefixes=("SK_",),
                model_name="Model",
                catalog_name="catalog",
                output_mode="invalid",
            )

    def test_folder_mode_requires_output_path(self) -> None:
        """Folder mode without output_path raises ValueError."""
        with pytest.raises(ValueError, match="output_path"):
            PipelineConfig(
                sql_endpoint="endpoint",
                database="db",
                schemas=("dbo",),
                key_prefixes=("SK_",),
                model_name="Model",
                catalog_name="catalog",
                output_mode="folder",
            )

    def test_fabric_mode_requires_workspace(self) -> None:
        """Fabric mode without workspace raises ValueError."""
        with pytest.raises(ValueError, match="workspace"):
            PipelineConfig(
                sql_endpoint="endpoint",
                database="db",
                schemas=("dbo",),
                key_prefixes=("SK_",),
                model_name="Model",
                catalog_name="catalog",
                output_mode="fabric",
                lakehouse_or_warehouse="lakehouse",
            )

    def test_fabric_mode_requires_lakehouse(self) -> None:
        """Fabric mode without lakehouse_or_warehouse raises ValueError."""
        with pytest.raises(ValueError, match="lakehouse_or_warehouse"):
            PipelineConfig(
                sql_endpoint="endpoint",
                database="db",
                schemas=("dbo",),
                key_prefixes=("SK_",),
                model_name="Model",
                catalog_name="catalog",
                output_mode="fabric",
                workspace="workspace",
            )

    def test_config_is_frozen(self) -> None:
        """Attempting to set attribute raises FrozenInstanceError."""
        config = PipelineConfig(
            sql_endpoint="endpoint",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="Model",
            catalog_name="catalog",
            output_path=Path("/tmp"),
        )
        # FrozenInstanceError becomes AttributeError or TypeError
        with pytest.raises((AttributeError, TypeError)):
            config.model_name = "New Name"  # type: ignore[misc]

    def test_config_defaults(self) -> None:
        """Verify default values."""
        config = PipelineConfig(
            sql_endpoint="endpoint",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="Model",
            catalog_name="catalog",
            output_path=Path("/tmp"),
        )
        assert config.output_mode == "folder"
        assert config.dev_mode is True
        assert config.overwrite is False
        assert config.confirm_overwrite is False
        assert config.item_type == "Lakehouse"

    def test_include_exclude_default_none(self) -> None:
        """include_tables and exclude_tables default to None."""
        config = PipelineConfig(
            sql_endpoint="endpoint",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="Model",
            catalog_name="catalog",
            output_path=Path("/tmp"),
        )
        assert config.include_tables is None
        assert config.exclude_tables is None

    def test_invalid_item_type(self) -> None:
        """Invalid item_type raises ValueError."""
        with pytest.raises(ValueError, match="item_type"):
            PipelineConfig(
                sql_endpoint="endpoint",
                database="db",
                schemas=("dbo",),
                key_prefixes=("SK_",),
                model_name="Model",
                catalog_name="catalog",
                output_mode="fabric",
                workspace="workspace",
                lakehouse_or_warehouse="lakehouse",
                item_type="Invalid",
            )


class TestPipelineError:
    """Test PipelineError exception."""

    def test_error_contains_stage(self) -> None:
        """PipelineError contains stage and appears in string."""
        error = PipelineError("connection", "Failed to connect")
        assert error.stage == "connection"
        assert "[connection]" in str(error)

    def test_error_contains_message(self) -> None:
        """Message appears in string representation."""
        error = PipelineError("discovery", "Failed to read schema")
        assert "Failed to read schema" in str(error)

    def test_error_preserves_cause(self) -> None:
        """Cause attribute stores original exception."""
        original = ValueError("Bad connection string")
        error = PipelineError("connection", "Failed to connect", original)
        assert error.cause is original

    def test_error_without_cause(self) -> None:
        """Cause defaults to None."""
        error = PipelineError("connection", "Failed to connect")
        assert error.cause is None


class TestGenerateSemanticModelFolderMode:
    """Test generate_semantic_model with folder output."""

    @patch("semantic_model_generator.pipeline.write_tmdl_folder")
    @patch("semantic_model_generator.pipeline.generate_all_tmdl")
    @patch("semantic_model_generator.pipeline.infer_relationships")
    @patch("semantic_model_generator.pipeline.classify_tables")
    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_folder_mode_calls_all_stages(
        self,
        mock_connect: MagicMock,
        mock_discover: MagicMock,
        mock_filter: MagicMock,
        mock_classify: MagicMock,
        mock_infer: MagicMock,
        mock_generate: MagicMock,
        mock_write: MagicMock,
    ) -> None:
        """Verify all 7 functions called in correct order."""
        # Setup mocks
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_tables = (TableMetadata("dbo", "Table1", ()),)
        mock_discover.return_value = mock_tables
        mock_filter.return_value = mock_tables
        mock_classifications = {("dbo", "Table1"): TableClassification.FACT}
        mock_classify.return_value = mock_classifications
        mock_relationships = ()
        mock_infer.return_value = mock_relationships
        mock_tmdl = {"model.tmdl": "table Table1"}
        mock_generate.return_value = mock_tmdl
        mock_summary = WriteSummary(
            written=("model.tmdl",), skipped=(), unchanged=(), output_path=Path("/tmp/output")
        )
        mock_write.return_value = mock_summary

        # Create config
        config = PipelineConfig(
            sql_endpoint="endpoint",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="Model",
            catalog_name="catalog",
            output_mode="folder",
            output_path=Path("/tmp/output"),
        )

        # Execute pipeline
        result = generate_semantic_model(config)

        # Verify call order and arguments
        mock_connect.assert_called_once_with("endpoint", "db")
        mock_discover.assert_called_once_with(mock_conn, ("dbo",))
        mock_filter.assert_called_once_with(mock_tables, None, None)
        mock_classify.assert_called_once_with(mock_tables, ("SK_",))
        mock_infer.assert_called_once_with(mock_tables, mock_classifications, ("SK_",))
        mock_generate.assert_called_once_with(
            "Model", mock_tables, mock_classifications, mock_relationships, ("SK_",), "catalog"
        )
        mock_write.assert_called_once_with(mock_tmdl, Path("/tmp/output"), "Model", True, False)

        # Verify result
        assert result["mode"] == "folder"
        assert result["output_path"] == Path("/tmp/output")
        assert result["summary"] == mock_summary

    @patch("semantic_model_generator.pipeline.write_tmdl_folder")
    @patch("semantic_model_generator.pipeline.generate_all_tmdl")
    @patch("semantic_model_generator.pipeline.infer_relationships")
    @patch("semantic_model_generator.pipeline.classify_tables")
    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_folder_mode_returns_result(
        self,
        mock_connect: MagicMock,
        mock_discover: MagicMock,
        mock_filter: MagicMock,
        mock_classify: MagicMock,
        mock_infer: MagicMock,
        mock_generate: MagicMock,
        mock_write: MagicMock,
    ) -> None:
        """Returns dict with mode, output_path, and summary."""
        # Setup mocks
        mock_connect.return_value = MagicMock()
        mock_tables = (TableMetadata("dbo", "T", ()),)
        mock_discover.return_value = mock_tables
        mock_filter.return_value = mock_tables
        mock_classify.return_value = {("dbo", "T"): TableClassification.FACT}
        mock_infer.return_value = ()
        mock_generate.return_value = {"model.tmdl": "table T"}
        mock_summary = WriteSummary(
            written=("model.tmdl",), skipped=(), unchanged=(), output_path=Path("/tmp/out")
        )
        mock_write.return_value = mock_summary

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_path=Path("/tmp"),
        )

        result = generate_semantic_model(config)

        assert "mode" in result
        assert "output_path" in result
        assert "summary" in result

    @patch("semantic_model_generator.pipeline.write_tmdl_folder")
    @patch("semantic_model_generator.pipeline.generate_all_tmdl")
    @patch("semantic_model_generator.pipeline.infer_relationships")
    @patch("semantic_model_generator.pipeline.classify_tables")
    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_folder_mode_passes_dev_mode(
        self,
        mock_connect: MagicMock,
        mock_discover: MagicMock,
        mock_filter: MagicMock,
        mock_classify: MagicMock,
        mock_infer: MagicMock,
        mock_generate: MagicMock,
        mock_write: MagicMock,
    ) -> None:
        """dev_mode and overwrite passed to write_tmdl_folder."""
        # Setup mocks
        mock_connect.return_value = MagicMock()
        mock_tables = (TableMetadata("dbo", "T", ()),)
        mock_discover.return_value = mock_tables
        mock_filter.return_value = mock_tables
        mock_classify.return_value = {("dbo", "T"): TableClassification.FACT}
        mock_infer.return_value = ()
        mock_generate.return_value = {"model.tmdl": "table T"}
        mock_write.return_value = WriteSummary(
            written=(), skipped=(), unchanged=(), output_path=Path("/tmp")
        )

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_path=Path("/tmp"),
            dev_mode=False,
            overwrite=True,
        )

        generate_semantic_model(config)

        # Verify dev_mode and overwrite passed
        mock_write.assert_called_once()
        call_args = mock_write.call_args
        assert call_args[0][3] is False  # dev_mode
        assert call_args[0][4] is True  # overwrite

    @patch("semantic_model_generator.pipeline.write_tmdl_folder")
    @patch("semantic_model_generator.pipeline.generate_all_tmdl")
    @patch("semantic_model_generator.pipeline.infer_relationships")
    @patch("semantic_model_generator.pipeline.classify_tables")
    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_folder_mode_passes_include_exclude(
        self,
        mock_connect: MagicMock,
        mock_discover: MagicMock,
        mock_filter: MagicMock,
        mock_classify: MagicMock,
        mock_infer: MagicMock,
        mock_generate: MagicMock,
        mock_write: MagicMock,
    ) -> None:
        """include_tables and exclude_tables forwarded to filter_tables."""
        # Setup mocks
        mock_connect.return_value = MagicMock()
        mock_tables = (TableMetadata("dbo", "T", ()),)
        mock_discover.return_value = mock_tables
        mock_filter.return_value = mock_tables
        mock_classify.return_value = {("dbo", "T"): TableClassification.FACT}
        mock_infer.return_value = ()
        mock_generate.return_value = {"model.tmdl": "table T"}
        mock_write.return_value = WriteSummary(
            written=(), skipped=(), unchanged=(), output_path=Path("/tmp")
        )

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_path=Path("/tmp"),
            include_tables=("T1", "T2"),
            exclude_tables=("T3",),
        )

        generate_semantic_model(config)

        # Verify filter_tables called with include/exclude
        mock_filter.assert_called_once_with(mock_tables, ("T1", "T2"), ("T3",))

    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_connection_error_wraps_as_pipeline_error(self, mock_connect: MagicMock) -> None:
        """Connection failure raises PipelineError with stage=connection."""
        mock_connect.side_effect = ValueError("Connection failed")

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_path=Path("/tmp"),
        )

        with pytest.raises(PipelineError) as exc_info:
            generate_semantic_model(config)

        assert exc_info.value.stage == "connection"
        assert isinstance(exc_info.value.cause, ValueError)

    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_discovery_error_wraps_as_pipeline_error(
        self, mock_connect: MagicMock, mock_discover: MagicMock
    ) -> None:
        """Discovery failure raises PipelineError with stage=discovery."""
        mock_connect.return_value = MagicMock()
        mock_discover.side_effect = RuntimeError("Schema read failed")

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_path=Path("/tmp"),
        )

        with pytest.raises(PipelineError) as exc_info:
            generate_semantic_model(config)

        assert exc_info.value.stage == "discovery"
        assert isinstance(exc_info.value.cause, RuntimeError)


class TestGenerateSemanticModelFabricMode:
    """Test generate_semantic_model with Fabric output."""

    @patch("semantic_model_generator.pipeline.deploy_semantic_model_dev")
    @patch("semantic_model_generator.pipeline.generate_all_tmdl")
    @patch("semantic_model_generator.pipeline.infer_relationships")
    @patch("semantic_model_generator.pipeline.classify_tables")
    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_fabric_dev_mode_calls_deploy_dev(
        self,
        mock_connect: MagicMock,
        mock_discover: MagicMock,
        mock_filter: MagicMock,
        mock_classify: MagicMock,
        mock_infer: MagicMock,
        mock_generate: MagicMock,
        mock_deploy_dev: MagicMock,
    ) -> None:
        """dev_mode=True calls deploy_semantic_model_dev."""
        # Setup mocks
        mock_connect.return_value = MagicMock()
        mock_tables = (TableMetadata("dbo", "T", ()),)
        mock_discover.return_value = mock_tables
        mock_filter.return_value = mock_tables
        mock_classify.return_value = {("dbo", "T"): TableClassification.FACT}
        mock_infer.return_value = ()
        mock_tmdl = {"model.tmdl": "table T"}
        mock_generate.return_value = mock_tmdl
        mock_deploy_dev.return_value = "model-id-123"

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_mode="fabric",
            workspace="ws",
            lakehouse_or_warehouse="lh",
            dev_mode=True,
        )

        result = generate_semantic_model(config)

        # Verify deploy_dev called
        mock_deploy_dev.assert_called_once_with(mock_tmdl, "ws", "M")
        assert result["mode"] == "fabric"
        assert result["model_id"] == "model-id-123"
        assert result["model_name"] == "M"

    @patch("semantic_model_generator.pipeline.deploy_semantic_model_prod")
    @patch("semantic_model_generator.pipeline.generate_all_tmdl")
    @patch("semantic_model_generator.pipeline.infer_relationships")
    @patch("semantic_model_generator.pipeline.classify_tables")
    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_fabric_prod_mode_calls_deploy_prod(
        self,
        mock_connect: MagicMock,
        mock_discover: MagicMock,
        mock_filter: MagicMock,
        mock_classify: MagicMock,
        mock_infer: MagicMock,
        mock_generate: MagicMock,
        mock_deploy_prod: MagicMock,
    ) -> None:
        """dev_mode=False calls deploy_semantic_model_prod."""
        # Setup mocks
        mock_connect.return_value = MagicMock()
        mock_tables = (TableMetadata("dbo", "T", ()),)
        mock_discover.return_value = mock_tables
        mock_filter.return_value = mock_tables
        mock_classify.return_value = {("dbo", "T"): TableClassification.FACT}
        mock_infer.return_value = ()
        mock_tmdl = {"model.tmdl": "table T"}
        mock_generate.return_value = mock_tmdl
        mock_deploy_prod.return_value = "model-id-456"

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_mode="fabric",
            workspace="ws",
            lakehouse_or_warehouse="lh",
            dev_mode=False,
            confirm_overwrite=True,
        )

        result = generate_semantic_model(config)

        # Verify deploy_prod called with confirm_overwrite
        mock_deploy_prod.assert_called_once_with(mock_tmdl, "ws", "M", True)
        assert result["mode"] == "fabric"
        assert result["model_id"] == "model-id-456"

    @patch("semantic_model_generator.pipeline.deploy_semantic_model_dev")
    @patch("semantic_model_generator.pipeline.generate_all_tmdl")
    @patch("semantic_model_generator.pipeline.infer_relationships")
    @patch("semantic_model_generator.pipeline.classify_tables")
    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_fabric_mode_returns_result(
        self,
        mock_connect: MagicMock,
        mock_discover: MagicMock,
        mock_filter: MagicMock,
        mock_classify: MagicMock,
        mock_infer: MagicMock,
        mock_generate: MagicMock,
        mock_deploy_dev: MagicMock,
    ) -> None:
        """Returns dict with mode, model_id, and model_name."""
        # Setup mocks
        mock_connect.return_value = MagicMock()
        mock_tables = (TableMetadata("dbo", "T", ()),)
        mock_discover.return_value = mock_tables
        mock_filter.return_value = mock_tables
        mock_classify.return_value = {("dbo", "T"): TableClassification.FACT}
        mock_infer.return_value = ()
        mock_generate.return_value = {"model.tmdl": "table T"}
        mock_deploy_dev.return_value = "id-789"

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="MyModel",
            catalog_name="cat",
            output_mode="fabric",
            workspace="ws",
            lakehouse_or_warehouse="lh",
        )

        result = generate_semantic_model(config)

        assert result["mode"] == "fabric"
        assert result["model_id"] == "id-789"
        assert result["model_name"] == "MyModel"

    @patch("semantic_model_generator.pipeline.deploy_semantic_model_dev")
    @patch("semantic_model_generator.pipeline.generate_all_tmdl")
    @patch("semantic_model_generator.pipeline.infer_relationships")
    @patch("semantic_model_generator.pipeline.classify_tables")
    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_deployment_error_wraps_as_pipeline_error(
        self,
        mock_connect: MagicMock,
        mock_discover: MagicMock,
        mock_filter: MagicMock,
        mock_classify: MagicMock,
        mock_infer: MagicMock,
        mock_generate: MagicMock,
        mock_deploy_dev: MagicMock,
    ) -> None:
        """Deployment failure raises PipelineError with stage=deployment."""
        # Setup mocks
        mock_connect.return_value = MagicMock()
        mock_tables = (TableMetadata("dbo", "T", ()),)
        mock_discover.return_value = mock_tables
        mock_filter.return_value = mock_tables
        mock_classify.return_value = {("dbo", "T"): TableClassification.FACT}
        mock_infer.return_value = ()
        mock_generate.return_value = {"model.tmdl": "table T"}
        mock_deploy_dev.side_effect = RuntimeError("Deployment failed")

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_mode="fabric",
            workspace="ws",
            lakehouse_or_warehouse="lh",
        )

        with pytest.raises(PipelineError) as exc_info:
            generate_semantic_model(config)

        assert exc_info.value.stage == "deployment"
        assert isinstance(exc_info.value.cause, RuntimeError)


class TestPipelineErrorStages:
    """Test error wrapping for remaining pipeline stages."""

    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_filtering_error_wraps(
        self, mock_connect: MagicMock, mock_discover: MagicMock, mock_filter: MagicMock
    ) -> None:
        """filter_tables failure -> PipelineError stage=filtering."""
        mock_connect.return_value = MagicMock()
        mock_discover.return_value = (TableMetadata("dbo", "T", ()),)
        mock_filter.side_effect = ValueError("Filter failed")

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_path=Path("/tmp"),
        )

        with pytest.raises(PipelineError) as exc_info:
            generate_semantic_model(config)

        assert exc_info.value.stage == "filtering"
        assert isinstance(exc_info.value.cause, ValueError)

    @patch("semantic_model_generator.pipeline.classify_tables")
    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_classification_error_wraps(
        self,
        mock_connect: MagicMock,
        mock_discover: MagicMock,
        mock_filter: MagicMock,
        mock_classify: MagicMock,
    ) -> None:
        """classify_tables failure -> PipelineError stage=classification."""
        mock_connect.return_value = MagicMock()
        mock_tables = (TableMetadata("dbo", "T", ()),)
        mock_discover.return_value = mock_tables
        mock_filter.return_value = mock_tables
        mock_classify.side_effect = RuntimeError("Classification failed")

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_path=Path("/tmp"),
        )

        with pytest.raises(PipelineError) as exc_info:
            generate_semantic_model(config)

        assert exc_info.value.stage == "classification"
        assert isinstance(exc_info.value.cause, RuntimeError)

    @patch("semantic_model_generator.pipeline.infer_relationships")
    @patch("semantic_model_generator.pipeline.classify_tables")
    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_relationship_error_wraps(
        self,
        mock_connect: MagicMock,
        mock_discover: MagicMock,
        mock_filter: MagicMock,
        mock_classify: MagicMock,
        mock_infer: MagicMock,
    ) -> None:
        """infer_relationships failure -> PipelineError stage=relationships."""
        mock_connect.return_value = MagicMock()
        mock_tables = (TableMetadata("dbo", "T", ()),)
        mock_discover.return_value = mock_tables
        mock_filter.return_value = mock_tables
        mock_classify.return_value = {("dbo", "T"): TableClassification.FACT}
        mock_infer.side_effect = ValueError("Relationship inference failed")

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_path=Path("/tmp"),
        )

        with pytest.raises(PipelineError) as exc_info:
            generate_semantic_model(config)

        assert exc_info.value.stage == "relationships"
        assert isinstance(exc_info.value.cause, ValueError)

    @patch("semantic_model_generator.pipeline.generate_all_tmdl")
    @patch("semantic_model_generator.pipeline.infer_relationships")
    @patch("semantic_model_generator.pipeline.classify_tables")
    @patch("semantic_model_generator.pipeline.filter_tables")
    @patch("semantic_model_generator.pipeline.discover_tables")
    @patch("semantic_model_generator.pipeline.create_fabric_connection")
    def test_tmdl_generation_error_wraps(
        self,
        mock_connect: MagicMock,
        mock_discover: MagicMock,
        mock_filter: MagicMock,
        mock_classify: MagicMock,
        mock_infer: MagicMock,
        mock_generate: MagicMock,
    ) -> None:
        """generate_all_tmdl failure -> PipelineError stage=tmdl_generation."""
        mock_connect.return_value = MagicMock()
        mock_tables = (TableMetadata("dbo", "T", ()),)
        mock_discover.return_value = mock_tables
        mock_filter.return_value = mock_tables
        mock_classify.return_value = {("dbo", "T"): TableClassification.FACT}
        mock_infer.return_value = ()
        mock_generate.side_effect = RuntimeError("TMDL generation failed")

        config = PipelineConfig(
            sql_endpoint="ep",
            database="db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="M",
            catalog_name="cat",
            output_path=Path("/tmp"),
        )

        with pytest.raises(PipelineError) as exc_info:
            generate_semantic_model(config)

        assert exc_info.value.stage == "tmdl_generation"
        assert isinstance(exc_info.value.cause, RuntimeError)
