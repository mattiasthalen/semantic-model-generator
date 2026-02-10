"""Fabric REST API integration modules."""

from semantic_model_generator.fabric.auth import get_fabric_token
from semantic_model_generator.fabric.packaging import package_tmdl_for_fabric
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
]
