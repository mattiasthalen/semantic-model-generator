"""Pipeline orchestration module for semantic model generation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Stub imports for pipeline functions (will be implemented in GREEN phase)
from semantic_model_generator.fabric import (  # noqa: F401
    deploy_semantic_model_dev,
    deploy_semantic_model_prod,
)
from semantic_model_generator.output import write_tmdl_folder  # noqa: F401
from semantic_model_generator.schema import (  # noqa: F401
    classify_tables,
    create_fabric_connection,
    discover_tables,
    filter_tables,
    infer_relationships,
)
from semantic_model_generator.tmdl import generate_all_tmdl  # noqa: F401


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
    output_path: Path | None = None

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
        raise NotImplementedError


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
    raise NotImplementedError
