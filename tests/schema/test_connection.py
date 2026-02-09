"""Tests for Fabric warehouse connection factory using mssql-python."""

from unittest.mock import Mock, patch

import mssql_python

from semantic_model_generator.schema.connection import create_fabric_connection


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
            mssql_python.OperationalError("Transient error 1"),
            mssql_python.OperationalError("Transient error 2"),
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
