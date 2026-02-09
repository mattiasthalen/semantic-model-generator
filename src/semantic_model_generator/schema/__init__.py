"""Schema discovery and classification."""

from semantic_model_generator.domain.types import TableClassification
from semantic_model_generator.schema.classification import classify_table, classify_tables
from semantic_model_generator.schema.filtering import filter_tables

__all__ = ["TableClassification", "classify_table", "classify_tables", "filter_tables"]
