"""Tests for Fabric resource resolution module."""

from unittest.mock import MagicMock, patch

import pytest

from semantic_model_generator.fabric.resolution import (
    build_direct_lake_url,
    is_guid,
    resolve_direct_lake_url,
    resolve_lakehouse_id,
    resolve_workspace_id,
)


# is_guid tests (pure, no mocks)
def test_is_guid_valid_lowercase() -> None:
    """Test is_guid with valid lowercase GUID."""
    guid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    assert is_guid(guid) is True


def test_is_guid_valid_uppercase() -> None:
    """Test is_guid with valid uppercase GUID."""
    guid = "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"
    assert is_guid(guid) is True


def test_is_guid_invalid_short() -> None:
    """Test is_guid with invalid short string."""
    assert is_guid("not-a-guid") is False


def test_is_guid_invalid_format() -> None:
    """Test is_guid with GUID missing dashes."""
    guid_no_dashes = "a1b2c3d4e5f67890abcdef1234567890"
    assert is_guid(guid_no_dashes) is False


def test_is_guid_empty() -> None:
    """Test is_guid with empty string."""
    assert is_guid("") is False


# build_direct_lake_url tests (pure, no mocks)
def test_build_direct_lake_url() -> None:
    """Test build_direct_lake_url constructs correct URL."""
    workspace_id = "workspace-guid-123"
    lakehouse_id = "lakehouse-guid-456"
    expected = f"https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{lakehouse_id}"

    result = build_direct_lake_url(workspace_id, lakehouse_id)

    assert result == expected


# resolve_workspace_id tests (mock requests.get)
def test_resolve_workspace_id_found() -> None:
    """Test resolve_workspace_id with matching workspace."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "value": [
            {"id": "workspace-guid-1", "displayName": "Test Workspace"},
            {"id": "workspace-guid-2", "displayName": "Other Workspace"},
        ]
    }

    with patch("semantic_model_generator.fabric.resolution.requests.get") as mock_get:
        mock_get.return_value = mock_response

        result = resolve_workspace_id("Test Workspace", "bearer-token")

        assert result == "workspace-guid-1"


def test_resolve_workspace_id_not_found() -> None:
    """Test resolve_workspace_id raises ValueError when workspace not found."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"value": []}

    with patch("semantic_model_generator.fabric.resolution.requests.get") as mock_get:
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Missing Workspace"):
            resolve_workspace_id("Missing Workspace", "bearer-token")


def test_resolve_workspace_id_multiple_matches() -> None:
    """Test resolve_workspace_id raises ValueError with multiple matches."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "value": [
            {"id": "workspace-guid-1", "displayName": "Duplicate"},
            {"id": "workspace-guid-2", "displayName": "Duplicate"},
        ]
    }

    with patch("semantic_model_generator.fabric.resolution.requests.get") as mock_get:
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Multiple.*Duplicate"):
            resolve_workspace_id("Duplicate", "bearer-token")


def test_resolve_workspace_id_uses_bearer_token() -> None:
    """Test resolve_workspace_id includes Bearer token in Authorization header."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "value": [{"id": "workspace-guid", "displayName": "Workspace"}]
    }

    with patch("semantic_model_generator.fabric.resolution.requests.get") as mock_get:
        mock_get.return_value = mock_response

        resolve_workspace_id("Workspace", "test-token-123")

        # Verify the Authorization header contains Bearer token
        call_args = mock_get.call_args
        headers = call_args.kwargs.get("headers", {})
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-token-123"


# resolve_lakehouse_id tests (mock requests.get)
def test_resolve_lakehouse_id_found() -> None:
    """Test resolve_lakehouse_id with matching lakehouse."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "value": [
            {"id": "lakehouse-guid-1", "displayName": "Test Lakehouse"},
            {"id": "lakehouse-guid-2", "displayName": "Other Lakehouse"},
        ]
    }

    with patch("semantic_model_generator.fabric.resolution.requests.get") as mock_get:
        mock_get.return_value = mock_response

        result = resolve_lakehouse_id(
            "workspace-guid", "Test Lakehouse", "bearer-token", "Lakehouse"
        )

        assert result == "lakehouse-guid-1"


def test_resolve_lakehouse_id_not_found() -> None:
    """Test resolve_lakehouse_id raises ValueError when lakehouse not found."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"value": []}

    with patch("semantic_model_generator.fabric.resolution.requests.get") as mock_get:
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Missing Lakehouse"):
            resolve_lakehouse_id("workspace-guid", "Missing Lakehouse", "bearer-token", "Lakehouse")


