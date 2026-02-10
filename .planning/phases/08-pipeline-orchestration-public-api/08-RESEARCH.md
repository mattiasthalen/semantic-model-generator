# Phase 8: Pipeline Orchestration & Public API - Research

**Researched:** 2026-02-10
**Domain:** Pipeline orchestration, public API design, error handling, integration testing
**Confidence:** HIGH

## Summary

Phase 8 creates the unified public API that orchestrates the full semantic model generation pipeline, tying together all previous phases (schema discovery, classification, relationship inference, TMDL generation, and output) into a single `generate_semantic_model()` function. The research confirms that Python's functional programming style with frozen dataclasses is ideal for configuration objects, and the existing codebase already has all the building blocks needed—this phase is primarily about orchestration and comprehensive error handling.

The pipeline follows a linear dependency chain: connection → schema discovery → filtering → classification → relationship inference → TMDL generation → output (either folder write or Fabric deployment). Each stage can fail independently, requiring clear error messages that identify the failing stage and provide actionable guidance. The existing codebase uses stdlib dataclasses with `frozen=True, slots=True` for immutability, which aligns perfectly with the configuration object pattern recommended by modern Python API design sources.

For integration testing, the standard pytest framework with tmp_path fixtures and mocking strategies (used throughout phases 1-7) will extend naturally to end-to-end tests. The key is testing the folder output path first (no external dependencies), then optionally adding Fabric deployment tests with appropriate mocking or test workspaces. Error handling best practices emphasize stage identification in exception messages and wrapping lower-level exceptions with context.

**Primary recommendation:** Create a frozen dataclass `PipelineConfig` for all configuration parameters, implement `generate_semantic_model()` as a pure orchestration function that calls phase-specific functions in sequence, wrap each stage in try/except blocks that add stage context to exceptions, and write integration tests using tmp_path fixtures with representative test data.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| dataclasses (stdlib) | 3.11+ | Configuration object with validation | Already used project-wide for domain types; frozen=True ensures immutability |
| typing (stdlib) | 3.11+ | Type hints for config and return types | Already used; mypy strict mode enforced project-wide |
| pathlib (stdlib) | 3.11+ | File path handling | Already used in Phase 6 output layer |
| pytest (dev) | Latest | Integration testing framework | Already used for all unit tests phases 1-7 |
| unittest.mock (stdlib) | 3.11+ | Mocking for integration tests | Already used extensively in existing tests |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Existing phase modules | - | All phase-specific functions | Pipeline calls these in sequence |
| tmp_path fixture (pytest) | - | Temporary directories for integration tests | Testing folder output mode |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Dataclass config | Dict or TypedDict | Dict lacks validation, TypedDict is runtime-unaware; dataclass provides `__post_init__` validation |
| Manual orchestration | Orchestration framework (Prefect, Dagster) | Overkill for library API; frameworks are for scheduling/monitoring, not function calls |
| Custom exception hierarchy | Re-raise stdlib exceptions | Custom exceptions provide stage context without losing original traceback |
| Pydantic dataclasses | Stdlib dataclasses | Pydantic adds external dependency; project uses stdlib-only approach (REQ-22) |

**Installation:**
```bash
# No new dependencies needed - all stdlib or already in pyproject.toml
python --version  # Ensure >= 3.11
```

## Architecture Patterns

### Recommended Project Structure
```
src/semantic_model_generator/
├── __init__.py              # UPDATE - Export generate_semantic_model and PipelineConfig
├── pipeline.py              # NEW - Orchestration and configuration
├── schema/                  # Phase 3 (connection, discovery, filtering, classification)
├── relationships.py         # Phase 4 (infer_relationships)
├── tmdl/                    # Phase 5 (generate_all_tmdl)
├── output/                  # Phase 6 (write_tmdl_folder)
└── fabric/                  # Phase 7 (deploy_semantic_model_dev/prod)

tests/
├── test_pipeline.py         # NEW - Integration tests for full pipeline
└── fixtures/                # NEW (optional) - Test data for integration tests
```

