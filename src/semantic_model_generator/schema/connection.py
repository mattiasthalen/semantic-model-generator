"""Fabric warehouse connection factory using mssql-python.

Connects to Microsoft Fabric warehouses using mssql-python (Microsoft's official
Python driver released GA January 2026). Uses DDBC (Direct Database Connectivity)
instead of routing through ODBC Driver Manager.

Authentication via ActiveDirectoryDefault leverages DefaultAzureCredential internally,
supporting managed identity, CLI credentials, environment variables, etc.

References:
- https://learn.microsoft.com/en-us/fabric/database/sql/connect-python
- https://github.com/microsoft/mssql-python/wiki/Microsoft-Entra-ID-support
- https://pypi.org/project/mssql-python/
"""

import mssql_python
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


@retry(
    retry=retry_if_exception_type((mssql_python.OperationalError, mssql_python.InterfaceError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def create_fabric_connection(
    sql_endpoint: str,
    database: str,
) -> mssql_python.Connection:
    """Create authenticated connection to a Fabric warehouse.

    Uses ActiveDirectoryDefault authentication which internally leverages
    DefaultAzureCredential. Supports multiple credential sources:
    - Managed Identity (production Azure services)
    - Azure CLI (local development)
    - Environment variables (CI/CD pipelines)
    - Visual Studio Code
    - Azure PowerShell

    Args:
        sql_endpoint: Fabric SQL analytics endpoint (e.g., xxx.datawarehouse.fabric.microsoft.com)
        database: Database name in the warehouse

    Returns:
        Authenticated mssql_python Connection

    Raises:
        mssql_python.OperationalError: After 3 retry attempts on transient failures
        mssql_python.InterfaceError: Connection configuration errors
        azure.core.exceptions.ClientAuthenticationError: If no valid credential found
    """
    connection_string = (
        f"Server={sql_endpoint},1433;"
        f"Database={database};"
        "Authentication=ActiveDirectoryDefault;"
        "Encrypt=Yes;"
        "TrustServerCertificate=No"
    )

    return mssql_python.connect(connection_string)
