"""Fabric authentication module."""

import sys

from azure.identity import DefaultAzureCredential

FABRIC_API_SCOPE = "https://api.fabric.microsoft.com/.default"
FABRIC_API_RESOURCE = "https://api.fabric.microsoft.com"


def _is_fabric_notebook() -> bool:
    """Detect if running in Fabric notebook environment.

    Returns:
        True if notebookutils module is available (Fabric notebook), False otherwise.
    """
    return "notebookutils" in sys.modules


def get_fabric_token() -> str:
    """Acquire bearer token for Fabric REST API.

    In Fabric notebook environment, uses notebookutils.credentials.getToken().
    Otherwise, uses DefaultAzureCredential which supports multiple credential sources
    (managed identity, CLI, environment variables, etc.).

    Returns:
        Bearer token string (not including 'Bearer ' prefix).
    """
    if _is_fabric_notebook():
        # Import notebookutils (only available in Fabric notebooks)
        import notebookutils  # type: ignore  # noqa: PGH003

        return notebookutils.credentials.getToken(FABRIC_API_RESOURCE)
    else:
        credential = DefaultAzureCredential()
        token = credential.get_token(FABRIC_API_SCOPE)
        return token.token
