# Technology Stack

**Project:** Python TMDL Semantic Model Generator for Microsoft Fabric
**Researched:** 2026-02-09
**Overall Confidence:** MEDIUM-HIGH

## Recommended Stack

### Core Language & Runtime

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python | 3.10+ | Runtime environment | Microsoft Fabric notebooks support Python 3.10 and 3.11 (default 3.11). Modern async support, match statements, and better typing. | HIGH |
| mssql-python | 1.3.0+ | SQL Server connectivity | Microsoft's official GA driver (Jan 2026) with Direct Database Connectivity (DDBC), no external driver dependencies on Windows, superior performance vs pyodbc, native Azure auth support. Token authentication for Fabric warehouses. | HIGH |

### Build & Packaging

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| hatchling | latest | Build backend | PyPA-maintained, PEP 621 compliant, recommended by Python Packaging Guide and uv. Simpler than setuptools, faster than poetry-core. Excellent plugin system. | HIGH |
| setuptools-scm | 9.2.2+ | Dynamic versioning from git tags | De facto standard for git tag versioning. Extracts version from git metadata, manages _version.py automatically. Widely adopted, stable, well-documented. | HIGH |

### Testing

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| pytest | 9.0.2+ | Test framework | 52% market share in Python testing. Superior fixture system, minimal boilerplate, 1300+ plugins. Function-based approach aligns with functional programming demand. Native assert statements, parametrization support. | HIGH |
| pytest-cov | latest | Coverage reporting | Standard pytest coverage plugin. Integrates seamlessly with pytest, generates terminal and HTML reports. | HIGH |
| pytest-mock | latest | Mocking support | Provides pytest fixtures for unittest.mock. Cleaner API than raw mocks. | MEDIUM |

### Code Quality & Linting

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| ruff | 0.15.0+ | Linter + Formatter | Replaces Black, isort, Flake8, pyupgrade, autoflake. 10-100x faster than alternatives. 800+ rules. Written in Rust. Adopted by major projects (Pandas, FastAPI, Hugging Face). Single tool = simpler toolchain. | HIGH |

### Type Checking

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| mypy | 1.19.1+ | Static type checker | Most mature Python type checker. 73% of devs use type hints now. Excellent error messages, comprehensive checks. pyright is faster but mypy has better ecosystem support. Consider ty (Astral) when reaches stable 1.0. | HIGH |

### Pre-commit Hooks

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| pre-commit | 4.5.1+ | Git hook framework | Industry standard for Python. Ensures make check runs before commit. Manages hook versioning, runs in isolated environments. | HIGH |

### HTTP Client

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| httpx | 0.28.1+ | HTTP client for Fabric REST API | Modern requests-compatible API with async support, HTTP/2, full type annotations, 100% test coverage. Better than requests (sync-only) or aiohttp (async-only). | HIGH |

### Authentication

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| azure-identity | latest | Azure authentication | Provides DefaultAzureCredential for token auth. Handles multiple auth flows (CLI, managed identity, environment, interactive). Required for Fabric warehouse token auth and REST API auth. | HIGH |

### YAML/TMDL Handling

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| ruamel.yaml | latest | YAML parsing for TMDL | YAML 1.2 compliant, preserves comments and formatting (critical for TMDL), round-trip capability. TMDL is YAML-like. Superior to PyYAML for format preservation. | MEDIUM |

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| pydantic | latest | Data validation & settings | Validate TMDL structure, configuration management, type-safe data classes with validation | MEDIUM |
| typer | latest | CLI framework (optional) | If CLI interface needed. Type-hint driven, built on Click, modern approach, auto-generates help | MEDIUM |

### Development Tools

| Tool | Purpose | Configuration Notes | Confidence |
|------|---------|---------------------|------------|
| ruff | Linting + formatting | Configured in pyproject.toml. Replaces Black+isort+Flake8. Run via `make lint` | HIGH |
| mypy | Type checking | Strict mode in pyproject.toml. Run via `make typecheck` | HIGH |
| pytest | Test execution | Test discovery in tests/. Run via `make test` | HIGH |
| pre-commit | Git hooks | `.pre-commit-config.yaml` with ruff, mypy, pytest. Run via `make check` | HIGH |

