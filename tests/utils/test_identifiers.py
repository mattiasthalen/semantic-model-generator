"""Tests for TMDL identifier quoting and unquoting."""

import pytest

from semantic_model_generator.utils.identifiers import (
    quote_tmdl_identifier,
    unquote_tmdl_identifier,
)


class TestNoQuotingNeeded:
    """Test cases where identifiers don't need quoting."""

    def test_simple_alphanumeric(self):
        """Simple alphanumeric names don't need quotes."""
        assert quote_tmdl_identifier("Sales") == "Sales"

    def test_mixed_case(self):
        """Mixed case alphanumeric names don't need quotes."""
        assert quote_tmdl_identifier("DimProduct") == "DimProduct"

    def test_with_underscore(self):
        """Names with underscores don't need quotes."""
        assert quote_tmdl_identifier("Fact_Sales") == "Fact_Sales"


class TestQuotingTriggered:
    """Test cases where special characters trigger quoting."""

    def test_whitespace(self):
        """Whitespace triggers quoting."""
        assert quote_tmdl_identifier("Product Name") == "'Product Name'"

    def test_dot(self):
        """Dot triggers quoting."""
        assert quote_tmdl_identifier("Table.Column") == "'Table.Column'"

    def test_equals(self):
        """Equals sign triggers quoting."""
        assert quote_tmdl_identifier("Key=Value") == "'Key=Value'"

    def test_colon(self):
        """Colon triggers quoting."""
        assert quote_tmdl_identifier("Type:Name") == "'Type:Name'"

    def test_single_quote(self):
        """Single quote triggers quoting and is escaped by doubling."""
        assert quote_tmdl_identifier("Customer's Choice") == "'Customer''s Choice'"

    def test_tab_character(self):
        """Tab character triggers quoting."""
        assert quote_tmdl_identifier("Name\tExtra") == "'Name\tExtra'"


class TestMultipleSpecialChars:
    """Test cases with multiple special characters."""

    def test_space_and_dot(self):
        """Multiple special characters are handled."""
        assert quote_tmdl_identifier("My Table.Col Name") == "'My Table.Col Name'"

    def test_quote_dot_space(self):
        """Quote, dot, and space combined."""
        assert quote_tmdl_identifier("It's a.test") == "'It''s a.test'"


class TestUnquoting:
    """Test unquoting identifiers."""

    def test_unquote_simple(self):
        """Unquoting simple name returns unchanged."""
        assert unquote_tmdl_identifier("Sales") == "Sales"

    def test_unquote_quoted(self):
        """Unquoting quoted name removes outer quotes."""
        assert unquote_tmdl_identifier("'Product Name'") == "Product Name"

    def test_unquote_escaped_quote(self):
        """Unquoting handles escaped internal quotes."""
        assert unquote_tmdl_identifier("'Customer''s Choice'") == "Customer's Choice"

    def test_unquote_complex(self):
        """Unquoting complex quoted name."""
        assert unquote_tmdl_identifier("'It''s a.test'") == "It's a.test"


class TestRoundTrip:
    """Test that quote/unquote is idempotent."""

    @pytest.mark.parametrize(
        "name",
        [
            "Sales",
            "Product Name",
            "Customer's Choice",
            "Table.Column",
            "Key=Value",
            "Type:Name",
            "It's a.test",
        ],
    )
    def test_round_trip(self, name):
        """unquote(quote(name)) == name for all valid names."""
        quoted = quote_tmdl_identifier(name)
        unquoted = unquote_tmdl_identifier(quoted)
        assert unquoted == name


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string_raises_error(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            quote_tmdl_identifier("")

    def test_empty_string_unquote_raises_error(self):
        """Empty string raises ValueError on unquote."""
        with pytest.raises(ValueError, match="cannot be empty"):
            unquote_tmdl_identifier("")