def test_resolve_lakehouse_id_warehouse_type() -> None:
    """Test resolve_lakehouse_id uses /warehouses endpoint for Warehouse type."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "value": [{"id": "warehouse-guid", "displayName": "Test Warehouse"}]
    }

    with patch("semantic_model_generator.fabric.resolution.requests.get") as mock_get:
        mock_get.return_value = mock_response

        resolve_lakehouse_id("workspace-guid", "Test Warehouse", "bearer-token", "Warehouse")

        # Verify endpoint contains /warehouses
        call_args = mock_get.call_args
        url = call_args.args[0]
        assert "/warehouses" in url


def test_resolve_lakehouse_id_lakehouse_type() -> None:
    """Test resolve_lakehouse_id uses /lakehouses endpoint for Lakehouse type."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "value": [{"id": "lakehouse-guid", "displayName": "Test Lakehouse"}]
    }

    with patch("semantic_model_generator.fabric.resolution.requests.get") as mock_get:
        mock_get.return_value = mock_response

        resolve_lakehouse_id("workspace-guid", "Test Lakehouse", "bearer-token", "Lakehouse")

        # Verify endpoint contains /lakehouses
        call_args = mock_get.call_args
        url = call_args.args[0]
        assert "/lakehouses" in url


# resolve_direct_lake_url tests (mock resolution functions)
def test_resolve_direct_lake_url_with_names() -> None:
    """Test resolve_direct_lake_url resolves both workspace and lakehouse names."""
    with (
        patch("semantic_model_generator.fabric.resolution.is_guid") as mock_is_guid,
        patch("semantic_model_generator.fabric.resolution.resolve_workspace_id") as mock_resolve_ws,
        patch("semantic_model_generator.fabric.resolution.resolve_lakehouse_id") as mock_resolve_lh,
        patch("semantic_model_generator.fabric.resolution.build_direct_lake_url") as mock_build_url,
    ):
        mock_is_guid.side_effect = [False, False]  # Both are names
        mock_resolve_ws.return_value = "workspace-guid"
        mock_resolve_lh.return_value = "lakehouse-guid"
        mock_build_url.return_value = "https://onelake.dfs.fabric.microsoft.com/w/l"

        result = resolve_direct_lake_url("Workspace Name", "Lakehouse Name", "token")

        mock_resolve_ws.assert_called_once_with("Workspace Name", "token")
        mock_resolve_lh.assert_called_once_with(
            "workspace-guid", "Lakehouse Name", "token", "Lakehouse"
        )
        mock_build_url.assert_called_once_with("workspace-guid", "lakehouse-guid")
        assert result == "https://onelake.dfs.fabric.microsoft.com/w/l"


def test_resolve_direct_lake_url_with_guids() -> None:
    """Test resolve_direct_lake_url with GUIDs skips resolution."""
    with (
        patch("semantic_model_generator.fabric.resolution.is_guid") as mock_is_guid,
        patch("semantic_model_generator.fabric.resolution.resolve_workspace_id") as mock_resolve_ws,
        patch("semantic_model_generator.fabric.resolution.resolve_lakehouse_id") as mock_resolve_lh,
        patch("semantic_model_generator.fabric.resolution.build_direct_lake_url") as mock_build_url,
    ):
        mock_is_guid.side_effect = [True, True]  # Both are GUIDs
        mock_build_url.return_value = "https://onelake.dfs.fabric.microsoft.com/w/l"

        workspace_guid = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        lakehouse_guid = "b1b2c3d4-e5f6-7890-abcd-ef1234567890"

        result = resolve_direct_lake_url(workspace_guid, lakehouse_guid, "token")

        # No resolution calls should be made
        mock_resolve_ws.assert_not_called()
        mock_resolve_lh.assert_not_called()
        mock_build_url.assert_called_once_with(workspace_guid, lakehouse_guid)
        assert result == "https://onelake.dfs.fabric.microsoft.com/w/l"


def test_resolve_direct_lake_url_mixed() -> None:
    """Test resolve_direct_lake_url with workspace name and lakehouse GUID."""
    with (
        patch("semantic_model_generator.fabric.resolution.is_guid") as mock_is_guid,
        patch("semantic_model_generator.fabric.resolution.resolve_workspace_id") as mock_resolve_ws,
        patch("semantic_model_generator.fabric.resolution.resolve_lakehouse_id") as mock_resolve_lh,
        patch("semantic_model_generator.fabric.resolution.build_direct_lake_url") as mock_build_url,
    ):
        mock_is_guid.side_effect = [False, True]  # Workspace is name, lakehouse is GUID
        mock_resolve_ws.return_value = "workspace-guid"
        mock_build_url.return_value = "https://onelake.dfs.fabric.microsoft.com/w/l"

        lakehouse_guid = "b1b2c3d4-e5f6-7890-abcd-ef1234567890"

        result = resolve_direct_lake_url("Workspace Name", lakehouse_guid, "token")

        mock_resolve_ws.assert_called_once_with("Workspace Name", "token")
        mock_resolve_lh.assert_not_called()  # Lakehouse is already GUID
        mock_build_url.assert_called_once_with("workspace-guid", lakehouse_guid)
        assert result == "https://onelake.dfs.fabric.microsoft.com/w/l"