### Pattern 1: Configuration Object with Frozen Dataclass
**What:** Single configuration dataclass with all pipeline parameters, validated in `__post_init__`.
**When to use:** Public API entry point needs validated, immutable configuration.
**Example:**
```python
# Source: Project convention (Phase 2 decision: frozen=True, slots=True)
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True, slots=True, kw_only=True)
class PipelineConfig:
    """Configuration for semantic model generation pipeline.

    All parameters use kw_only to prevent positional argument errors.
    Frozen ensures immutability after construction.
    """
    # Connection parameters (Phase 3)
    sql_endpoint: str
    database: str
    schemas: tuple[str, ...]  # User must specify, no defaults

    # Filtering parameters (Phase 3)
    include_tables: tuple[str, ...] | None = None
    exclude_tables: tuple[str, ...] | None = None

    # Classification parameters (Phase 3)
    key_prefixes: tuple[str, ...]  # User must specify, no defaults

    # Model parameters (Phase 5)
    model_name: str
    catalog_name: str

    # Output parameters (Phase 6 OR Phase 7)
    output_mode: str = "folder"  # "folder" or "fabric"
    output_path: Path | None = None  # Required for folder mode
    workspace: str | None = None  # Required for fabric mode
    lakehouse_or_warehouse: str | None = None  # Required for fabric mode
    item_type: str = "Lakehouse"  # "Lakehouse" or "Warehouse"

    # Mode parameters
    dev_mode: bool = True  # Default safe iteration
    overwrite: bool = False  # Prod folder mode protection
    confirm_overwrite: bool = False  # Prod Fabric mode protection

    def __post_init__(self) -> None:
        """Validate configuration after construction."""
        if not self.schemas:
            raise ValueError("schemas cannot be empty")
        if not self.key_prefixes:
            raise ValueError("key_prefixes cannot be empty")

        # Output mode validation
        if self.output_mode not in ("folder", "fabric"):
            raise ValueError(f"output_mode must be 'folder' or 'fabric', got {self.output_mode}")

        if self.output_mode == "folder" and self.output_path is None:
            raise ValueError("output_path required when output_mode='folder'")

        if self.output_mode == "fabric" and (self.workspace is None or self.lakehouse_or_warehouse is None):
            raise ValueError("workspace and lakehouse_or_warehouse required when output_mode='fabric'")
```

### Pattern 2: Pipeline Orchestration Function
**What:** Single public function that calls phase-specific functions in sequence, wrapping each in error context.
**When to use:** User-facing API that needs to be simple and provide clear error messages.
**Example:**
```python
# Source: Error handling best practices research + project functional style
from typing import Any
from semantic_model_generator.schema import (
    create_fabric_connection,
    discover_tables,
    filter_tables,
    classify_tables,
    infer_relationships,
)
from semantic_model_generator.tmdl import generate_all_tmdl
from semantic_model_generator.output import write_tmdl_folder
from semantic_model_generator.fabric import deploy_semantic_model_dev, deploy_semantic_model_prod

class PipelineError(Exception):
    """Base exception for pipeline errors with stage context."""
    def __init__(self, stage: str, message: str, cause: Exception | None = None):
        self.stage = stage
        self.message = message
        self.cause = cause
        super().__init__(f"[{stage}] {message}")

def generate_semantic_model(config: PipelineConfig) -> dict[str, Any]:
    """Generate semantic model from Fabric warehouse metadata.

    Orchestrates the full pipeline: connect → discover → classify → infer → generate → output.

    Args:
        config: Pipeline configuration with all parameters.

    Returns:
        Result dict with keys:
        - For folder mode: {"mode": "folder", "output_path": Path, "summary": WriteSummary}
        - For Fabric mode: {"mode": "fabric", "model_id": str, "model_name": str}

    Raises:
        PipelineError: On any pipeline stage failure with stage identification.
    """
    # Stage 1: Connection
    try:
        conn = create_fabric_connection(config.sql_endpoint, config.database)
    except Exception as e:
        raise PipelineError("connection", f"Failed to connect to {config.sql_endpoint}", e) from e

    # Stage 2: Discovery
    try:
        tables = discover_tables(conn, config.schemas)
    except Exception as e:
        raise PipelineError("discovery", f"Failed to read schema for {config.schemas}", e) from e

    # Stage 3: Filtering
    try:
        filtered = filter_tables(tables, config.include_tables, config.exclude_tables)
    except Exception as e:
        raise PipelineError("filtering", "Failed to filter tables", e) from e

    # Stage 4: Classification
    try:
        classifications = classify_tables(filtered, config.key_prefixes)
    except Exception as e:
        raise PipelineError("classification", "Failed to classify tables", e) from e

    # Stage 5: Relationship inference
    try:
        relationships = infer_relationships(filtered, classifications, config.key_prefixes)
    except Exception as e:
        raise PipelineError("relationships", "Failed to infer relationships", e) from e

    # Stage 6: TMDL generation
    try:
        tmdl_files = generate_all_tmdl(
            config.model_name,
            filtered,
            classifications,
            relationships,
            config.key_prefixes,
            config.catalog_name,
        )
    except Exception as e:
        raise PipelineError("tmdl_generation", "Failed to generate TMDL", e) from e

    # Stage 7: Output
    if config.output_mode == "folder":
        try:
            summary = write_tmdl_folder(
                tmdl_files,
                config.output_path,
                config.model_name,
                config.dev_mode,
                config.overwrite,
            )
            return {"mode": "folder", "output_path": summary.output_path, "summary": summary}
        except Exception as e:
            raise PipelineError("output", f"Failed to write folder at {config.output_path}", e) from e

    else:  # fabric mode
        try:
            if config.dev_mode:
                model_id = deploy_semantic_model_dev(
                    tmdl_files, config.workspace, config.model_name
                )
            else:
                model_id = deploy_semantic_model_prod(
                    tmdl_files, config.workspace, config.model_name, config.confirm_overwrite
                )
            return {"mode": "fabric", "model_id": model_id, "model_name": config.model_name}
        except Exception as e:
            raise PipelineError("deployment", f"Failed to deploy to workspace {config.workspace}", e) from e
```

