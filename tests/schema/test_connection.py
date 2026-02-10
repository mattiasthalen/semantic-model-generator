"""Tests for Fabric warehouse connection factory using mssql-python."""

import struct
import sys
from unittest.mock import Mock, patch

import mssql_python

from semantic_model_generator.schema.connection import (
    SQL_COPT_SS_ACCESS_TOKEN,
    create_fabric_connection,
)


@patch("semantic_model_generator.schema.connection.mssql_python")
class TestCreateFabricConnection:
    """Test connection factory with mocked mssql_python driver."""

    def test_connection_string_format(self, mock_mssql_python):
        """Connection string uses ActiveDirectoryDefault authentication."""
        mock_mssql_python.connect.return_value = Mock()

        sql_endpoint = "test-endpoint.datawarehouse.fabric.microsoft.com"
        database = "test-database"

        create_fabric_connection(sql_endpoint, database)

        # Get the connection string from the mock call
        call_args = mock_mssql_python.connect.call_args
        conn_string = call_args[0][0]

        # Verify required components
        assert f"Server={sql_endpoint},1433" in conn_string
        assert f"Database={database}" in conn_string
        assert "Authentication=ActiveDirectoryDefault" in conn_string
        assert "Encrypt=Yes" in conn_string
        assert "TrustServerCertificate=No" in conn_string

        # Verify excluded parameters (ActiveDirectoryDefault handles auth internally)
        assert "UID=" not in conn_string
        assert "PWD=" not in conn_string

    def test_retry_on_operational_error(self, mock_mssql_python):
        """Transient mssql_python errors are retried up to 3 times."""
        # Use the real mssql_python exception classes for the retry decorator to catch
        mock_mssql_python.OperationalError = mssql_python.OperationalError
        mock_mssql_python.InterfaceError = mssql_python.InterfaceError

        # Simulate 2 failures then success
        mock_conn = Mock()
        mock_mssql_python.connect.side_effect = [
            mssql_python.OperationalError("Driver error", "Transient connection error"),
            mssql_python.OperationalError("Driver error", "Transient connection error"),
            mock_conn,  # Success on third attempt
        ]

        result = create_fabric_connection("endpoint.fabric.microsoft.com", "mydb")

        # Should succeed after retries
        assert result == mock_conn
        # Should have been called 3 times (2 failures + 1 success)
        assert mock_mssql_python.connect.call_count == 3

    def test_returns_connection_object(self, mock_mssql_python):
        """Factory returns the mssql_python Connection object."""
        mock_conn = Mock()
        mock_mssql_python.connect.return_value = mock_conn

        result = create_fabric_connection("endpoint.fabric.microsoft.com", "mydb")

        assert result == mock_conn

    def test_notebook_authentication(self, mock_mssql_python):
        """In Fabric notebook, uses notebookutils token with SQL_COPT_SS_ACCESS_TOKEN."""
        mock_notebookutils = Mock()
        mock_notebookutils.credentials.getToken.return_value = "notebook-sql-token"
        mock_conn = Mock()
        mock_mssql_python.connect.return_value = mock_conn

        sql_endpoint = "test-endpoint.datawarehouse.fabric.microsoft.com"
        database = "test-database"

        with patch.dict(sys.modules, {"notebookutils": mock_notebookutils}):
            result = create_fabric_connection(sql_endpoint, database)

            # Verify notebookutils was called for SQL database resource
            mock_notebookutils.credentials.getToken.assert_called_once_with(
                "https://database.windows.net"
            )

            # Verify connection call
            assert mock_mssql_python.connect.call_count == 1
            call_args = mock_mssql_python.connect.call_args

            # First argument: connection string (no Authentication=ActiveDirectoryDefault)
            conn_string = call_args[0][0]
            assert f"Server={sql_endpoint},1433" in conn_string
            assert f"Database={database}" in conn_string
            assert "Encrypt=Yes" in conn_string
            assert "TrustServerCertificate=No" in conn_string
            assert "Authentication=ActiveDirectoryDefault" not in conn_string

            # Second argument: attrs_before with SQL_COPT_SS_ACCESS_TOKEN
            attrs_before = call_args[1].get("attrs_before", {})
            assert SQL_COPT_SS_ACCESS_TOKEN in attrs_before

            # Verify token struct format
            token_struct = attrs_before[SQL_COPT_SS_ACCESS_TOKEN]
            token_bytes = "notebook-sql-token".encode("UTF-16-LE")
            expected_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
            assert token_struct == expected_struct

            assert result == mock_conn

    def test_standard_authentication_outside_notebook(self, mock_mssql_python):
        """Outside notebook, uses ActiveDirectoryDefault authentication."""
        mock_conn = Mock()
        mock_mssql_python.connect.return_value = mock_conn

        # Ensure notebookutils is NOT in sys.modules
        original_modules = sys.modules.copy()
        if "notebookutils" in sys.modules:
            del sys.modules["notebookutils"]

        try:
            sql_endpoint = "test-endpoint.datawarehouse.fabric.microsoft.com"
            database = "test-database"

            result = create_fabric_connection(sql_endpoint, database)

            # Verify connection call
            assert mock_mssql_python.connect.call_count == 1
            call_args = mock_mssql_python.connect.call_args

            # Should only have connection string argument (no attrs_before)
            conn_string = call_args[0][0]
            assert f"Server={sql_endpoint},1433" in conn_string
            assert f"Database={database}" in conn_string
            assert "Authentication=ActiveDirectoryDefault" in conn_string
            assert "Encrypt=Yes" in conn_string

            # No attrs_before parameter
            assert "attrs_before" not in call_args[1]

            assert result == mock_conn
        finally:
            # Restore original sys.modules
            sys.modules.clear()
            sys.modules.update(original_modules)
