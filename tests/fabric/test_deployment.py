"""Tests for Fabric semantic model deployment."""

from datetime import UTC
from unittest.mock import Mock, patch

import pytest

from semantic_model_generator.fabric.deployment import (
    create_semantic_model,
    deploy_semantic_model_dev,
    deploy_semantic_model_prod,
    find_semantic_model_by_name,
    update_semantic_model_definition,
)


class TestFindSemanticModelByName:
    """Tests for find_semantic_model_by_name function."""

    @patch("semantic_model_generator.fabric.deployment.requests.get")
    def test_find_existing_model(self, mock_get: Mock) -> None:
        """Test finding existing model returns ID."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "value": [
                {"id": "model-111", "displayName": "Other Model"},
                {"id": "model-222", "displayName": "Test Model"},
                {"id": "model-333", "displayName": "Another Model"},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = find_semantic_model_by_name("ws-123", "Test Model", "test-token")

        assert result == "model-222"

    @patch("semantic_model_generator.fabric.deployment.requests.get")
    def test_find_nonexistent_model(self, mock_get: Mock) -> None:
        """Test finding nonexistent model returns None."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "value": [
                {"id": "model-111", "displayName": "Other Model"},
                {"id": "model-333", "displayName": "Another Model"},
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = find_semantic_model_by_name("ws-123", "Nonexistent Model", "test-token")

        assert result is None

    @patch("semantic_model_generator.fabric.deployment.requests.get")
    def test_find_model_uses_correct_endpoint(self, mock_get: Mock) -> None:
        """Test uses correct API endpoint."""
        mock_response = Mock()
        mock_response.json.return_value = {"value": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        find_semantic_model_by_name("ws-456", "Test Model", "test-token")

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert (
            call_args[0][0]
            == "https://api.fabric.microsoft.com/v1/workspaces/ws-456/semanticModels"
        )


class TestCreateSemanticModel:
    """Tests for create_semantic_model function."""

    @patch("semantic_model_generator.fabric.deployment.requests.post")
    def test_create_returns_id_on_201(self, mock_post: Mock) -> None:
        """Test create returns model ID on 201 response."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "model-123", "displayName": "Test Model"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        model_id, op_id = create_semantic_model("ws-123", "Test Model", {"parts": []}, "test-token")

        assert model_id == "model-123"
        assert op_id is None

    @patch("semantic_model_generator.fabric.deployment.requests.post")
    def test_create_returns_operation_id_on_202(self, mock_post: Mock) -> None:
        """Test create returns operation ID on 202 response."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"x-ms-operation-id": "op-456"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        model_id, op_id = create_semantic_model("ws-123", "Test Model", {"parts": []}, "test-token")

        assert model_id is None
        assert op_id == "op-456"

    @patch("semantic_model_generator.fabric.deployment.requests.post")
    def test_create_sends_correct_payload(self, mock_post: Mock) -> None:
        """Test create sends correct JSON payload."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "model-789"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        definition = {"parts": [{"path": "model.tmdl", "payload": "base64data"}]}
        create_semantic_model("ws-123", "Test Model", definition, "test-token")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        json_payload = call_args[1]["json"]
        assert json_payload["displayName"] == "Test Model"
        assert json_payload["definition"] == definition

    @patch("semantic_model_generator.fabric.deployment.requests.post")
    def test_create_uses_correct_endpoint(self, mock_post: Mock) -> None:
        """Test create uses correct API endpoint."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "model-999"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        create_semantic_model("ws-abc", "Test Model", {"parts": []}, "test-token")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert (
            call_args[0][0]
            == "https://api.fabric.microsoft.com/v1/workspaces/ws-abc/semanticModels"
        )


