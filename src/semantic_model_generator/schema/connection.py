"""Fabric warehouse connection factory with token authentication.

Connects to Microsoft Fabric warehouses using pyodbc + azure-identity.
Token auth uses UTF-16-LE encoding via SQL_COPT_SS_ACCESS_TOKEN (1256).

References:
- https://debruyn.dev/2023/connect-to-fabric-lakehouses-warehouses-from-python-code/
- https://learn.microsoft.com/en-us/fabric/data-warehouse/connectivity
"""

import struct
from itertools import chain, repeat

import pyodbc
from azure.identity import DefaultAzureCredential
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# SQL_COPT_SS_ACCESS_TOKEN attribute code for pyodbc
_SQL_COPT_SS_ACCESS_TOKEN = 1256

# Azure SQL Database token scope
_TOKEN_SCOPE = "https://database.windows.net//.default"


def encode_token_for_odbc(token: str) -> bytes:
    """Encode authentication token as UTF-16-LE bytes with length prefix.

    pyodbc requires tokens encoded as:
    1. UTF-16-LE byte string (each byte interleaved with 0x00)
    2. Prefixed with 4-byte little-endian integer of encoded length
    """
    token_as_bytes = token.encode("UTF-8")
    encoded_bytes = bytes(chain.from_iterable(zip(token_as_bytes, repeat(0))))
    return struct.pack("<i", len(encoded_bytes)) + encoded_bytes


@retry(
    retry=retry_if_exception_type((pyodbc.OperationalError, pyodbc.InterfaceError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def create_fabric_connection(
    sql_endpoint: str,
    database: str,
) -> pyodbc.Connection:
    """Create authenticated connection to a Fabric warehouse.

    Uses DefaultAzureCredential for token acquisition (supports managed identity,
    CLI credentials, environment variables, etc.).

    Args:
        sql_endpoint: Fabric SQL analytics endpoint (e.g., xxx.datawarehouse.fabric.microsoft.com)
        database: Database name in the warehouse

    Returns:
        Authenticated pyodbc Connection

    Raises:
        pyodbc.OperationalError: After 3 retry attempts on transient failures
        azure.core.exceptions.ClientAuthenticationError: If no valid credential found
    """
    credential = DefaultAzureCredential()
    token_object = credential.get_token(_TOKEN_SCOPE)
    token_bytes = encode_token_for_odbc(token_object.token)

    attrs_before = {_SQL_COPT_SS_ACCESS_TOKEN: token_bytes}

    connection_string = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={sql_endpoint},1433;"
        f"Database={database};"
        "Encrypt=Yes;"
        "TrustServerCertificate=No"
    )

    return pyodbc.connect(connection_string, attrs_before=attrs_before)
