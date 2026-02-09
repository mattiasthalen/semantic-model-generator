"""TMDL identifier quoting and unquoting.

TMDL requires identifiers containing special characters (spaces, dots, equals, colons,
single quotes) to be wrapped in single quotes. Internal single quotes are escaped by doubling.
"""

import re


def quote_tmdl_identifier(identifier: str) -> str:
    """Quote a TMDL identifier if it contains special characters.

    Special characters that trigger quoting:
    - Whitespace (spaces, tabs, newlines, etc.)
    - Dot (.)
    - Equals (=)
    - Colon (:)
    - Single quote (')

    When quoting is needed:
    - Wrap identifier in single quotes
    - Escape internal single quotes by doubling them

    Args:
        identifier: The identifier to potentially quote.

    Returns:
        The identifier, quoted if necessary.

    Raises:
        ValueError: If identifier is empty.
    """
    if not identifier:
        raise ValueError("Identifier cannot be empty")

    # Check if quoting is needed (any special character present)
    needs_quoting = re.search(r"[\s.=:']", identifier) is not None

    if not needs_quoting:
        return identifier

    # Escape internal single quotes by doubling them
    escaped = identifier.replace("'", "''")

    # Wrap in single quotes
    return f"'{escaped}'"


def unquote_tmdl_identifier(identifier: str) -> str:
    """Unquote a TMDL identifier that was previously quoted.

    Removes outer single quotes and unescapes doubled internal quotes.
    If identifier has no quotes, returns it unchanged.

    Args:
        identifier: The identifier to unquote.

    Returns:
        The unquoted identifier.

    Raises:
        ValueError: If identifier is empty.
    """
    if not identifier:
        raise ValueError("Identifier cannot be empty")

    # If no outer quotes, return unchanged
    if not (identifier.startswith("'") and identifier.endswith("'")):
        return identifier

    # Remove outer quotes
    unquoted = identifier[1:-1]

    # Unescape doubled single quotes
    return unquoted.replace("''", "'")
