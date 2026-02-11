"""Pipeline orchestration module for semantic model generation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from semantic_model_generator.fabric import (
    deploy_semantic_model_dev,
    deploy_semantic_model_prod,
    resolve_direct_lake_url,
)
from semantic_model_generator.fabric.auth import get_fabric_token
from semantic_model_generator.output import write_tmdl_folder
from semantic_model_generator.schema import (
    classify_tables,
    create_fabric_connection,
    discover_tables,
    filter_tables,
    infer_relationships,
)
from semantic_model_generator.tmdl import generate_all_tmdl


class PipelineError(Exception):
    """Exception raised when a pipeline stage fails.

    Attributes:
        stage: Name of the pipeline stage that failed.
        message: Error message.
        cause: Original exception that caused the failure.
    """

    def __init__(self, stage: str, message: str, cause: Exception | None = None) -> None:
        """Initialize PipelineError.

        Args:
            stage: Name of the pipeline stage.
            message: Error message.
            cause: Original exception.
        """
        super().__init__(f"[{stage}] {message}")
        self.stage = stage
        self.message = message
        self.cause = cause


@dataclass(frozen=True, slots=True, kw_only=True)
class PipelineConfig:
    """Configuration for semantic model generation pipeline.

    All required parameters must be provided at construction time.
    Configuration is validated in __post_init__ and frozen thereafter.
    """

    # Connection parameters
    sql_endpoint: str
    database: str

    # Schema discovery
    schemas: tuple[str, ...]
    key_prefixes: tuple[str, ...]

    # Model metadata
    model_name: str
    catalog_name: str

    # Filtering (optional)
    include_tables: tuple[str, ...] | None = None
    exclude_tables: tuple[str, ...] | None = None

    # Output configuration
    output_mode: str = "folder"
    output_path: str | Path | None = None

    # Fabric deployment (required for output_mode="fabric")
    workspace: str | None = None
    lakehouse_or_warehouse: str | None = None
    item_type: str = "Lakehouse"

    # Mode flags
    dev_mode: bool = True
    overwrite: bool = False
    confirm_overwrite: bool = False

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        # Convert output_path string to Path (frozen dataclass needs object.__setattr__)
        if self.output_path is not None and not isinstance(self.output_path, Path):
            object.__setattr__(self, "output_path", Path(self.output_path))

        # Validate schemas
        if len(self.schemas) == 0:
            raise ValueError("schemas cannot be empty; at least one schema required")

        # Validate key_prefixes
        if len(self.key_prefixes) == 0:
            raise ValueError("key_prefixes cannot be empty; provide prefixes like ('SK_', 'ID_')")

        # Validate output_mode
        if self.output_mode not in ("folder", "fabric"):
            raise ValueError(f"output_mode must be 'folder' or 'fabric', got {self.output_mode}")

        # Validate item_type
        if self.item_type not in ("Lakehouse", "Warehouse"):
            raise ValueError(f"item_type must be 'Lakehouse' or 'Warehouse', got {self.item_type}")

        # Validate folder mode requirements
        if self.output_mode == "folder" and self.output_path is None:
            raise ValueError("output_path required when output_mode='folder'")

        # Validate fabric mode requirements
        if self.output_mode == "fabric":
            if self.workspace is None:
                raise ValueError("workspace required when output_mode='fabric'")
            if self.lakehouse_or_warehouse is None:
                raise ValueError("lakehouse_or_warehouse required when output_mode='fabric'")


def generate_semantic_model(config: PipelineConfig) -> dict[str, Any]:
    """Generate semantic model from configuration.

    Orchestrates the entire pipeline:
    1. Connect to Fabric SQL endpoint
    2. Discover tables in specified schemas
    3. Filter tables by include/exclude patterns
    4. Classify tables as dimension/fact
    5. Infer star-schema relationships
    6. Generate TMDL files
    7. Output to folder or deploy to Fabric

    Args:
        config: Pipeline configuration.

    Returns:
        Result dict with mode-specific keys:
        - folder mode: {"mode": "folder", "output_path": Path, "summary": WriteSummary}
        - fabric mode: {"mode": "fabric", "model_id": str, "model_name": str}

    Raises:
        PipelineError: When any pipeline stage fails.
    """
    # Stage 1: Connection
    try:
        conn = create_fabric_connection(config.sql_endpoint, config.database)
    except Exception as e:
        raise PipelineError(
            "connection", f"Failed to connect to {config.sql_endpoint}: {e}", e
        ) from e

    # Stage 2: Discovery
    try:
        tables = discover_tables(conn, config.schemas)
    except Exception as e:
        raise PipelineError(
            "discovery", f"Failed to read schema for {config.schemas}: {e}", e
        ) from e

    # Stage 3: Filtering
    try:
        filtered = filter_tables(tables, config.include_tables, config.exclude_tables)
    except Exception as e:
        raise PipelineError("filtering", f"Failed to filter tables: {e}", e) from e

    # Stage 4: Classification
    try:
        classifications = classify_tables(filtered, config.key_prefixes)
    except Exception as e:
        raise PipelineError("classification", f"Failed to classify tables: {e}", e) from e

    # Stage 5: Relationship inference
    try:
        relationships = infer_relationships(filtered, classifications, config.key_prefixes)
    except Exception as e:
        raise PipelineError("relationships", f"Failed to infer relationships: {e}", e) from e

    # Stage 5.5: Resolve Direct Lake URL (fabric mode only)
    direct_lake_url = ""
    if config.output_mode == "fabric":
        try:
            assert config.workspace is not None
            assert config.lakehouse_or_warehouse is not None
            token = get_fabric_token()
            direct_lake_url = resolve_direct_lake_url(
                config.workspace, config.lakehouse_or_warehouse, token, config.item_type
            )
        except Exception as e:
            raise PipelineError("resolution", f"Failed to resolve Direct Lake URL: {e}", e) from e

    # Stage 6: TMDL generation
    try:
        tmdl_files = generate_all_tmdl(
            config.model_name,
            filtered,
            classifications,
            relationships,
            config.key_prefixes,
            config.catalog_name,
            direct_lake_url,
        )
    except Exception as e:
        raise PipelineError("tmdl_generation", f"Failed to generate TMDL: {e}", e) from e

    # Stage 7: Output - branch on output_mode
    if config.output_mode == "folder":
        # Folder mode
        try:
            assert config.output_path is not None  # Validated in __post_init__
            # After __post_init__, output_path is guaranteed to be Path (strings converted)
            output_path = cast(Path, config.output_path)
            summary = write_tmdl_folder(
                tmdl_files,
                output_path,
                config.model_name,
                config.dev_mode,
                config.overwrite,
            )
            return {
                "mode": "folder",
                "output_path": summary.output_path,
                "summary": summary,
            }
        except Exception as e:
            raise PipelineError(
                "output", f"Failed to write folder at {config.output_path}: {e}", e
            ) from e
    else:
        # Fabric mode
        try:
            assert config.workspace is not None  # Validated in __post_init__
            if config.dev_mode:
                model_id = deploy_semantic_model_dev(
                    tmdl_files, config.workspace, config.model_name
                )
            else:
                model_id = deploy_semantic_model_prod(
                    tmdl_files,
                    config.workspace,
                    config.model_name,
                    config.confirm_overwrite,
                )
            return {"mode": "fabric", "model_id": model_id, "model_name": config.model_name}
        except Exception as e:
            raise PipelineError(
                "deployment", f"Failed to deploy to workspace {config.workspace}: {e}", e
            ) from e
