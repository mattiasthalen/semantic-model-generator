"""Fabric long-running operation polling module."""

from typing import Any

import requests
from tenacity import retry, retry_if_result, stop_after_attempt, wait_exponential

FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"


def _is_still_running(result: dict[str, Any]) -> bool:
    """Check if operation is still running (for tenacity retry)."""
    return result.get("status") == "Running"


@retry(
    retry=retry_if_result(_is_still_running),
    stop=stop_after_attempt(60),
    wait=wait_exponential(multiplier=1, min=2, max=30),
)
def poll_operation(operation_id: str, token: str) -> dict[str, Any]:
    """Poll long-running operation until completion.

    Args:
        operation_id: Operation ID from x-ms-operation-id response header.
        token: Bearer token.

    Returns:
        Operation dict with "status" key ("Succeeded" or "Failed").

    Raises:
        RuntimeError: If operation status is "Failed", with error details.
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.get(f"{FABRIC_API_BASE}/operations/{operation_id}", headers=headers)
    response.raise_for_status()

    operation = response.json()
    status = operation.get("status")

    if status == "Failed":
        error = operation.get("error", {})
        error_code = error.get("errorCode", "Unknown")
        error_msg = error.get("message", "No details")
        raise RuntimeError(f"Operation {operation_id} failed: [{error_code}] {error_msg}")

    return operation  # type: ignore[no-any-return]


def get_operation_result(operation_id: str, token: str) -> dict[str, Any]:
    """Get result of a completed operation.

    Args:
        operation_id: Operation ID.
        token: Bearer token.

    Returns:
        Result dict (e.g., created semantic model object).
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.get(f"{FABRIC_API_BASE}/operations/{operation_id}/result", headers=headers)
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]
