"""TMDL metadata file generators for .platform, definition.pbism, and diagramLayout.json."""

import json
from collections.abc import Sequence

from semantic_model_generator.domain.types import (
    TableClassification,
    TableMetadata,
)
from semantic_model_generator.utils.uuid_gen import generate_deterministic_uuid


def generate_platform_json(model_name: str) -> str:
    """Generate .platform JSON file content.

    Args:
        model_name: Name of the semantic model.

    Returns:
        JSON string with fabric gitIntegration schema, SemanticModel type,
        displayName, and deterministic logicalId.
    """
    logical_id = generate_deterministic_uuid("platform", model_name)

    platform_data = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "config": {
            "logicalId": str(logical_id),
            "version": "2.0",
        },
        "metadata": {
            "displayName": model_name,
            "type": "SemanticModel",
        },
    }

    return json.dumps(platform_data, indent=2, sort_keys=True)


def generate_definition_pbism_json() -> str:
    """Generate definition.pbism JSON file content.

    The Fabric semanticModel schema only allows $schema, version, and settings.
    Properties like name, description, author, createdAt, modifiedAt are NOT
    allowed (schema has additionalProperties: false).

    Returns:
        JSON string with fabric semanticModel schema, version, and empty settings.
    """
    definition_data = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "settings": {},
        "version": "4.2",
    }

    return json.dumps(definition_data, indent=2, sort_keys=True)


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
    # Hardcoded layout constants
    table_width = 220
    table_height = 140
    x_gap = 40
    y_gap = 40

    # Separate and sort tables by classification
    dimensions = []
    facts = []

    for table in tables:
        classification = classifications.get(
            (table.schema_name, table.table_name), TableClassification.UNCLASSIFIED
        )
        if classification == TableClassification.DIMENSION:
            dimensions.append(table)
        elif classification == TableClassification.FACT:
            facts.append(table)
        # Skip unclassified tables

    # Sort each group by (schema_name, table_name)
    dimensions.sort(key=lambda t: (t.schema_name, t.table_name))
    facts.sort(key=lambda t: (t.schema_name, t.table_name))

    # Layout: dimensions in horizontal row(s), facts in vertical column to the right
    table_entries = []

    # Layout dimensions horizontally (incrementing x)
    dim_x = 0
    dim_y = 0
    for dim in dimensions:
        table_entries.append(
            {
                "name": dim.table_name,
                "x": dim_x,
                "y": dim_y,
                "width": table_width,
                "height": table_height,
            }
        )
        dim_x += table_width + x_gap

    # Layout facts vertically in column to the right of dimensions
    # Start facts at x position after all dimensions
    fact_x = dim_x if dimensions else 0
    fact_y = 0
    for fact in facts:
        table_entries.append(
            {
                "name": fact.table_name,
                "x": fact_x,
                "y": fact_y,
                "width": table_width,
                "height": table_height,
            }
        )
        fact_y += table_height + y_gap

    layout_data = {
        "version": 1,
        "tables": table_entries,
    }

    return json.dumps(layout_data, indent=2, sort_keys=True)
