"""Tests for Fabric long-running operation polling."""

from unittest.mock import Mock, patch

import pytest

from semantic_model_generator.fabric.polling import get_operation_result, poll_operation


class TestPollOperation:
    """Tests for poll_operation function."""

    @patch("semantic_model_generator.fabric.polling.requests.get")
    def test_poll_operation_succeeds_immediately(self, mock_get: Mock) -> None:
        """Test operation succeeds on first call."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "Succeeded", "id": "op-123"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = poll_operation("op-123", "test-token")

        assert result["status"] == "Succeeded"
        assert result["id"] == "op-123"
        mock_get.assert_called_once()

    @patch("semantic_model_generator.fabric.polling.requests.get")
    def test_poll_operation_polls_until_success(self, mock_get: Mock) -> None:
        """Test operation polls multiple times until success."""
        # Return "Running" twice, then "Succeeded"
        mock_response_running_1 = Mock()
        mock_response_running_1.json.return_value = {"status": "Running"}
        mock_response_running_1.raise_for_status = Mock()

        mock_response_running_2 = Mock()
        mock_response_running_2.json.return_value = {"status": "Running"}
        mock_response_running_2.raise_for_status = Mock()

        mock_response_succeeded = Mock()
        mock_response_succeeded.json.return_value = {"status": "Succeeded", "id": "op-456"}
        mock_response_succeeded.raise_for_status = Mock()

        mock_get.side_effect = [
            mock_response_running_1,
            mock_response_running_2,
            mock_response_succeeded,
        ]

        result = poll_operation("op-456", "test-token")

        assert result["status"] == "Succeeded"
        assert mock_get.call_count == 3

    @patch("semantic_model_generator.fabric.polling.requests.get")
    def test_poll_operation_raises_on_failure(self, mock_get: Mock) -> None:
        """Test operation raises RuntimeError when status is Failed."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "Failed",
            "error": {"errorCode": "TestError", "message": "Something failed"},
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        expected_msg = "Operation op-789 failed.*TestError.*Something failed"
        with pytest.raises(RuntimeError, match=expected_msg):
            poll_operation("op-789", "test-token")

    @patch("semantic_model_generator.fabric.polling.requests.get")
    def test_poll_operation_uses_correct_endpoint(self, mock_get: Mock) -> None:
        """Test operation uses correct API endpoint."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "Succeeded"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        poll_operation("op-abc", "test-token")

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://api.fabric.microsoft.com/v1/operations/op-abc"

    @patch("semantic_model_generator.fabric.polling.requests.get")
    def test_poll_operation_uses_bearer_token(self, mock_get: Mock) -> None:
        """Test operation uses Authorization header with bearer token."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "Succeeded"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        poll_operation("op-def", "my-token-123")

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer my-token-123"


class TestGetOperationResult:
    """Tests for get_operation_result function."""

    @patch("semantic_model_generator.fabric.polling.requests.get")
    def test_get_operation_result_returns_json(self, mock_get: Mock) -> None:
        """Test returns operation result JSON."""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "model-123", "displayName": "Test Model"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_operation_result("op-result-1", "test-token")

        assert result["id"] == "model-123"
        assert result["displayName"] == "Test Model"

    @patch("semantic_model_generator.fabric.polling.requests.get")
    def test_get_operation_result_uses_correct_endpoint(self, mock_get: Mock) -> None:
        """Test uses correct API endpoint for operation result."""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "model-456"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        get_operation_result("op-result-2", "test-token")

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert (
            call_args[0][0] == "https://api.fabric.microsoft.com/v1/operations/op-result-2/result"
        )
