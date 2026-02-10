"""Fabric semantic model deployment module."""

from typing import Any

import requests  # noqa: F401

from semantic_model_generator.fabric.auth import get_fabric_token  # noqa: F401
from semantic_model_generator.fabric.packaging import package_tmdl_for_fabric  # noqa: F401
from semantic_model_generator.fabric.polling import (  # noqa: F401
    get_operation_result,
    poll_operation,
)
from semantic_model_generator.fabric.resolution import is_guid  # noqa: F401


def find_semantic_model_by_name(workspace_id: str, model_name: str, token: str) -> str | None:
    """Find semantic model by name in workspace.

    Args:
        workspace_id: Workspace GUID.
        model_name: Model display name.
        token: Bearer token.

    Returns:
        Model ID if found, None otherwise.
    """
    raise NotImplementedError


def create_semantic_model(
    workspace_id: str, display_name: str, definition: dict[str, Any], token: str
) -> tuple[str | None, str | None]:
    """Create semantic model in workspace.

    Args:
        workspace_id: Workspace GUID.
        display_name: Model display name.
        definition: TMDL definition (from package_tmdl_for_fabric).
        token: Bearer token.

    Returns:
        (model_id, operation_id) tuple.
        - 201: (model_id, None)
        - 202: (None, operation_id)
    """
    raise NotImplementedError


def update_semantic_model_definition(
    workspace_id: str, semantic_model_id: str, definition: dict[str, Any], token: str
) -> str | None:
    """Update existing semantic model definition.

    Args:
        workspace_id: Workspace GUID.
        semantic_model_id: Model ID.
        definition: TMDL definition (from package_tmdl_for_fabric).
        token: Bearer token.

    Returns:
        Operation ID if 202 (long-running), None if 200 (immediate).
    """
    raise NotImplementedError


def deploy_semantic_model_dev(tmdl_files: dict[str, str], workspace: str, model_name: str) -> str:
    """Deploy semantic model in dev mode (timestamped name).

    Args:
        tmdl_files: TMDL files from generate_all_tmdl().
        workspace: Workspace name or GUID.
        model_name: Base model name (timestamp will be appended).

    Returns:
        Created model ID.
    """
    raise NotImplementedError


def deploy_semantic_model_prod(
    tmdl_files: dict[str, str], workspace: str, model_name: str, confirm_overwrite: bool = False
) -> str:
    """Deploy semantic model in prod mode (base name, overwrite protection).

    Args:
        tmdl_files: TMDL files from generate_all_tmdl().
        workspace: Workspace name or GUID.
        model_name: Model name (no timestamp).
        confirm_overwrite: If True, overwrite existing model. If False, raise error.

    Returns:
        Model ID (created or updated).

    Raises:
        ValueError: If model exists and confirm_overwrite=False.
    """
    raise NotImplementedError
