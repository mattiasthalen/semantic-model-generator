"""Tests for Fabric warehouse connection factory."""

import struct
from unittest.mock import MagicMock, Mock, patch

from semantic_model_generator.schema.connection import (
    create_fabric_connection,
    encode_token_for_odbc,
)


class TestTokenEncoding:
    """Test token encoding to UTF-16-LE with length prefix."""

    def test_simple_token_encoding(self):
        """Token is encoded as UTF-16-LE bytes with length prefix."""
        token = "test"
        result = encode_token_for_odbc(token)

        # First 4 bytes are little-endian integer length
        expected_length = len(token) * 2  # UTF-16-LE: each ASCII char becomes 2 bytes
        actual_length = struct.unpack("<i", result[:4])[0]
        assert actual_length == expected_length

        # Remaining bytes are UTF-16-LE encoded (each byte followed by 0x00)
        encoded_bytes = result[4:]
        # 't' 'e' 's' 't' -> b't\x00e\x00s\x00t\x00'
        assert encoded_bytes == b"t\x00e\x00s\x00t\x00"

    def test_empty_token(self):
        """Empty token produces length-prefixed empty bytes."""
        token = ""
        result = encode_token_for_odbc(token)

        # First 4 bytes should be 0 (no encoded content)
        length = struct.unpack("<i", result[:4])[0]
        assert length == 0
        assert len(result) == 4  # Only the length prefix

    def test_longer_token(self):
        """Longer token is correctly encoded."""
        token = "myaccesstoken123"
        result = encode_token_for_odbc(token)

        expected_length = len(token) * 2
        actual_length = struct.unpack("<i", result[:4])[0]
        assert actual_length == expected_length
        assert len(result) == 4 + expected_length


@patch("semantic_model_generator.schema.connection.pyodbc")
@patch("semantic_model_generator.schema.connection.DefaultAzureCredential")
class TestCreateFabricConnection:
    """Test connection factory with mocked pyodbc and azure-identity."""

    def test_calls_default_azure_credential(self, mock_cred_class, mock_pyodbc):
        """Factory acquires token using DefaultAzureCredential."""
        mock_token = Mock()
        mock_token.token = "test-token"
        mock_cred = Mock()
        mock_cred.get_token.return_value = mock_token
        mock_cred_class.return_value = mock_cred

        mock_pyodbc.connect.return_value = Mock()

        create_fabric_connection("endpoint.fabric.microsoft.com", "mydb")

        # Verify DefaultAzureCredential was instantiated
        mock_cred_class.assert_called_once()
        # Verify get_token called with correct scope
        mock_cred.get_token.assert_called_once_with("https://database.windows.net//.default")

    def test_connection_string_format(self, mock_cred_class, mock_pyodbc):
        """Connection string contains required parameters."""
        mock_token = Mock()
        mock_token.token = "test-token"
        mock_cred = Mock()
        mock_cred.get_token.return_value = mock_token
        mock_cred_class.return_value = mock_cred

        mock_pyodbc.connect.return_value = Mock()

        sql_endpoint = "test-endpoint.datawarehouse.fabric.microsoft.com"
        database = "test-database"

        create_fabric_connection(sql_endpoint, database)

        # Get the connection string from the mock call
        call_args = mock_pyodbc.connect.call_args
        conn_string = call_args[0][0]

        # Verify required components
        assert "ODBC Driver 18 for SQL Server" in conn_string
        assert sql_endpoint in conn_string
        assert database in conn_string
        assert "Encrypt=Yes" in conn_string
        assert "TrustServerCertificate=No" in conn_string

        # Verify excluded parameters (token auth doesn't use these)
        assert "Authentication=" not in conn_string
        assert "UID=" not in conn_string
        assert "PWD=" not in conn_string

    def test_token_passed_via_attrs_before(self, mock_cred_class, mock_pyodbc):
        """Token is passed via attrs_before with SQL_COPT_SS_ACCESS_TOKEN key."""
        mock_token = Mock()
        mock_token.token = "mytoken"
        mock_cred = Mock()
        mock_cred.get_token.return_value = mock_token
        mock_cred_class.return_value = mock_cred

        mock_pyodbc.connect.return_value = Mock()

        create_fabric_connection("endpoint.fabric.microsoft.com", "mydb")

        # Get attrs_before from the mock call
        call_args = mock_pyodbc.connect.call_args
        attrs_before = call_args[1]["attrs_before"]

        # SQL_COPT_SS_ACCESS_TOKEN = 1256
        assert 1256 in attrs_before
        # Token should be encoded
        token_bytes = attrs_before[1256]
        assert isinstance(token_bytes, bytes)
        assert len(token_bytes) > 4  # Has length prefix + encoded content

    def test_retry_on_operational_error(self, mock_cred_class, mock_pyodbc):
        """Transient pyodbc errors are retried up to 3 times."""
        mock_token = Mock()
        mock_token.token = "test-token"
        mock_cred = Mock()
        mock_cred.get_token.return_value = mock_token
        mock_cred_class.return_value = mock_cred

        # Simulate 2 failures then success
        mock_pyodbc.OperationalError = Exception  # Mock the exception class
        mock_conn = Mock()
        mock_pyodbc.connect.side_effect = [
            mock_pyodbc.OperationalError("Transient error 1"),
            mock_pyodbc.OperationalError("Transient error 2"),
            mock_conn,  # Success on third attempt
        ]

        result = create_fabric_connection("endpoint.fabric.microsoft.com", "mydb")

        # Should succeed after retries
        assert result == mock_conn
        # Should have been called 3 times (2 failures + 1 success)
        assert mock_pyodbc.connect.call_count == 3

    def test_returns_connection_object(self, mock_cred_class, mock_pyodbc):
        """Factory returns the pyodbc Connection object."""
        mock_token = Mock()
        mock_token.token = "test-token"
        mock_cred = Mock()
        mock_cred.get_token.return_value = mock_token
        mock_cred_class.return_value = mock_cred

        mock_conn = MagicMock()
        mock_pyodbc.connect.return_value = mock_conn

        result = create_fabric_connection("endpoint.fabric.microsoft.com", "mydb")

        assert result == mock_conn
