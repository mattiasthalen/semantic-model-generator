"""TMDL folder writer with dev/prod modes and watermark preservation."""

from datetime import UTC, datetime
from pathlib import Path

from semantic_model_generator.output.watermark import (
    WriteSummary,
    add_watermark_to_content,
    is_auto_generated,
    write_file_atomically,
)


def get_output_folder(
    base_path: Path,
    model_name: str,
    dev_mode: bool = True,
    timestamp: str | None = None,
) -> Path:
    """Get output folder path with dev/prod mode support.

    Args:
        base_path: Base output directory
        model_name: Model name (case and spaces preserved)
        dev_mode: If True, appends timestamp suffix; if False, uses base name
        timestamp: Optional explicit timestamp in format "YYYYMMDDTHHMMSSz" (for testing).
                   If None and dev_mode=True, generates current UTC timestamp.

    Returns:
        Path to output folder

    Examples:
        >>> get_output_folder(Path("/out"), "My Model", dev_mode=True, timestamp="20260210T120000Z")
        Path("/out/My Model_20260210T120000Z")

        >>> get_output_folder(Path("/out"), "My Model", dev_mode=False)
        Path("/out/My Model")
    """
    if dev_mode:
        if timestamp is None:
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return base_path / f"{model_name}_{timestamp}"

    return base_path / model_name


def write_tmdl_folder(
    files: dict[str, str],
    output_path: Path,
    model_name: str,
    dev_mode: bool = True,
    overwrite: bool = False,
    version: str | None = None,
    timestamp: str | None = None,
) -> WriteSummary:
    """Write TMDL files to disk with dev/prod mode and watermark preservation.

    Writes all files from the dict to a folder structure compatible with Fabric.
    Files are watermarked to identify auto-generated content. Existing files
    without watermarks are preserved (manually maintained). Files with watermarks
    are overwritten on regeneration.

    Args:
        files: Dictionary mapping relative paths to file content
        output_path: Base output directory
        model_name: Model name for folder creation
        dev_mode: If True (default), creates timestamped folder; if False, uses base name
        overwrite: If True in prod mode, allows overwriting existing folder
        version: Version string for watermark (if None, uses package version)
        timestamp: Explicit timestamp for deterministic output (if None, uses current UTC)

    Returns:
        WriteSummary with lists of written, skipped, and unchanged files

    Raises:
        FileExistsError: In prod mode when folder exists and overwrite=False
    """
    # Step 1: Determine output folder
    folder_path = get_output_folder(output_path, model_name, dev_mode, timestamp)

    # Step 2: Handle prod mode overwrite protection
    if not dev_mode and folder_path.exists() and not overwrite:
        raise FileExistsError(
            f"Output folder '{folder_path}' already exists. "
            f"Pass overwrite=True to overwrite, or use dev mode for safe iteration."
        )

    # Step 3: Create output directory structure
    folder_path.mkdir(parents=True, exist_ok=True)
    (folder_path / "definition").mkdir(exist_ok=True)
    (folder_path / "definition" / "tables").mkdir(exist_ok=True)

    # Step 4: Get version for watermark
    if version is None:
        from semantic_model_generator._version import __version__

        version = __version__

    # Step 5: Process each file in the dict
    written: list[str] = []
    skipped: list[str] = []
    unchanged: list[str] = []

    for relative_path, content in files.items():
        full_path = folder_path / relative_path
        watermarked_content = add_watermark_to_content(relative_path, content, version, timestamp)

        if not full_path.exists():
            # New file: write it
            write_file_atomically(full_path, watermarked_content)
            written.append(relative_path)
        else:
            # Existing file: check watermark and content
            existing = full_path.read_text(encoding="utf-8")

            if existing == watermarked_content:
                # Byte-identical: skip writing
                unchanged.append(relative_path)
            elif is_auto_generated(existing):
                # Has watermark: overwrite
                write_file_atomically(full_path, watermarked_content)
                written.append(relative_path)
            else:
                # No watermark (manually maintained): preserve
                skipped.append(relative_path)

    # Step 6: Return WriteSummary
    return WriteSummary(
        written=tuple(sorted(written)),
        skipped=tuple(sorted(skipped)),
        unchanged=tuple(sorted(unchanged)),
        output_path=folder_path,
    )
