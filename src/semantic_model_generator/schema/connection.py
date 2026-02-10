"""Fabric warehouse connection factory using mssql-python.

Connects to Microsoft Fabric warehouses using mssql-python (Microsoft's official
Python driver released GA January 2026). Uses DDBC (Direct Database Connectivity)
instead of routing through ODBC Driver Manager.

Authentication:
- In Fabric notebooks: Uses notebookutils.credentials.getToken() with token
  passed via SQL_COPT_SS_ACCESS_TOKEN
- Otherwise: Uses ActiveDirectoryDefault which leverages DefaultAzureCredential

References:
- https://learn.microsoft.com/en-us/fabric/database/sql/connect-python
- https://github.com/microsoft/mssql-python/wiki/Microsoft-Entra-ID-support
- https://pypi.org/project/mssql-python/
"""

import struct
import sys

import mssql_python
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

SQL_COPT_SS_ACCESS_TOKEN = 1256  # SQL Server access token attribute
SQL_DATABASE_RESOURCE = "https://database.windows.net"


def _is_fabric_notebook() -> bool:
    """Detect if running in Fabric notebook environment.

    Returns:
        True if notebookutils module is available (Fabric notebook), False otherwise.
    """
    return "notebookutils" in sys.modules


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

    Authentication method depends on environment:
    - In Fabric notebooks: Uses notebookutils.credentials.getToken() with
      token passed via attrs_before
    - Otherwise: Uses ActiveDirectoryDefault (DefaultAzureCredential)

    Supports multiple credential sources when not in notebook:
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
    if _is_fabric_notebook():
        # Fabric notebook: use notebookutils token with SQL_COPT_SS_ACCESS_TOKEN
        import notebookutils  # noqa: PGH003

        token: str = notebookutils.credentials.getToken(SQL_DATABASE_RESOURCE)
        token_bytes = token.encode("UTF-16-LE")

        # Pack token with length prefix for SQL_COPT_SS_ACCESS_TOKEN
        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)

        connection_string = (
            f"Server={sql_endpoint},1433;Database={database};Encrypt=Yes;TrustServerCertificate=No"
        )

        return mssql_python.connect(
            connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct}
        )
    else:
        # Standard environment: use ActiveDirectoryDefault
        connection_string = (
            f"Server={sql_endpoint},1433;"
            f"Database={database};"
            "Authentication=ActiveDirectoryDefault;"
            "Encrypt=Yes;"
            "TrustServerCertificate=No"
        )

        return mssql_python.connect(connection_string)
