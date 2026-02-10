"""Tests for Fabric authentication module."""

import sys
from unittest.mock import MagicMock, patch

from semantic_model_generator.fabric.auth import get_fabric_token


def test_get_fabric_token_returns_string() -> None:
    """Test that get_fabric_token returns a bearer token string."""
    mock_token = MagicMock()
    mock_token.token = "test-bearer-token-123"

    mock_credential = MagicMock()
    mock_credential.get_token.return_value = mock_token

    with patch("semantic_model_generator.fabric.auth.DefaultAzureCredential") as mock_cred_class:
        mock_cred_class.return_value = mock_credential

        result = get_fabric_token()

        assert result == "test-bearer-token-123"
        assert isinstance(result, str)


def test_get_fabric_token_uses_correct_scope() -> None:
    """Test that get_fabric_token uses the Fabric API scope."""
    mock_token = MagicMock()
    mock_token.token = "token"

    mock_credential = MagicMock()
    mock_credential.get_token.return_value = mock_token

    with patch("semantic_model_generator.fabric.auth.DefaultAzureCredential") as mock_cred_class:
        mock_cred_class.return_value = mock_credential

        get_fabric_token()

        mock_credential.get_token.assert_called_once_with(
            "https://api.fabric.microsoft.com/.default"
        )


def test_get_fabric_token_creates_credential() -> None:
    """Test that get_fabric_token instantiates DefaultAzureCredential."""
    mock_token = MagicMock()
    mock_token.token = "token"

    mock_credential = MagicMock()
    mock_credential.get_token.return_value = mock_token

    with patch("semantic_model_generator.fabric.auth.DefaultAzureCredential") as mock_cred_class:
        mock_cred_class.return_value = mock_credential

        get_fabric_token()

        mock_cred_class.assert_called_once()


def test_get_fabric_token_in_notebook() -> None:
    """Test that get_fabric_token uses notebookutils when in Fabric notebook."""
    mock_notebookutils = MagicMock()
    mock_notebookutils.credentials.getToken.return_value = "notebook-token-456"

    with (
        patch.dict(sys.modules, {"notebookutils": mock_notebookutils}),
        patch("semantic_model_generator.fabric.auth.DefaultAzureCredential") as mock_cred_class,
    ):
        result = get_fabric_token()

        assert result == "notebook-token-456"
        mock_notebookutils.credentials.getToken.assert_called_once_with(
            "https://api.fabric.microsoft.com"
        )
        # Should NOT use DefaultAzureCredential in notebook
        mock_cred_class.assert_not_called()


def test_get_fabric_token_outside_notebook() -> None:
    """Test that get_fabric_token uses DefaultAzureCredential when not in notebook."""
    mock_token = MagicMock()
    mock_token.token = "azure-credential-token"

    mock_credential = MagicMock()
    mock_credential.get_token.return_value = mock_token

    # Ensure notebookutils is NOT in sys.modules
    original_modules = sys.modules.copy()
    if "notebookutils" in sys.modules:
        del sys.modules["notebookutils"]

    try:
        with patch(
            "semantic_model_generator.fabric.auth.DefaultAzureCredential"
        ) as mock_cred_class:
            mock_cred_class.return_value = mock_credential

            result = get_fabric_token()

            assert result == "azure-credential-token"
            mock_cred_class.assert_called_once()
            mock_credential.get_token.assert_called_once_with(
                "https://api.fabric.microsoft.com/.default"
            )
    finally:
        # Restore original sys.modules
        sys.modules.clear()
        sys.modules.update(original_modules)
