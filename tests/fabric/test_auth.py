"""Tests for Fabric authentication module."""

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
