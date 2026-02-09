"""TMDL whitespace validation and indentation helpers.

TMDL requires tab-only indentation. Space indentation is invalid.
This module provides validation to detect space indentation and helpers
to generate correct tab indentation.
"""

from typing import NamedTuple


class TmdlIndentationError(NamedTuple):
    """Structured error for TMDL indentation violations.

    Attributes:
        line_number: 1-based line number where error occurred.
        message: Human-readable error message.
        line_content: Content of the line (truncated to 50 chars).
    """

    line_number: int
    message: str
    line_content: str


def validate_tmdl_indentation(content: str) -> list[TmdlIndentationError]:
    """Validate that TMDL content uses only tab indentation.

    Checks each non-empty line for leading spaces. Returns a list of errors
    for any lines that start with spaces instead of tabs.

    Args:
        content: The TMDL content to validate.

    Returns:
        List of indentation errors. Empty list if content is valid.
    """
    errors = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, start=1):
        # Skip empty lines
        if not line:
            continue

        # Check if line starts with spaces
        if line and line[0] == " ":
            # Count leading spaces
            space_count = len(line) - len(line.lstrip(" "))

            # Truncate line content to 50 chars
            truncated_line = line[:50]

            msg = (
                f"Line {line_num}: {space_count} leading space(s) detected. "
                "TMDL requires tab indentation."
            )
            error = TmdlIndentationError(
                line_number=line_num,
                message=msg,
                line_content=truncated_line,
            )
            errors.append(error)

    return errors


def indent_tmdl(level: int) -> str:
    """Generate tab indentation string for TMDL.

    Args:
        level: Indentation level (0 = no indent, 1 = one tab, etc.).

    Returns:
        String containing the appropriate number of tabs.

    Raises:
        ValueError: If level is negative.
    """
    if level < 0:
        raise ValueError("Indentation level must be non-negative")

    return "\t" * level
