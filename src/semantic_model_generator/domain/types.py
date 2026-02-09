"""Domain types for semantic model generation."""

import uuid
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


class TableClassification(StrEnum):
    """Classification of a warehouse table in star schema."""

    DIMENSION = "dimension"
    FACT = "fact"
    UNCLASSIFIED = "unclassified"


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


@dataclass(frozen=True, slots=True)
class Relationship:
    """Inferred star-schema relationship between tables."""

    id: uuid.UUID
    from_table: str  # Schema-qualified fact table: "dbo.FactSales"
    from_column: str  # FK column name: "FK_CustomerID"
    to_table: str  # Schema-qualified dim table: "dbo.DimCustomer"
    to_column: str  # PK column name: "SK_CustomerID"
    is_active: bool
    cross_filtering_behavior: str = "oneDirection"
    from_cardinality: str = "many"
    to_cardinality: str = "one"
