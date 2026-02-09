"""Domain types for semantic model generation."""

from dataclasses import dataclass
from enum import StrEnum


class TmdlDataType(StrEnum):
    """TMDL tabular model data types.

    Based on Analysis Services tabular model data types.
    See: https://learn.microsoft.com/en-us/analysis-services/tabular-models/data-types-supported-ssas-tabular
    """

    INT64 = "int64"
    DOUBLE = "double"
    BOOLEAN = "boolean"
    STRING = "string"
    DATETIME = "dateTime"
    DECIMAL = "decimal"
    BINARY = "binary"


@dataclass(frozen=True, slots=True)
class ColumnMetadata:
    """Immutable metadata for a warehouse column."""

    name: str
    sql_type: str
    is_nullable: bool
    ordinal_position: int
    max_length: int | None = None
    numeric_precision: int | None = None
    numeric_scale: int | None = None

    def __post_init__(self) -> None:
        """Validate invariants after construction."""
        if not self.name:
            raise ValueError("Column name cannot be empty")
        if self.ordinal_position < 1:
            raise ValueError("Ordinal position must be >= 1")


@dataclass(frozen=True, slots=True)
class TableMetadata:
    """Immutable metadata for a warehouse table."""

    schema_name: str
    table_name: str
    columns: tuple[ColumnMetadata, ...]