### Pattern 3: Integration Tests with tmp_path and Mocking
**What:** End-to-end tests using pytest's tmp_path fixture for folder output, mocking for database.
**When to use:** Verifying the full pipeline works with representative data.
**Example:**
```python
# Source: Existing test patterns from phases 1-7 + pytest best practices
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from semantic_model_generator.pipeline import PipelineConfig, generate_semantic_model

class TestGenerateSemanticModelFolderMode:
    """Integration tests for folder output mode."""

    def test_end_to_end_folder_output_dev_mode(self, tmp_path: Path):
        """Full pipeline with folder output creates TMDL structure."""
        # Mock the database connection and cursor
        with patch("semantic_model_generator.schema.connection.mssql_python") as mock_mssql:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_mssql.connect.return_value = mock_conn

            # Simulate schema discovery results
            mock_cursor.fetchall.return_value = [
                ("dbo", "DimCustomer", "SK_CustomerID", "bigint", "NO", 1, None, 19, 0),
                ("dbo", "DimCustomer", "Name", "varchar", "YES", 2, 100, None, None),
                ("dbo", "FactSales", "SK_CustomerID", "bigint", "NO", 1, None, 19, 0),
                ("dbo", "FactSales", "SK_DateID", "bigint", "NO", 2, None, 19, 0),
                ("dbo", "FactSales", "Amount", "decimal", "NO", 3, None, 18, 2),
            ]

            config = PipelineConfig(
                sql_endpoint="test.datawarehouse.fabric.microsoft.com",
                database="test_db",
                schemas=("dbo",),
                key_prefixes=("SK_",),
                model_name="TestModel",
                catalog_name="TestCatalog",
                output_mode="folder",
                output_path=tmp_path,
                dev_mode=True,
            )

            result = generate_semantic_model(config)

            # Verify result structure
            assert result["mode"] == "folder"
            assert result["output_path"].exists()
            assert result["summary"].written  # Some files were written

            # Verify TMDL structure was created
            output_folder = result["output_path"]
            assert (output_folder / "definition" / "database.tmdl").exists()
            assert (output_folder / "definition" / "model.tmdl").exists()
            assert (output_folder / "definition" / "tables").exists()
            assert (output_folder / ".platform").exists()

    def test_pipeline_error_includes_stage_context(self, tmp_path: Path):
        """Pipeline errors identify the failing stage."""
        config = PipelineConfig(
            sql_endpoint="invalid.endpoint",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="Test",
            catalog_name="Cat",
            output_mode="folder",
            output_path=tmp_path,
        )

        with pytest.raises(Exception) as exc_info:
            generate_semantic_model(config)

        # Error message should contain stage identifier
        assert "connection" in str(exc_info.value) or "discovery" in str(exc_info.value)
```