class TestUpdateSemanticModelDefinition:
    """Tests for update_semantic_model_definition function."""

    @patch("semantic_model_generator.fabric.deployment.requests.post")
    def test_update_returns_none_on_200(self, mock_post: Mock) -> None:
        """Test update returns None on 200 response (immediate)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = update_semantic_model_definition(
            "ws-123", "model-123", {"parts": []}, "test-token"
        )

        assert result is None

    @patch("semantic_model_generator.fabric.deployment.requests.post")
    def test_update_returns_operation_id_on_202(self, mock_post: Mock) -> None:
        """Test update returns operation ID on 202 response."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"x-ms-operation-id": "op-update-1"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = update_semantic_model_definition(
            "ws-123", "model-123", {"parts": []}, "test-token"
        )

        assert result == "op-update-1"

    @patch("semantic_model_generator.fabric.deployment.requests.post")
    def test_update_uses_correct_endpoint(self, mock_post: Mock) -> None:
        """Test update uses correct API endpoint with updateMetadata parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        update_semantic_model_definition("ws-def", "model-456", {"parts": []}, "test-token")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        expected_url = (
            "https://api.fabric.microsoft.com/v1/workspaces/ws-def/"
            "semanticModels/model-456/updateDefinition?updateMetadata=True"
        )
        assert call_args[0][0] == expected_url

    @patch("semantic_model_generator.fabric.deployment.requests.post")
    def test_update_sends_definition_payload(self, mock_post: Mock) -> None:
        """Test update sends definition in payload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        definition = {"parts": [{"path": "model.tmdl", "payload": "updated-data"}]}
        update_semantic_model_definition("ws-123", "model-123", definition, "test-token")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        json_payload = call_args[1]["json"]
        assert json_payload["definition"] == definition


class TestDeploySemanticModelDev:
    """Tests for deploy_semantic_model_dev function."""

    @patch("semantic_model_generator.fabric.deployment.datetime")
    @patch("semantic_model_generator.fabric.deployment.get_fabric_token")
    @patch("semantic_model_generator.fabric.deployment.resolve_workspace_id")
    @patch("semantic_model_generator.fabric.deployment.package_tmdl_for_fabric")
    @patch("semantic_model_generator.fabric.deployment.create_semantic_model")
    def test_dev_deploy_creates_model_with_timestamp_name(
        self,
        mock_create: Mock,
        mock_package: Mock,
        mock_resolve_ws: Mock,
        mock_get_token: Mock,
        mock_datetime: Mock,
    ) -> None:
        """Test dev deploy appends UTC timestamp to model name."""
        # Mock datetime to return fixed time
        mock_now = Mock()
        mock_now.strftime.return_value = "20260210T123456Z"
        mock_datetime.now.return_value = mock_now
        mock_datetime.UTC = UTC

        mock_get_token.return_value = "test-token"
        mock_resolve_ws.return_value = "ws-123"
        mock_package.return_value = {"parts": []}
        mock_create.return_value = ("model-123", None)

        result = deploy_semantic_model_dev({"model.tmdl": "content"}, "Test Workspace", "MyModel")

        # Verify create was called with timestamped name
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[0][1] == "MyModel_20260210T123456Z"
        assert result == "model-123"

    @patch("semantic_model_generator.fabric.deployment.datetime")
    @patch("semantic_model_generator.fabric.deployment.get_fabric_token")
    @patch("semantic_model_generator.fabric.deployment.is_guid")
    @patch("semantic_model_generator.fabric.deployment.resolve_workspace_id")
    @patch("semantic_model_generator.fabric.deployment.package_tmdl_for_fabric")
    @patch("semantic_model_generator.fabric.deployment.create_semantic_model")
    def test_dev_deploy_resolves_workspace_name(
        self,
        mock_create: Mock,
        mock_package: Mock,
        mock_resolve_ws: Mock,
        mock_is_guid: Mock,
        mock_get_token: Mock,
        mock_datetime: Mock,
    ) -> None:
        """Test dev deploy resolves workspace name to ID."""
        mock_now = Mock()
        mock_now.strftime.return_value = "20260210T000000Z"
        mock_datetime.now.return_value = mock_now
        mock_datetime.UTC = UTC

        mock_get_token.return_value = "test-token"
        mock_is_guid.return_value = False
        mock_resolve_ws.return_value = "ws-resolved-123"
        mock_package.return_value = {"parts": []}
        mock_create.return_value = ("model-456", None)

        deploy_semantic_model_dev({"model.tmdl": "content"}, "Test Workspace", "MyModel")

        mock_resolve_ws.assert_called_once_with("Test Workspace", "test-token")

    @patch("semantic_model_generator.fabric.deployment.datetime")
    @patch("semantic_model_generator.fabric.deployment.get_fabric_token")
    @patch("semantic_model_generator.fabric.deployment.is_guid")
    @patch("semantic_model_generator.fabric.deployment.package_tmdl_for_fabric")
    @patch("semantic_model_generator.fabric.deployment.create_semantic_model")
    def test_dev_deploy_returns_model_id_on_201(
        self,
        mock_create: Mock,
        mock_package: Mock,
        mock_is_guid: Mock,
        mock_get_token: Mock,
        mock_datetime: Mock,
    ) -> None:
        """Test dev deploy returns model ID on immediate creation (201)."""
        mock_now = Mock()
        mock_now.strftime.return_value = "20260210T000000Z"
        mock_datetime.now.return_value = mock_now
        mock_datetime.UTC = UTC

        mock_get_token.return_value = "test-token"
        mock_is_guid.return_value = True
        mock_package.return_value = {"parts": []}
        mock_create.return_value = ("model-immediate", None)

        result = deploy_semantic_model_dev({"model.tmdl": "content"}, "ws-guid-123", "MyModel")

        assert result == "model-immediate"

    @patch("semantic_model_generator.fabric.deployment.datetime")
    @patch("semantic_model_generator.fabric.deployment.get_fabric_token")
    @patch("semantic_model_generator.fabric.deployment.is_guid")
    @patch("semantic_model_generator.fabric.deployment.package_tmdl_for_fabric")
    @patch("semantic_model_generator.fabric.deployment.create_semantic_model")
    @patch("semantic_model_generator.fabric.deployment.poll_operation")
    @patch("semantic_model_generator.fabric.deployment.get_operation_result")
    def test_dev_deploy_polls_lro_on_202(
        self,
        mock_get_result: Mock,
        mock_poll: Mock,
        mock_create: Mock,
        mock_package: Mock,
        mock_is_guid: Mock,
        mock_get_token: Mock,
        mock_datetime: Mock,
    ) -> None:
        """Test dev deploy polls LRO and returns model ID from result on 202."""
        mock_now = Mock()
        mock_now.strftime.return_value = "20260210T000000Z"
        mock_datetime.now.return_value = mock_now
        mock_datetime.UTC = UTC

        mock_get_token.return_value = "test-token"
        mock_is_guid.return_value = True
        mock_package.return_value = {"parts": []}
        mock_create.return_value = (None, "op-lro-123")
        mock_poll.return_value = {"status": "Succeeded"}
        mock_get_result.return_value = {"id": "model-from-lro"}

        result = deploy_semantic_model_dev({"model.tmdl": "content"}, "ws-guid-456", "MyModel")

        mock_poll.assert_called_once_with("op-lro-123", "test-token")
        mock_get_result.assert_called_once_with("op-lro-123", "test-token")
        assert result == "model-from-lro"


