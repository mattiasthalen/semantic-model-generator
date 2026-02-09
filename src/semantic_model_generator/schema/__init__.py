"""Schema discovery and classification."""

from semantic_model_generator.domain.types import Relationship, TableClassification
from semantic_model_generator.schema.classification import classify_table, classify_tables
from semantic_model_generator.schema.connection import create_fabric_connection
from semantic_model_generator.schema.discovery import discover_tables
from semantic_model_generator.schema.filtering import filter_tables
from semantic_model_generator.schema.relationships import infer_relationships

__all__ = [
    "Relationship",
    "TableClassification",
    "classify_table",
    "classify_tables",
    "create_fabric_connection",
    "discover_tables",
    "filter_tables",
    "infer_relationships",
]
