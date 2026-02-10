"""Output layer for writing TMDL files to disk."""

from semantic_model_generator.output.watermark import (
    WriteSummary,
    add_watermark_to_content,
    generate_watermark_json,
    generate_watermark_tmdl,
    is_auto_generated,
    write_file_atomically,
)

__all__ = [
    "WriteSummary",
    "add_watermark_to_content",
    "generate_watermark_json",
    "generate_watermark_tmdl",
    "is_auto_generated",
    "write_file_atomically",
]
