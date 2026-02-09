"""Tests for TMDL whitespace validation and indentation helpers."""

import pytest
from semantic_model_generator.utils.whitespace import (
    indent_tmdl,
    validate_tmdl_indentation,
)


class TestValidTmdl:
    """Test cases for valid TMDL (tab indentation)."""

    def test_tab_indentation(self):
        """Tab-indented content is valid."""
        content = "table Sales\n\tcolumn Name"
        errors = validate_tmdl_indentation(content)
        assert errors == []

    def test_deep_tabs(self):
        """Multiple tab levels are valid."""
        content = "\t\tcolumn deep"
        errors = validate_tmdl_indentation(content)
        assert errors == []

    def test_no_indentation(self):
        """No indentation is valid."""
        content = "no indent line"
        errors = validate_tmdl_indentation(content)
        assert errors == []

    def test_empty_content(self):
        """Empty content is valid."""
        errors = validate_tmdl_indentation("")
        assert errors == []

    def test_blank_lines(self):
        """Blank lines are valid."""
        content = "\n\n\n"
        errors = validate_tmdl_indentation(content)
        assert errors == []

    def test_mixed_tabs_on_different_lines(self):
        """Different indentation levels on different lines are valid."""
        content = "table Sales\n\tcolumn Name\n\t\tproperty Value"
        errors = validate_tmdl_indentation(content)
        assert errors == []


class TestInvalidTmdl:
    """Test cases for invalid TMDL (space indentation)."""

    def test_two_spaces(self):
        """Two leading spaces produce error."""
        content = "  column Name"
        errors = validate_tmdl_indentation(content)
        assert len(errors) == 1
        assert errors[0].line_number == 1
        assert "2 leading space" in errors[0].message.lower()

    def test_spaces_on_second_line(self):
        """Spaces on second line produce error."""
        content = "table Sales\n  column Name"
        errors = validate_tmdl_indentation(content)
        assert len(errors) == 1
        assert errors[0].line_number == 2

    def test_multiple_lines_with_spaces(self):
        """Multiple lines with spaces produce multiple errors."""
        content = "  line1\n  line2"
        errors = validate_tmdl_indentation(content)
        assert len(errors) == 2
        assert errors[0].line_number == 1
        assert errors[1].line_number == 2

    def test_mixed_tab_and_space_lines(self):
        """Mixed tab lines (valid) and space lines (invalid)."""
        content = "\ttab line\n  space line"
        errors = validate_tmdl_indentation(content)
        assert len(errors) == 1
        assert errors[0].line_number == 2

    def test_four_spaces(self):
        """Four leading spaces produce error mentioning 4 spaces."""
        content = "    column Name"
        errors = validate_tmdl_indentation(content)
        assert len(errors) == 1
        assert "4 leading space" in errors[0].message.lower()


class TestIndentationErrorStructure:
    """Test the IndentationError structure."""

    def test_error_has_line_number(self):
        """Error has line_number field."""
        content = "  bad indent"
        errors = validate_tmdl_indentation(content)
        assert hasattr(errors[0], "line_number")
        assert isinstance(errors[0].line_number, int)

    def test_error_has_message(self):
        """Error has message field."""
        content = "  bad indent"
        errors = validate_tmdl_indentation(content)
        assert hasattr(errors[0], "message")
        assert isinstance(errors[0].message, str)

    def test_error_has_line_content(self):
        """Error has line_content field."""
        content = "  bad indent"
        errors = validate_tmdl_indentation(content)
        assert hasattr(errors[0], "line_content")
        assert isinstance(errors[0].line_content, str)

    def test_line_content_truncated(self):
        """Line content is truncated to 50 chars."""
        content = "  " + "x" * 100
        errors = validate_tmdl_indentation(content)
        assert len(errors[0].line_content) <= 50


class TestIndentHelper:
    """Test indent_tmdl helper function."""

    def test_indent_zero(self):
        """indent_tmdl(0) returns empty string."""
        assert indent_tmdl(0) == ""

    def test_indent_one(self):
        """indent_tmdl(1) returns single tab."""
        assert indent_tmdl(1) == "\t"

    def test_indent_two(self):
        """indent_tmdl(2) returns two tabs."""
        assert indent_tmdl(2) == "\t\t"

    def test_indent_three(self):
        """indent_tmdl(3) returns three tabs."""
        assert indent_tmdl(3) == "\t\t\t"

    def test_indent_negative_raises_error(self):
        """indent_tmdl(-1) raises ValueError."""
        with pytest.raises(ValueError, match="level must be non-negative"):
            indent_tmdl(-1)