### Anti-Patterns to Avoid
- **Positional arguments in config:** Use `kw_only=True` to force named arguments, preventing parameter order errors
- **Mutable config:** Mutating config during pipeline execution causes debugging nightmares; use frozen dataclasses
- **Swallowing exceptions:** Always re-raise with context; silent failures are impossible to debug
- **Interactive prompts:** Library is used in notebooks; never use `input()` or interactive confirmation (REQ-35)
- **Global state:** Pipeline should be pure function of config; no module-level state

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Configuration validation | Manual if/else chains | Dataclass `__post_init__` | Built-in validation, type-safe, IDE autocomplete |
| Error context tracking | String concatenation | Exception chaining with `from e` | Preserves full traceback, standard Python pattern |
| Temporary directories | Manual cleanup with try/finally | pytest `tmp_path` fixture | Automatic cleanup, cross-platform, standard pytest pattern |
| Pipeline frameworks | Custom DAG system | Function calls in sequence | Library API needs simple orchestration, not scheduling |

**Key insight:** This phase is about gluing existing pieces together, not building new infrastructure. The orchestration is intentionally simple (linear function calls) because the pipeline has no parallelism or branching—every stage depends on the prior stage's output.

## Common Pitfalls

### Pitfall 1: Complex Configuration Validation Logic
**What goes wrong:** Validation logic scattered across multiple functions, hard to test, duplicated checks.
**Why it happens:** Each function validates its own inputs independently.
**How to avoid:** Centralize all validation in `PipelineConfig.__post_init__`, make it fail fast at construction.
**Warning signs:** Multiple ValueError exceptions from different stages for the same root cause.

### Pitfall 2: Losing Exception Context
**What goes wrong:** Re-raising exceptions without `from e` loses original traceback.
**Why it happens:** Catching generic `Exception` and raising new exception without chain.
**How to avoid:** Always use `raise NewException(...) from original_exception` to preserve traceback.
**Warning signs:** Debugging shows exception in orchestration layer but not the actual failing line in phase module.

### Pitfall 3: Testing with Real Fabric Resources
**What goes wrong:** Integration tests depend on external Fabric workspace, fail unpredictably, slow.
**Why it happens:** Temptation to test "for real" against actual API.
**How to avoid:** Mock database connection and Fabric APIs for integration tests; use tmp_path for folder output.
**Warning signs:** Tests fail in CI but pass locally, test suite takes minutes to run.

### Pitfall 4: Inconsistent Dev/Prod Mode Behavior
**What goes wrong:** Dev mode and prod mode have different error handling or validation logic.
**Why it happens:** Copy-pasted code with subtle differences between modes.
**How to avoid:** Share the core pipeline logic; only branch at the final output stage based on mode flags.
**Warning signs:** Bug reports that only occur in prod mode, or tests pass in dev but fail in prod.

### Pitfall 5: Unclear Error Messages
**What goes wrong:** User sees "ValueError: Invalid input" with no context about which parameter or stage failed.
**Why it happens:** Generic exception messages without stage or parameter identification.
**How to avoid:** Include stage name, parameter name, and actual/expected values in all error messages.
**Warning signs:** Users can't self-diagnose errors, support requests ask "what does this error mean?"

## Code Examples

Verified patterns from official sources and project conventions:

### Configuration Validation
```python
# Source: Python dataclasses docs + project convention
@dataclass(frozen=True, slots=True, kw_only=True)
class PipelineConfig:
    schemas: tuple[str, ...]
    key_prefixes: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate at construction time, fail fast."""
        if not self.schemas:
            raise ValueError("schemas cannot be empty; at least one schema required")

        if not self.key_prefixes:
            raise ValueError("key_prefixes cannot be empty; provide prefixes like ('SK_', 'ID_')")

        # Type validation happens automatically via type hints
        # Additional business logic validation here
```

### Error Wrapping with Stage Context
```python
# Source: Python exception chaining docs + error handling research
class PipelineError(Exception):
    """Pipeline error with stage identification."""
    def __init__(self, stage: str, message: str, cause: Exception | None = None):
        self.stage = stage
        self.message = message
        self.cause = cause
        super().__init__(f"[{stage}] {message}")

# Usage in pipeline
try:
    tables = discover_tables(conn, config.schemas)
except Exception as e:
    raise PipelineError(
        stage="discovery",
        message=f"Failed to read schema metadata for schemas: {config.schemas}",
        cause=e
    ) from e
```

