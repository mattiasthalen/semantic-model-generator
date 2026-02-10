"""Fabric resource resolution module."""

import requests  # noqa: F401


def is_guid(value: str) -> bool:
    """Check if value is a valid GUID."""
    raise NotImplementedError


def build_direct_lake_url(workspace_id: str, lakehouse_id: str) -> str:
    """Build Direct Lake URL from workspace and lakehouse GUIDs."""
    raise NotImplementedError


def resolve_workspace_id(workspace_name: str, token: str) -> str:
    """Resolve workspace name to GUID."""
    raise NotImplementedError


def resolve_lakehouse_id(
    workspace_id: str, lakehouse_name: str, token: str, item_type: str = "Lakehouse"
) -> str:
    """Resolve lakehouse/warehouse name to GUID."""
    raise NotImplementedError


def resolve_direct_lake_url(
    workspace: str, lakehouse: str, token: str, item_type: str = "Lakehouse"
) -> str:
    """Resolve workspace and lakehouse names/GUIDs to Direct Lake URL."""
    raise NotImplementedError
