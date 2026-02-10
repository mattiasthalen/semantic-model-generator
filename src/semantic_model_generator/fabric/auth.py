"""Fabric authentication module."""

from azure.identity import DefaultAzureCredential

FABRIC_API_SCOPE = "https://api.fabric.microsoft.com/.default"


def get_fabric_token() -> str:
    """Acquire bearer token for Fabric REST API.

    Uses DefaultAzureCredential which supports multiple credential sources
    (managed identity, CLI, environment variables, etc.).

    Returns:
        Bearer token string (not including 'Bearer ' prefix).
    """
    credential = DefaultAzureCredential()
    token = credential.get_token(FABRIC_API_SCOPE)
    return token.token
