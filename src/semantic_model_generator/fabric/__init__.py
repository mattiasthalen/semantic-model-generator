"""Fabric REST API integration modules."""

from semantic_model_generator.fabric.auth import get_fabric_token
from semantic_model_generator.fabric.deployment import (
    create_semantic_model,
    deploy_semantic_model_dev,
    deploy_semantic_model_prod,
    find_semantic_model_by_name,
    update_semantic_model_definition,
)
from semantic_model_generator.fabric.packaging import package_tmdl_for_fabric
from semantic_model_generator.fabric.polling import get_operation_result, poll_operation
from semantic_model_generator.fabric.resolution import (
    build_direct_lake_url,
    is_guid,
    resolve_direct_lake_url,
    resolve_lakehouse_id,
    resolve_workspace_id,
)

__all__ = [
    "get_fabric_token",
    "resolve_workspace_id",
    "resolve_lakehouse_id",
    "resolve_direct_lake_url",
    "build_direct_lake_url",
    "is_guid",
    "package_tmdl_for_fabric",
    "poll_operation",
    "get_operation_result",
    "find_semantic_model_by_name",
    "create_semantic_model",
    "update_semantic_model_definition",
    "deploy_semantic_model_dev",
    "deploy_semantic_model_prod",
]