## Installation

```bash
# Core dependencies
pip install mssql-python>=1.3.0 httpx>=0.28.1 azure-identity ruamel.yaml

# Optional: Data validation and CLI
pip install pydantic typer

# Development dependencies
pip install -D pytest>=9.0.2 pytest-cov pytest-mock ruff>=0.15.0 mypy>=1.19.1 pre-commit>=4.5.1

# Build tools
pip install -D hatchling setuptools-scm
```

## pyproject.toml Configuration

```toml
[build-system]
requires = ["hatchling", "setuptools-scm"]
build-backend = "hatchling.build"

[project]
name = "semantic-model-generator"
dynamic = ["version"]
requires-python = ">=3.10"
dependencies = [
    "mssql-python>=1.3.0",
    "httpx>=0.28.1",
    "azure-identity",
    "ruamel.yaml",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.2",
    "pytest-cov",
    "pytest-mock",
    "ruff>=0.15.0",
    "mypy>=1.19.1",
    "pre-commit>=4.5.1",
]

[tool.hatch.version]
source = "vcs"

[tool.setuptools_scm]
write_to = "src/semantic_model_generator/_version.py"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]  # Core rules
extend-select = ["B", "C4", "SIM"]  # Bugbear, comprehensions, simplify

[tool.mypy]
python_version = "3.10"
strict = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing --cov-report=html"
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative | Confidence |
|----------|-------------|-------------|-------------------|------------|
| SQL Driver | mssql-python | pyodbc 5.3.0 | Requires external ODBC driver install, platform-specific behavior, slower performance | HIGH |
| SQL Driver | mssql-python | pymssql 2.3.11 | **Officially discontinued** (archived Nov 2019), despite PyPI releases continuing. Project recommends pyodbc. Lacks modern features. | HIGH |
| Type Checker | mypy | pyright | Pyright is faster but mypy has better ecosystem integration, more comprehensive checks, better documentation | MEDIUM |
| Type Checker | mypy | ty (Astral) | 10-60x faster than mypy, but **preview status** (not production-ready as of Feb 2026). Revisit when reaches 1.0. | LOW |
| Linter | ruff | Black + Flake8 + isort | Multiple tools = slower CI, complex config, maintenance overhead. Ruff replaces all with single tool. | HIGH |
| Build Backend | hatchling | poetry | Poetry lags in PEP 621 compliance, uses proprietary tool.poetry config sections, heavier tooling | MEDIUM |
| Build Backend | hatchling | setuptools | Setuptools works but more verbose config, slower builds, legacy baggage | MEDIUM |
| HTTP Client | httpx | requests | requests is sync-only, no HTTP/2, not actively developed. httpx is modern successor. | HIGH |
| HTTP Client | httpx | aiohttp | aiohttp is async-only, no sync API. httpx supports both sync/async with same API. | MEDIUM |
| YAML Library | ruamel.yaml | PyYAML | PyYAML doesn't preserve comments/formatting, YAML 1.1 only. TMDL benefits from format preservation. | MEDIUM |
| Test Framework | pytest | unittest | unittest requires classes, verbose boilerplate, weaker assertion reporting. pytest more pythonic. | HIGH |

## What NOT to Use

| Avoid | Why | Use Instead | Confidence |
|-------|-----|-------------|------------|
| pymssql | **Project discontinued** (Nov 2019), archived GitHub repo, maintainers recommend pyodbc | mssql-python | HIGH |
| AMO/TOM libraries | .NET only, no native Python bindings. Would require pythonnet/CLR bridge, adding complexity | Direct TMDL file generation + REST API | HIGH |
| microsoft-fabric-api | **Does not exist on PyPI** as of Feb 2026. Community packages (msfabricpysdkcore) exist but unsupported | httpx + direct REST API calls | HIGH |
| Black + isort + Flake8 separately | Redundant with ruff, 10-100x slower, complex multi-tool config | ruff (replaces all) | HIGH |
| setup.py for build | Legacy approach, verbose, PEP 517/518 recommend pyproject.toml | pyproject.toml + hatchling | HIGH |
| Poetry for this project | PEP 621 non-compliance, lock file overhead for library (not app), tool.poetry vendor lock-in | hatchling + pip | MEDIUM |

## Stack Patterns by Variant

**If developing inside Fabric notebook:**
- Use `%pip install` for package installation
- Validate against Python 3.11 (Fabric default)
- Azure auth via DefaultAzureCredential (picks up notebook identity automatically)
- Constrain to packages available in Fabric environment or use inline installation

**If developing as standalone CLI tool:**
- Add typer for CLI interface
- Add rich for terminal formatting
- Consider click if prefer decorator-based CLI

**If requiring C extensions in future:**
- Switch to PDM build backend (better C/C++ extension support)
- Keep hatchling's simpler config as long as pure Python

## Version Compatibility

| Package | Compatible With | Notes | Confidence |
|---------|-----------------|-------|------------|
| mssql-python 1.3.0+ | Python 3.10-3.14 | Requires Python >=3.10 | HIGH |
| pytest 9.0.2+ | Python 3.10+ | Breaking changes in 9.0, pin major version | HIGH |
| ruff 0.15.0+ | Python 3.7+ | Target Python 3.10 in config | HIGH |
| mypy 1.19.1+ | Python 3.9+ | Configure for Python 3.10 target | HIGH |
| httpx 0.28.1+ | Python 3.8+ | No compatibility issues | HIGH |
| hatchling | setuptools-scm | Compatible, both support pyproject.toml | HIGH |

## Fabric Notebook Compatibility

| Requirement | Status | Notes | Confidence |
|-------------|--------|-------|------------|
| Python 3.10+ | ✅ Supported | Fabric notebooks support 3.10 and 3.11 (default) | HIGH |
| Custom packages | ✅ Supported | Install via %pip or %conda inline commands | HIGH |
| Environment resource | ❌ Not supported | No Environment integration for Python notebooks (preview limitation) | HIGH |
| Pre-installed packages | ℹ️ Varies | DuckDB, Polars, scikit-learn pre-installed. Core deps must be installed. | MEDIUM |
| Runtime override | ❌ Not supported | Cannot override runtime packages in Fabric | MEDIUM |

## Open Questions & Limitations

### TMDL Generation Strategy

**Question:** Generate TMDL directly as text or use intermediate object model?

**Options:**
1. **Direct text generation** - Simple, no dependencies, but brittle and hard to validate
2. **Intermediate Python objects + serialization** - Type-safe, testable, but more complex
3. **AMO/TOM via pythonnet** - Authoritative but heavy (.NET dependency)

**Recommendation:** Start with option 2 (Python objects + ruamel.yaml serialization). Use Pydantic for validation. Enables functional approach with immutable data structures.

**Confidence:** MEDIUM (needs phase-specific research)

### Fabric REST API SDK

**Issue:** No official Microsoft Fabric Python SDK on PyPI (microsoft-fabric-api doesn't exist). Community packages (msfabricpysdkcore) are unsupported.

**Recommendation:** Use httpx to call Fabric REST API directly. Well-documented endpoints, type-safe with Pydantic models, no SDK lock-in.

**Trade-off:** Manual API versioning, no built-in retry logic (add httpx retries manually).

**Confidence:** MEDIUM-HIGH

### Token Authentication Flow

**Question:** How to obtain tokens for Fabric warehouse + REST API?

**Answer:** Use `azure-identity` DefaultAzureCredential:
- In Fabric notebooks: Automatically picks up notebook's managed identity
- Local development: Falls back to Azure CLI credentials
- CI/CD: Environment variables or managed identity

**Implementation:**
```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
token = credential.get_token("https://database.windows.net/.default")  # SQL
api_token = credential.get_token("https://analysis.windows.net/powerbi/api/.default")  # Fabric API
```

**Confidence:** HIGH

### TMDL Validation

**Question:** How to validate generated TMDL is correct?

**Options:**
1. Schema validation via Pydantic models
2. Deploy to test workspace and check for errors
3. Parse with ruamel.yaml and validate structure

**Recommendation:** All three - Pydantic validation during generation, YAML parsing for syntax, deployment test for semantic correctness.

**Confidence:** MEDIUM

## Sources

### Official Documentation (HIGH Confidence)
- [TMDL Overview - Microsoft Learn](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025)
- [Fabric REST API: Create Semantic Model](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/create-semantic-model)
- [mssql-python GA Announcement - Microsoft Tech Community](https://techcommunity.microsoft.com/blog/sqlserver/announcing-general-availability-of-the-mssql-python-driver/4470788)
- [Microsoft Python Driver for SQL Server - Microsoft Learn](https://learn.microsoft.com/en-us/sql/connect/python/mssql-python/python-sql-driver-mssql-python?view=sql-server-ver17)
- [Azure Identity - DefaultAzureCredential](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential?view=azure-python)
- [Python in Fabric Notebooks - Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/using-python-experience-on-notebook)

### PyPI Package Versions (HIGH Confidence)
- [pytest 9.0.2 - PyPI](https://pypi.org/project/pytest/)
- [ruff 0.15.0 - PyPI](https://pypi.org/project/ruff/)
- [mypy 1.19.1 - PyPI](https://pypi.org/project/mypy/)
- [setuptools-scm 9.2.2 - PyPI](https://pypi.org/project/setuptools-scm/)
- [httpx 0.28.1 - PyPI](https://pypi.org/project/httpx/)
- [pre-commit 4.5.1 - PyPI](https://pypi.org/project/pre-commit/)
- [mssql-python 1.3.0 - PyPI](https://pypi.org/project/mssql-python/)
- [pymssql 2.3.11 - PyPI](https://pypi.org/project/pymssql/)
- [pyodbc 5.3.0 - PyPI](https://pypi.org/project/pyodbc/)

### Tool Comparisons (MEDIUM Confidence)
- [Ruff Documentation - Astral](https://docs.astral.sh/ruff/)
- [Python Packaging Best Practices 2026 - dasroot.net](https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/)
- [Pytest vs Unittest - PyCharm Blog](https://blog.jetbrains.com/pycharm/2024/03/pytest-vs-unittest/)
- [HTTPX vs Requests vs AIOHTTP - Oxylabs](https://oxylabs.io/blog/httpx-vs-requests-vs-aiohttp)
- [pymssql vs pyodbc Performance - Microsoft Python Blog](https://devblogs.microsoft.com/python/mssql-python-vs-pyodbc-benchmarking-sql-server-performance/)
- [ruamel.yaml for Python - Top Python Libraries](https://medium.com/top-python-libraries/why-ruamel-yaml-should-be-your-python-yaml-library-of-choice-81bc17891147)

### Deprecation & Status (HIGH Confidence)
- [Pymssql Project Discontinuation - GitHub Issue #668](https://github.com/pymssql/pymssql/issues/668)
- [ty Type Checker Announcement - Astral Blog](https://astral.sh/blog/ty)

### Community & Ecosystem (MEDIUM Confidence)
- [Fabric January 2026 Feature Summary - Microsoft Fabric Blog](https://blog.fabric.microsoft.com/en-us/blog/fabric-january-2026-feature-summary?ft=All)
- [Python Type Checking: mypy vs Pyright - Medium](https://medium.com/@asma.shaikh_19478/python-type-checking-mypy-vs-pyright-performance-battle-fce38c8cb874)
- [Pre-commit Hooks Guide 2025 - Medium](https://gatlenculp.medium.com/effortless-code-quality-the-ultimate-pre-commit-hooks-guide-for-2025-57ca501d9835)

---

*Stack research for: Python TMDL Semantic Model Generator for Microsoft Fabric*
*Researched: 2026-02-09*
*Confidence: MEDIUM-HIGH (core stack HIGH, TMDL-specific patterns MEDIUM due to limited Python examples)*