class TestDeploySemanticModelProd:
    """Tests for deploy_semantic_model_prod function."""

    @patch("semantic_model_generator.fabric.deployment.get_fabric_token")
    @patch("semantic_model_generator.fabric.deployment.is_guid")
    @patch("semantic_model_generator.fabric.deployment.find_semantic_model_by_name")
    @patch("semantic_model_generator.fabric.deployment.package_tmdl_for_fabric")
    def test_prod_deploy_raises_without_confirmation(
        self,
        mock_package: Mock,
        mock_find: Mock,
        mock_is_guid: Mock,
        mock_get_token: Mock,
    ) -> None:
        """Test prod deploy raises ValueError when model exists and confirm_overwrite=False."""
        mock_get_token.return_value = "test-token"
        mock_is_guid.return_value = True
        mock_find.return_value = "model-existing-123"

        expected_msg = "Semantic model 'MyModel' already exists.*confirm_overwrite=True"
        with pytest.raises(ValueError, match=expected_msg):
            deploy_semantic_model_prod(
                {"model.tmdl": "content"}, "ws-123", "MyModel", confirm_overwrite=False
            )

    @patch("semantic_model_generator.fabric.deployment.get_fabric_token")
    @patch("semantic_model_generator.fabric.deployment.is_guid")
    @patch("semantic_model_generator.fabric.deployment.find_semantic_model_by_name")
    @patch("semantic_model_generator.fabric.deployment.package_tmdl_for_fabric")
    @patch("semantic_model_generator.fabric.deployment.update_semantic_model_definition")
    def test_prod_deploy_updates_existing_with_confirmation(
        self,
        mock_update: Mock,
        mock_package: Mock,
        mock_find: Mock,
        mock_is_guid: Mock,
        mock_get_token: Mock,
    ) -> None:
        """Test prod deploy updates existing model when confirm_overwrite=True."""
        mock_get_token.return_value = "test-token"
        mock_is_guid.return_value = True
        mock_find.return_value = "model-existing-456"
        mock_package.return_value = {"parts": []}
        mock_update.return_value = None

        result = deploy_semantic_model_prod(
            {"model.tmdl": "content"}, "ws-123", "MyModel", confirm_overwrite=True
        )

        mock_update.assert_called_once_with(
            "ws-123", "model-existing-456", {"parts": []}, "test-token"
        )
        assert result == "model-existing-456"

    @patch("semantic_model_generator.fabric.deployment.get_fabric_token")
    @patch("semantic_model_generator.fabric.deployment.is_guid")
    @patch("semantic_model_generator.fabric.deployment.find_semantic_model_by_name")
    @patch("semantic_model_generator.fabric.deployment.package_tmdl_for_fabric")
    @patch("semantic_model_generator.fabric.deployment.create_semantic_model")
    def test_prod_deploy_creates_new_if_not_exists(
        self,
        mock_create: Mock,
        mock_package: Mock,
        mock_find: Mock,
        mock_is_guid: Mock,
        mock_get_token: Mock,
    ) -> None:
        """Test prod deploy creates new model if it doesn't exist."""
        mock_get_token.return_value = "test-token"
        mock_is_guid.return_value = True
        mock_find.return_value = None
        mock_package.return_value = {"parts": []}
        mock_create.return_value = ("model-new-789", None)

        result = deploy_semantic_model_prod({"model.tmdl": "content"}, "ws-123", "MyModel")

        mock_create.assert_called_once_with("ws-123", "MyModel", {"parts": []}, "test-token")
        assert result == "model-new-789"

    @patch("semantic_model_generator.fabric.deployment.get_fabric_token")
    @patch("semantic_model_generator.fabric.deployment.is_guid")
    @patch("semantic_model_generator.fabric.deployment.find_semantic_model_by_name")
    @patch("semantic_model_generator.fabric.deployment.package_tmdl_for_fabric")
    @patch("semantic_model_generator.fabric.deployment.create_semantic_model")
    def test_prod_deploy_uses_base_name(
        self,
        mock_create: Mock,
        mock_package: Mock,
        mock_find: Mock,
        mock_is_guid: Mock,
        mock_get_token: Mock,
    ) -> None:
        """Test prod deploy uses base name without timestamp."""
        mock_get_token.return_value = "test-token"
        mock_is_guid.return_value = True
        mock_find.return_value = None
        mock_package.return_value = {"parts": []}
        mock_create.return_value = ("model-123", None)

        deploy_semantic_model_prod({"model.tmdl": "content"}, "ws-123", "MyModel")

        # Verify create was called with base name (no timestamp)
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[0][1] == "MyModel"

    @patch("semantic_model_generator.fabric.deployment.get_fabric_token")
    @patch("semantic_model_generator.fabric.deployment.is_guid")
    @patch("semantic_model_generator.fabric.deployment.find_semantic_model_by_name")
    def test_prod_deploy_raises_clear_error_message(
        self,
        mock_find: Mock,
        mock_is_guid: Mock,
        mock_get_token: Mock,
    ) -> None:
        """Test prod deploy error message includes model name and mentions confirm_overwrite."""
        mock_get_token.return_value = "test-token"
        mock_is_guid.return_value = True
        mock_find.return_value = "model-123"

        with pytest.raises(ValueError) as exc_info:
            deploy_semantic_model_prod(
                {"model.tmdl": "content"}, "ws-123", "MySpecificModel", confirm_overwrite=False
            )

        error_msg = str(exc_info.value)
        assert "MySpecificModel" in error_msg
        assert "confirm_overwrite=True" in error_msg
