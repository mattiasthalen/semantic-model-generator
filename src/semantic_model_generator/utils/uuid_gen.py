"""Deterministic UUID generation for semantic model objects."""

import uuid

# Project-specific namespace for uuid5 generation.
# Generated once via uuid.uuid4(), committed as constant.
# All semantic model UUIDs are derived from this namespace.
SEMANTIC_MODEL_NAMESPACE = uuid.UUID("b8a7d3f2-6c1e-4a59-9d2b-8f3e7c5a1d04")


def generate_deterministic_uuid(object_type: str, object_name: str) -> uuid.UUID:
    """Generate a stable UUID for a semantic model object.

    Uses uuid5 (SHA-1) with a project-specific namespace to ensure:
    - Same inputs always produce the same UUID
    - Different inputs produce different UUIDs
    - UUIDs are stable across regenerations (REQ-12)

    Args:
        object_type: Type of object (e.g., "table", "column", "relationship").
            Normalized to lowercase, stripped of whitespace.
        object_name: Fully qualified name of object (e.g., "Sales", "Sales.Amount").
            Stripped of whitespace but case is preserved (source systems may be case-sensitive).

    Returns:
        Deterministic UUID based on object type and name.

    Raises:
        ValueError: If object_type or object_name is empty after stripping.
    """
    normalized_type = object_type.strip().lower()
    normalized_name = object_name.strip()

    if not normalized_type:
        raise ValueError("object_type cannot be empty")
    if not normalized_name:
        raise ValueError("object_name cannot be empty")

    composite_name = f"{normalized_type}:{normalized_name}"
    return uuid.uuid5(SEMANTIC_MODEL_NAMESPACE, composite_name)
