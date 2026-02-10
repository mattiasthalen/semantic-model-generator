"""Fabric authentication module."""

from azure.identity import DefaultAzureCredential  # noqa: F401


def get_fabric_token() -> str:
    """Acquire bearer token for Fabric REST API."""
    raise NotImplementedError
