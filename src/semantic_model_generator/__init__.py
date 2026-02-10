"""semantic-model-generator: Generate TMDL semantic models from Fabric warehouse metadata.

This package provides tools to automatically create deployable Tabular Model Definition Language
(TMDL) semantic models from Microsoft Fabric warehouse schemas, with intelligent dimension/fact
classification and star-schema relationship inference.
"""

from importlib.metadata import PackageNotFoundError, version

from semantic_model_generator.pipeline import (
    PipelineConfig,
    PipelineError,
    generate_semantic_model,
)

try:
    __version__ = version("semantic-model-generator")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__: list[str] = [
    "__version__",
    "PipelineConfig",
    "PipelineError",
    "generate_semantic_model",
]
