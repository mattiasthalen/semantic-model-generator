"""Output layer for writing TMDL files to disk."""

from semantic_model_generator.output.watermark import (
    WriteSummary,
    add_watermark_to_content,
    generate_watermark_json,
    generate_watermark_tmdl,
    is_auto_generated,
    write_file_atomically,
)
from semantic_model_generator.output.writer import (
    get_output_folder,
    write_tmdl_folder,
)

__all__ = [
    "WriteSummary",
    "add_watermark_to_content",
    "generate_watermark_json",
    "generate_watermark_tmdl",
    "get_output_folder",
    "is_auto_generated",
    "write_file_atomically",
    "write_tmdl_folder",
]
