"""TMDL metadata file generators for .platform, definition.pbism, and diagramLayout.json."""

from collections.abc import Sequence

from semantic_model_generator.domain.types import (
    TableClassification,
    TableMetadata,
)


def generate_platform_json(model_name: str) -> str:
    """Generate .platform JSON file content.

    Args:
        model_name: Name of the semantic model.

    Returns:
        JSON string with fabric gitIntegration schema, SemanticModel type,
        displayName, and deterministic logicalId.
    """
    raise NotImplementedError("Task 1: RED - to be implemented in Task 2")


def generate_definition_pbism_json(
    model_name: str,
    description: str = "",
    author: str = "",
    timestamp: str | None = None,
) -> str:
    """Generate definition.pbism JSON file content.

    Per user decision: definition.pbism must include model name, description,
    version, author (if available), and timestamps.

    Args:
        model_name: Name of the semantic model.
        description: Model description (default empty).
        author: Model author (default empty).
        timestamp: ISO 8601 timestamp for createdAt/modifiedAt (default None = generate now).

    Returns:
        JSON string with fabric semanticModel schema, name, description,
        version, author, createdAt, modifiedAt, and settings.
    """
    raise NotImplementedError("Task 1: RED - to be implemented in Task 2")


def generate_diagram_layout_json(
    tables: Sequence[TableMetadata],
    classifications: dict[tuple[str, str], TableClassification],
) -> str:
    """Generate diagramLayout.json file content.

    Per user decision: facts in left column, dimensions as rows above and below facts.

    Args:
        tables: All tables in the model.
        classifications: Map of (schema, table) to TableClassification.

    Returns:
        JSON string with version and tables array containing name, x, y, width, height
        for each table. Layout visually separates facts from dimensions.
    """
    raise NotImplementedError("Task 1: RED - to be implemented in Task 2")
