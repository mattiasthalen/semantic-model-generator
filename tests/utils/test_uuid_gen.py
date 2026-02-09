"""Tests for deterministic UUID generation."""

import uuid

import pytest
from semantic_model_generator.utils.uuid_gen import (
    SEMANTIC_MODEL_NAMESPACE,
    generate_deterministic_uuid,
)


class TestDeterminism:
    """Test that same inputs produce same UUID."""

    def test_table_determinism(self):
        """Calling with same table twice returns identical UUID."""
        uuid1 = generate_deterministic_uuid("table", "Sales")
        uuid2 = generate_deterministic_uuid("table", "Sales")
        assert uuid1 == uuid2

    def test_column_determinism(self):
        """Calling with same column twice returns identical UUID."""
        uuid1 = generate_deterministic_uuid("column", "Sales.Amount")
        uuid2 = generate_deterministic_uuid("column", "Sales.Amount")
        assert uuid1 == uuid2


class TestDifferentInputs:
    """Test that different inputs produce different UUIDs."""

    def test_different_names_same_type(self):
        """Different object names produce different UUIDs."""
        uuid_sales = generate_deterministic_uuid("table", "Sales")
        uuid_customers = generate_deterministic_uuid("table", "Customers")
        assert uuid_sales != uuid_customers

    def test_different_types_same_name(self):
        """Different object types with same name produce different UUIDs."""
        uuid_table = generate_deterministic_uuid("table", "Sales")
        uuid_column = generate_deterministic_uuid("column", "Sales")
        assert uuid_table != uuid_column


class TestInputNormalization:
    """Test that inputs are normalized correctly."""

    def test_trailing_space_stripped_from_name(self):
        """Trailing spaces in object_name are stripped."""
        uuid1 = generate_deterministic_uuid("table", "Sales")
        uuid2 = generate_deterministic_uuid("table", "Sales ")
        assert uuid1 == uuid2

    def test_leading_space_stripped_from_name(self):
        """Leading spaces in object_name are stripped."""
        uuid1 = generate_deterministic_uuid("table", "Sales")
        uuid2 = generate_deterministic_uuid("table", " Sales")
        assert uuid1 == uuid2

    def test_object_type_case_normalized(self):
        """Object type is case-normalized (lowercased)."""
        uuid1 = generate_deterministic_uuid("TABLE", "Sales")
        uuid2 = generate_deterministic_uuid("table", "Sales")
        assert uuid1 == uuid2


class TestCasePreservation:
    """Test that object_name case is preserved."""

    def test_name_case_matters(self):
        """Object name case is preserved (source system may be case-sensitive)."""
        uuid_upper = generate_deterministic_uuid("table", "Sales")
        uuid_lower = generate_deterministic_uuid("table", "sales")
        assert uuid_upper != uuid_lower


class TestReturnType:
    """Test return type properties."""

    def test_returns_uuid_instance(self):
        """Result is a uuid.UUID instance."""
        result = generate_deterministic_uuid("table", "Sales")
        assert isinstance(result, uuid.UUID)

    def test_returns_uuid5(self):
        """Result is a UUID version 5 (uuid5)."""
        result = generate_deterministic_uuid("table", "Sales")
        assert result.version == 5


class TestNamespaceConstant:
    """Test SEMANTIC_MODEL_NAMESPACE properties."""

    def test_namespace_is_uuid(self):
        """SEMANTIC_MODEL_NAMESPACE is a UUID instance."""
        assert isinstance(SEMANTIC_MODEL_NAMESPACE, uuid.UUID)

    def test_namespace_not_well_known(self):
        """SEMANTIC_MODEL_NAMESPACE is not a well-known namespace."""
        assert SEMANTIC_MODEL_NAMESPACE != uuid.NAMESPACE_DNS
        assert SEMANTIC_MODEL_NAMESPACE != uuid.NAMESPACE_URL
        assert SEMANTIC_MODEL_NAMESPACE != uuid.NAMESPACE_OID
        assert SEMANTIC_MODEL_NAMESPACE != uuid.NAMESPACE_X500


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_object_type_raises_error(self):
        """Empty object_type raises ValueError."""
        with pytest.raises(ValueError, match="object_type cannot be empty"):
            generate_deterministic_uuid("", "Sales")

    def test_whitespace_only_object_type_raises_error(self):
        """Whitespace-only object_type raises ValueError after stripping."""
        with pytest.raises(ValueError, match="object_type cannot be empty"):
            generate_deterministic_uuid("   ", "Sales")

    def test_empty_object_name_raises_error(self):
        """Empty object_name raises ValueError."""
        with pytest.raises(ValueError, match="object_name cannot be empty"):
            generate_deterministic_uuid("table", "")

    def test_whitespace_only_object_name_raises_error(self):
        """Whitespace-only object_name raises ValueError after stripping."""
        with pytest.raises(ValueError, match="object_name cannot be empty"):
            generate_deterministic_uuid("table", "   ")