### Integration Test with Mock Database
```python
# Source: Project test patterns (phases 3-7) + unittest.mock docs
from unittest.mock import Mock, patch

def test_pipeline_with_mock_database(tmp_path: Path):
    """Test full pipeline with mocked database connection."""
    with patch("semantic_model_generator.schema.connection.mssql_python") as mock_mssql:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_mssql.connect.return_value = mock_conn

        # Simulate database response
        mock_cursor.fetchall.return_value = [
            ("dbo", "DimCustomer", "SK_CustomerID", "bigint", "NO", 1, None, 19, 0),
        ]

        config = PipelineConfig(
            sql_endpoint="test.endpoint",
            database="test_db",
            schemas=("dbo",),
            key_prefixes=("SK_",),
            model_name="Test",
            catalog_name="Cat",
            output_mode="folder",
            output_path=tmp_path,
        )

        result = generate_semantic_model(config)

        assert result["mode"] == "folder"
        assert result["output_path"].exists()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Dict configuration | Dataclass with validation | Python 3.7+ (PEP 557) | Type safety, IDE support, validation at construction |
| Separate dev/prod functions | Unified function with mode parameter | Modern API design 2024+ | Single entry point, consistent behavior |
| Silent failures | Exception chaining with context | Python 3.0+ (`from` clause) | Debuggable errors with full traceback |
| Orchestration frameworks for libraries | Simple function calls | 2025+ library design | Lightweight, no scheduling overhead |

**Deprecated/outdated:**
- **Global configuration objects:** Modern Python uses explicit config parameters (dependency injection pattern)
- **Interactive confirmation prompts:** Notebook-unfriendly; use explicit boolean flags (REQ-35)
- **Hard-coded defaults for key prefixes/schemas:** User must provide (REQ-02, REQ-05)

## Open Questions

1. **Should we expose lower-level functions or only the unified pipeline?**
   - What we know: All phase modules already export their functions in `__init__.py`
   - What's unclear: Whether to document both high-level and low-level APIs
   - Recommendation: Keep low-level exports for advanced users, document `generate_semantic_model()` as primary API

2. **Should integration tests cover Fabric deployment or only folder output?**
   - What we know: Folder output has no external dependencies and is deterministic
   - What's unclear: Value of testing Fabric deployment vs. mocking complexity
   - Recommendation: Start with folder-only integration tests (Phase 8); Fabric tests can be optional follow-up

3. **Should we return a result dataclass or a dict?**
   - What we know: Phases 1-7 use dataclasses for structured data
   - What's unclear: Whether return type should be typed (dataclass) or flexible (dict)
   - Recommendation: Use dict for flexibility; folder and fabric modes return different shapes, Union[FolderResult, FabricResult] is awkward

## Sources

### Primary (HIGH confidence)
- Python dataclasses official docs: https://docs.python.org/3/library/dataclasses.html
- PEP 557 Data Classes: https://peps.python.org/pep-0557/
- Python exception chaining docs: https://docs.python.org/3/tutorial/errors.html
- pytest tmp_path fixture docs: https://docs.pytest.org/en/stable/how-to/tmp_path.html
- Project codebase (phases 1-7): Verified patterns for dataclasses, testing, functional style

### Secondary (MEDIUM confidence)
- [Designing Pythonic library APIs](https://benhoyt.com/writings/python-api-design/) - API design patterns
- [Pydantic vs. Python Dataclasses](https://toolshref.com/pydantic-vs-python-dataclasses-architecture/) - When to use stdlib vs Pydantic
- [Python Integration Testing Guide](https://www.lambdatest.com/learning-hub/python-integration-testing) - Integration test patterns
- [Error Handling in Data Pipelines](https://medium.com/towards-data-engineering/error-handling-and-logging-in-data-pipelines-ensuring-data-reliability-227df82ba782) - Stage identification patterns
- [Best Practices for ETL Error Handling](https://www.linkedin.com/advice/1/what-best-way-design-etl-pipelines-error-handling-clxkc) - Pipeline error strategies

### Tertiary (LOW confidence)
- Various orchestration framework docs (Prefect, Dagster, Luigi) - Informative but overkill for this use case
- [Data Pipeline Orchestration Tools 2026](https://dagster.io/learn/data-pipeline-orchestration-tools) - Industry context
- [Workflow Orchestration Patterns](https://docs.dapr.io/developing-applications/building-blocks/workflow/workflow-patterns/) - High-level patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib or existing dependencies, verified in project codebase
- Architecture: HIGH - Patterns consistent with phases 1-7, dataclass conventions established
- Pitfalls: HIGH - Common errors from pipeline design experience and error handling research

**Research date:** 2026-02-10
**Valid until:** 60 days (stable domain, standard library focus)
