"""Fabric resource resolution module."""

import re
from typing import Any

import requests

FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"


def is_guid(value: str) -> bool:
    """Check if value is a valid GUID.

    Args:
        value: String to check.

    Returns:
        True if value is a valid UUID/GUID, False otherwise.
    """
    if not value:
        return False

    # UUID pattern: 8-4-4-4-12 hex digits
    guid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return bool(re.match(guid_pattern, value.lower()))


def _call_fabric_api(endpoint: str, token: str) -> dict[str, Any]:
    """Call Fabric REST API.

    Args:
        endpoint: API endpoint path (without base URL).
        token: Bearer token.

    Returns:
        JSON response as dict.
    """
    url = f"{FABRIC_API_BASE}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]


def build_direct_lake_url(workspace_id: str, lakehouse_id: str) -> str:
    """Build Direct Lake URL from workspace and lakehouse GUIDs.

    Args:
        workspace_id: Workspace GUID.
        lakehouse_id: Lakehouse GUID.

    Returns:
        Direct Lake connection URL.
    """
    return f"https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}"


def resolve_workspace_id(workspace_name: str, token: str) -> str:
    """Resolve workspace name to GUID.

    Args:
        workspace_name: Display name of workspace.
        token: Bearer token.

    Returns:
        Workspace GUID.

    Raises:
        ValueError: If workspace not found or multiple matches found.
    """
    response = _call_fabric_api("workspaces", token)
    workspaces = response["value"]

    matches = [ws for ws in workspaces if ws["displayName"] == workspace_name]

    if len(matches) == 0:
        raise ValueError(f"Workspace not found: {workspace_name}")
    if len(matches) > 1:
        raise ValueError(f"Multiple workspaces found with name: {workspace_name}")

    return matches[0]["id"]  # type: ignore[no-any-return]


def resolve_lakehouse_id(
    workspace_id: str, lakehouse_name: str, token: str, item_type: str = "Lakehouse"
) -> str:
    """Resolve lakehouse/warehouse name to GUID.

    Args:
        workspace_id: Workspace GUID.
        lakehouse_name: Display name of lakehouse/warehouse.
        token: Bearer token.
        item_type: Either "Lakehouse" or "Warehouse".

    Returns:
        Lakehouse/warehouse GUID.

    Raises:
        ValueError: If item not found, multiple matches, or unsupported item_type.
    """
    # Build endpoint based on item type
    if item_type == "Lakehouse":
        endpoint = f"workspaces/{workspace_id}/lakehouses"
    elif item_type == "Warehouse":
        endpoint = f"workspaces/{workspace_id}/warehouses"
    else:
        raise ValueError(f"Unsupported item_type: {item_type}")

    response = _call_fabric_api(endpoint, token)
    items = response["value"]

    matches = [item for item in items if item["displayName"] == lakehouse_name]

    if len(matches) == 0:
        raise ValueError(f"{item_type} not found: {lakehouse_name}")
    if len(matches) > 1:
        raise ValueError(f"Multiple {item_type}s found with name: {lakehouse_name}")

    return matches[0]["id"]  # type: ignore[no-any-return]


def resolve_direct_lake_url(
    workspace: str, lakehouse: str, token: str, item_type: str = "Lakehouse"
) -> str:
    """Resolve workspace and lakehouse names/GUIDs to Direct Lake URL.

    Accepts either names or GUIDs. GUIDs are passed through without API calls.

    Args:
        workspace: Workspace name or GUID.
        lakehouse: Lakehouse/warehouse name or GUID.
        token: Bearer token.
        item_type: Either "Lakehouse" or "Warehouse".

    Returns:
        Direct Lake connection URL.
    """
    # Resolve workspace if it's a name
    workspace_id = workspace if is_guid(workspace) else resolve_workspace_id(workspace, token)

    # Resolve lakehouse if it's a name
    lakehouse_id = (
        lakehouse
        if is_guid(lakehouse)
        else resolve_lakehouse_id(workspace_id, lakehouse, token, item_type)
    )

    return build_direct_lake_url(workspace_id, lakehouse_id)
