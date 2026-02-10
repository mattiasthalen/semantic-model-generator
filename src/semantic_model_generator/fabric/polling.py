"""Fabric long-running operation polling module."""

from typing import Any

import requests  # noqa: F401


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
    raise NotImplementedError


def get_operation_result(operation_id: str, token: str) -> dict[str, Any]:
    """Get result of a completed operation.

    Args:
        operation_id: Operation ID.
        token: Bearer token.

    Returns:
        Result dict (e.g., created semantic model object).
    """
    raise NotImplementedError
