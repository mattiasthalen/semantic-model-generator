"""SQL Server to TMDL data type mapping.

Maps Microsoft Fabric warehouse SQL types to TMDL tabular model data types.
Based on: https://learn.microsoft.com/en-us/fabric/data-warehouse/data-types
"""

from semantic_model_generator.domain.types import TmdlDataType

# Mapping from SQL Server types (Fabric warehouse) to TMDL types
SQL_TO_TMDL_TYPE: dict[str, TmdlDataType] = {
    # Integer types
    "bit": TmdlDataType.BOOLEAN,
    "smallint": TmdlDataType.INT64,
    "int": TmdlDataType.INT64,
    "bigint": TmdlDataType.INT64,
    # Decimal types
    "decimal": TmdlDataType.DECIMAL,
    "numeric": TmdlDataType.DECIMAL,
    "float": TmdlDataType.DOUBLE,
    "real": TmdlDataType.DOUBLE,
    # Character types
    "char": TmdlDataType.STRING,
    "varchar": TmdlDataType.STRING,
    # Date/time types
    "date": TmdlDataType.DATETIME,
    "datetime2": TmdlDataType.DATETIME,
    "time": TmdlDataType.DATETIME,
    # Binary types
    "varbinary": TmdlDataType.BINARY,
    "uniqueidentifier": TmdlDataType.BINARY,
}


def map_sql_type_to_tmdl(sql_type: str) -> TmdlDataType:
    """Map Microsoft Fabric warehouse SQL type to TMDL data type.

    Args:
        sql_type: SQL Server data type name (case-insensitive)

    Returns:
        Corresponding TMDL data type

    Raises:
        ValueError: If SQL type is not supported

    Example:
        >>> map_sql_type_to_tmdl("varchar")
        <TmdlDataType.STRING: 'string'>
        >>> map_sql_type_to_tmdl("INT")
        <TmdlDataType.INT64: 'int64'>
    """
    normalized = sql_type.lower().strip()

    if not normalized:
        raise ValueError("SQL type cannot be empty")

    if normalized not in SQL_TO_TMDL_TYPE:
        supported = ", ".join(sorted(SQL_TO_TMDL_TYPE.keys()))
        raise ValueError(f"Unsupported SQL type: '{sql_type}'. Supported types: {supported}")

    return SQL_TO_TMDL_TYPE[normalized]
