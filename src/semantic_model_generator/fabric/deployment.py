"""Fabric semantic model deployment module."""

from datetime import UTC, datetime
from typing import Any

import requests

from semantic_model_generator.fabric.auth import get_fabric_token
from semantic_model_generator.fabric.packaging import package_tmdl_for_fabric
from semantic_model_generator.fabric.polling import get_operation_result, poll_operation
from semantic_model_generator.fabric.resolution import is_guid, resolve_workspace_id

FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"


def find_semantic_model_by_name(workspace_id: str, model_name: str, token: str) -> str | None:
    """Find semantic model by name in workspace.

    Args:
        workspace_id: Workspace GUID.
        model_name: Model display name.
        token: Bearer token.

    Returns:
        Model ID if found, None otherwise.
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.get(
        f"{FABRIC_API_BASE}/workspaces/{workspace_id}/semanticModels", headers=headers
    )
    response.raise_for_status()

    models = response.json()["value"]
    matches = [model for model in models if model["displayName"] == model_name]

    if matches:
        return matches[0]["id"]  # type: ignore[no-any-return]
    return None


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
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"displayName": display_name, "definition": definition}
    response = requests.post(
        f"{FABRIC_API_BASE}/workspaces/{workspace_id}/semanticModels", headers=headers, json=payload
    )
    response.raise_for_status()

    if response.status_code == 201:
        model_id: str = response.json()["id"]
        return (model_id, None)
    elif response.status_code == 202:
        operation_id: str | None = response.headers.get("x-ms-operation-id")
        return (None, operation_id)
    else:
        # Should not reach here due to raise_for_status()
        return (None, None)


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
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"definition": definition}
    url = (
        f"{FABRIC_API_BASE}/workspaces/{workspace_id}/"
        f"semanticModels/{semantic_model_id}/updateDefinition?updateMetadata=True"
    )
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    if response.status_code == 200:
        return None
    elif response.status_code == 202:
        operation_id: str | None = response.headers.get("x-ms-operation-id")
        return operation_id
    else:
        return None


def deploy_semantic_model_dev(tmdl_files: dict[str, str], workspace: str, model_name: str) -> str:
    """Deploy semantic model in dev mode (timestamped name).

    Args:
        tmdl_files: TMDL files from generate_all_tmdl().
        workspace: Workspace name or GUID.
        model_name: Base model name (timestamp will be appended).

    Returns:
        Created model ID.
    """
    # Get token
    token = get_fabric_token()

    # Resolve workspace if it's a name
    workspace_id = workspace if is_guid(workspace) else resolve_workspace_id(workspace, token)

    # Generate timestamped name
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    deployment_name = f"{model_name}_{timestamp}"

    # Package TMDL files
    definition = package_tmdl_for_fabric(tmdl_files)

    # Create semantic model
    model_id, op_id = create_semantic_model(workspace_id, deployment_name, definition, token)

    # Handle LRO if needed
    if op_id:
        poll_operation(op_id, token)
        result = get_operation_result(op_id, token)
        model_id = result["id"]

    assert model_id is not None
    return model_id


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
    # Get token
    token = get_fabric_token()

    # Resolve workspace if it's a name
    workspace_id = workspace if is_guid(workspace) else resolve_workspace_id(workspace, token)

    # Check if model exists
    existing_id = find_semantic_model_by_name(workspace_id, model_name, token)

    if existing_id and not confirm_overwrite:
        msg = (
            f"Semantic model '{model_name}' already exists. "
            "Pass confirm_overwrite=True to overwrite."
        )
        raise ValueError(msg)

    # Package TMDL files
    definition = package_tmdl_for_fabric(tmdl_files)

    if existing_id:
        # Update existing model
        op_id = update_semantic_model_definition(workspace_id, existing_id, definition, token)
        if op_id:
            poll_operation(op_id, token)
        return existing_id
    else:
        # Create new model
        model_id, op_id = create_semantic_model(workspace_id, model_name, definition, token)
        if op_id:
            poll_operation(op_id, token)
            result = get_operation_result(op_id, token)
            model_id = result["id"]

        assert model_id is not None
        return model_id
