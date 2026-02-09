# Project Research Summary

**Project:** Python TMDL Semantic Model Generator for Microsoft Fabric
**Domain:** Data Warehouse Semantic Modeling / Business Intelligence Automation
**Researched:** 2026-02-09
**Confidence:** MEDIUM-HIGH

## Executive Summary

This is a Python library (not a CLI) that automates TMDL semantic model generation for Microsoft Fabric warehouses, designed for use in Fabric notebooks. Research indicates this domain follows functional data pipeline patterns with pure functions, immutable data structures, and strict TDD requirements. The recommended approach uses mssql-python for warehouse connectivity with token auth, introspects INFORMATION_SCHEMA to classify tables as facts/dimensions by key count, infers star-schema relationships using key prefix patterns, and generates complete TMDL folder structures with DirectLake partitions. The library supports two output modes: write to local folder (dry run for Git workflows) or deploy directly via Fabric REST API (automation workflows).

The critical success factors are: (1) deterministic UUID generation from day one to enable Git workflows and watermark preservation, (2) whitespace-perfect TMDL generation validated by parsing, and (3) proper handling of DirectLake-specific constraints like view filtering and cross-environment data source binding. The architecture follows a functional pipeline pattern with clear separation between I/O (input/output layers) and pure transforms (schema classification, relationship inference, TMDL generation), enabling comprehensive unit testing without mocks.

Key risks include TMDL syntax violations causing silent deployment failures, non-deterministic UUIDs making Git unusable, DirectLake views causing performance fallback, and token expiration during long-running generation. All are mitigated through validation parsing, deterministic UUID generation with namespace, filtering views during schema discovery, and implementing token refresh strategies. The project sits in a unique niche: Fabric-native Python library with automated schema-driven generation plus preservation of manual edits, bridging the gap between manual tools (Tabular Editor) and enterprise platforms (AnalyticsCreator).

## Key Findings

### Recommended Stack

The stack centers on modern Python tooling with Microsoft Fabric-native components. Python 3.10+ aligns with Fabric notebook support (3.11 default). Mssql-python 1.3.0+ is critical as Microsoft's official GA driver with native Azure auth and Direct Database Connectivity, replacing deprecated pymssql and avoiding pyodbc's external driver dependencies. Hatchling provides PEP 621-compliant build backend, setuptools-scm handles dynamic versioning from git tags. Testing uses pytest 9.0.2+ (function-based approach matches functional programming requirement), code quality uses ruff (10-100x faster than Black+Flake8+isort combined), type checking uses mypy (mature ecosystem despite pyright's speed advantage). Httpx provides modern HTTP client for Fabric REST API with sync/async support, azure-identity handles token authentication, ruamel.yaml preserves TMDL formatting during round-trip parsing.

**Core technologies:**
- **mssql-python 1.3.0+**: SQL Server connectivity — Microsoft's official GA driver with native Azure token auth, no external dependencies, superior performance vs pyodbc
- **hatchling + setuptools-scm**: Build backend + versioning — PyPA-maintained, PEP 621 compliant, dynamic versioning from git tags (project requirement)
- **pytest 9.0.2+**: Test framework — Function-based approach aligns with functional programming requirement, minimal boilerplate, superior fixture system
- **ruff 0.15.0+**: Linter + formatter — Single tool replacing Black+isort+Flake8, 10-100x faster, 800+ rules, simplifies toolchain
- **httpx 0.28.1+**: HTTP client — Modern requests-compatible API with async support, full type annotations, needed for Fabric REST API
- **azure-identity**: Azure authentication — DefaultAzureCredential for token auth, handles multiple auth flows (CLI, managed identity, environment)
- **ruamel.yaml**: YAML parsing — Preserves comments and formatting (critical for TMDL round-tripping), YAML 1.2 compliant

**What NOT to use:**
- pymssql (project discontinued Nov 2019, archived)
- AMO/TOM libraries (NET only, would require pythonnet bridge)
- microsoft-fabric-api package (does not exist on PyPI as of Feb 2026)
- Black+isort+Flake8 separately (redundant with ruff, 10-100x slower)

### Expected Features

Research identifies 12 table stakes features with 9 already implemented according to requirements. The three gaps critical for v1.0 are: basic validation (relationship validity, naming conflicts), business-friendly naming (remove prefixes, snake_case to Title Case), and smart column exclusion (hide technical columns). Schema inference, fact/dimension classification, relationship inference, TMDL generation, DirectLake partitions, filtering, deterministic UUIDs, watermark preservation, dual output modes are all specified as implemented.

**Must have (table stakes):**
- Schema inference from INFORMATION_SCHEMA — implemented
- Fact/dimension classification by key count (1 key = dimension, 2+ = fact) — implemented
- Relationship inference with key matching — implemented
- TMDL folder structure generation — implemented
- DirectLake partition support — implemented
- Include/exclude table/schema filtering — implemented
- Deterministic UUID generation — implemented
- Watermark-based preservation — implemented
- Dry-run folder output mode — implemented
- REST API deployment — implemented
- Basic validation (relationship validity, naming conflicts) — **NEEDED FOR v1.0**
- Business-friendly naming (remove prefixes, transform snake_case) — **NEEDED FOR v1.0**
- Smart column exclusion (hide technical columns) — **NEEDED FOR v1.0**

**Should have (competitive differentiators):**
- Role-playing dimension support — High value but complex; defer to v1.x based on user feedback
- Relationship confidence scoring — Helps users trust automation; add after MVP validation
- Automatic measure table — Best practice but not blocking
- Semantic lineage metadata — Governance value grows with adoption
- Metadata-driven customization — Power users will request this
- Relationship naming conventions — Quality-of-life improvement

**Defer (v2+):**
- Calculation group scaffolding — Complex, requires understanding measure patterns
- Composite model support — Niche use case, DirectLake covers most scenarios
- Incremental refresh configuration — Platform may auto-configure, assess value later

**Anti-features (explicitly NOT build):**
- Automatic measure generation — Measures are business logic, auto-generation creates noise not insight
- Complex AI/ML inference — Inferring business semantics from schema alone is guesswork
- GUI configuration — Python library in notebooks means code-based config is native
- Multi-source consolidation — ETL concern, not modeling concern

### Architecture Approach

The architecture follows functional pipeline patterns with five layers: (1) Public API (single entry point with validation), (2) Pipeline Orchestration (pure functions coordinating transforms), (3) Core Transform Functions (schema read/filter, relationship inference, TMDL generation), (4) Domain Logic Functions (type mapping, key matching, table classification, watermark preservation), and (5) Output Layer (filesystem writer, Fabric REST API client). All domain logic uses pure functions with immutable data structures (frozen dataclasses), enabling comprehensive unit testing without mocks. I/O is confined to input (schema reader) and output layers (file writer, API client), with all intermediate transforms operating on in-memory data.

**Major components:**
1. **Schema Operations** (schema/) — Read INFORMATION_SCHEMA, filter tables by patterns, classify dims vs facts by key count
2. **Relationship Inference** (relationships/) — Detect relationships from key patterns, handle role-playing dimensions with base key extraction, mark first active/rest inactive
3. **TMDL Generation** (tmdl/) — Template functions for each file type (database, model, tables, relationships, expressions), pure functions taking dicts returning strings
4. **Domain Logic** (domain/) — Pure utilities: SQL→TMDL type mapping, deterministic UUID generation, summarization strategy, format string selection
5. **Output Layer** (output/) — Filesystem writer with watermark preservation, Fabric REST API client with LRO polling, dual output strategy (folder or API)
6. **Pipeline Orchestrator** (pipeline/) — Coordinates transform sequence: connect → classify → infer → generate → output

**Critical architectural decisions:**
- Functional pipeline with immutable data structures (frozen dataclasses) enables testability and parallelization
- Separation of I/O from transforms allows unit testing pure functions without database/filesystem access
- Template functions for each TMDL component enable independent testing and composition
- Watermark-based preservation requires parsing existing TMDL before regeneration
- Deterministic UUIDs use uuid.uuid5() with consistent namespace and stable input strings

### Critical Pitfalls

Research identified 12 critical/moderate pitfalls, with top 5 requiring immediate architecture-level prevention:

1. **Whitespace-Sensitive TMDL Syntax Violations** — TMDL is whitespace-sensitive with stricter rules than Python. Prevention: use single tabs consistently, validate with TMDL parser library, test roundtrip parsing. Consequences: complete deployment failure with cryptic errors. Address in Phase 1 (Core TMDL Generation).

2. **Incorrect Identifier Quoting** — Object names with special characters (`. = : ' ` or spaces) require single quotes with escaped internal quotes. Prevention: quote all identifiers with special chars, escape with double single quotes, test with schemas containing special characters. Consequences: object reference failures, silent relationship breakage. Address in Phase 1 (Core TMDL Generation).

3. **Non-Deterministic UUID Generation** — Using uuid.uuid4() instead of uuid.uuid5() makes Git unusable. Prevention: use uuid.uuid5() with consistent namespace and stable input strings, generate twice and compare byte-for-byte. Consequences: massive Git diffs, constant merge conflicts, watermark preservation impossible. Address in Phase 1 (Core TMDL Generation) — cannot be retrofitted.

4. **DirectLake Views Cause Silent DirectQuery Fallback** — Tables sourced from SQL views fall back to DirectQuery, causing 10-100x slower performance. Prevention: query INFORMATION_SCHEMA.TABLES filtering for TABLE_TYPE = 'BASE TABLE', reject views during discovery. Consequences: silent performance degradation, difficult to diagnose. Address in Phase 1 (Schema Discovery).

5. **Token Expiration During Long-Running Generation** — Entra ID tokens expire in ~1 hour, generation from large warehouses can exceed this. Prevention: implement token refresh strategy, use Azure Identity's get_token() with automatic refresh, add retry logic on 401. Consequences: deployment fails after most work complete. Address in Phase 1 (Authentication).

**Additional critical pitfalls:**
- **Embedded DAX/M Syntax Injection** — Mixing TMDL, DAX, and M syntaxes causes corruption. Always use backtick-enclosed expressions for multi-line DAX/M.
- **Inactive Relationships Ignored for Role-Playing Dimensions** — Only one relationship active, others must be `isActive: false`. Generate USERELATIONSHIP measures.
- **Deploying DirectLake Model Without Connection Reconfiguration** — DirectLake connections reference SQL endpoint by GUID, don't auto-rebind across environments.
- **Referential Integrity Violations** — Fabric Warehouse keys are metadata only, not enforced. Validate before generating relationships.
- **Missing lineageTag Preservation on Updates** — New lineageTags on every run treat updates as delete+create. Preserve existing tags.

## Implications for Roadmap

Based on research, the project has strong foundations (9/12 table stakes implemented) and needs focused phases to close gaps and add differentiators. The architecture research provides clear build order: domain functions → schema operations → relationship inference → TMDL generation → output layer → orchestration → public API. The pitfalls research flags critical items that must be addressed in Phase 1 before any features can safely deploy.

### Suggested Phase Structure

**Phase 1: Core Foundation & Validation (Weeks 1-2)**
- **Rationale:** Must establish foundational utilities before any feature work. Deterministic UUIDs cannot be retrofitted. TMDL validation prevents deployment failures. These are architectural requirements.
- **Delivers:** Domain utilities (types.py, identifiers.py, summarization.py, formatting.py), configuration system, TMDL validation with parser, deterministic UUID generation with uuid.uuid5(), consistent identifier quoting logic, token refresh strategy, view filtering.
- **Addresses:** Pitfalls 1-5 (whitespace syntax, identifier quoting, non-deterministic UUIDs, DirectLake views, token expiration).
- **Stack:** Python 3.10+, pytest with TDD, azure-identity for token refresh, ruamel.yaml for TMDL parsing.
- **Research flag:** SKIP — foundational utilities are well-documented patterns.

**Phase 2: Schema Discovery & Classification (Week 2-3)**
- **Rationale:** Schema operations provide input data for all downstream transforms. Must filter views (Pitfall 4) and validate referential integrity (Pitfall 9) during discovery.
- **Delivers:** Schema reader (INFORMATION_SCHEMA query with mssql-python), table filtering (include/exclude patterns), fact/dimension classifier (key count heuristic), schema validation (check for views, test for key duplicates/orphans).
- **Addresses:** Table stakes: schema inference, filtering, classification. Pitfall 4 (view fallback), Pitfall 9 (referential integrity).
- **Stack:** mssql-python 1.3.0+ with token auth, pytest with mock database or fixture data.
- **Research flag:** SKIP — SQL introspection is standard pattern.

**Phase 3: Relationship Inference (Week 3-4)**
- **Rationale:** Core business logic for star schema detection. Must handle role-playing dimensions (Pitfall 6) and validate relationships (Pitfall 9).
- **Delivers:** Key pattern matching (exact match, base key extraction), relationship tuple generation (from_table, from_col, to_table, to_col, is_active), role-playing dimension detection (multiple FK to same dim), inactive relationship marking (first active, rest inactive), relationship validation (duplicates on one-side, orphans on many-side).
- **Addresses:** Table stakes: relationship inference. Should have: role-playing dimension support. Pitfall 6 (inactive relationships), Pitfall 9 (referential integrity validation).
- **Stack:** Pure functions with frozen dataclasses, pytest with fixture SchemaMetadata.
- **Research flag:** MODERATE — role-playing dimension patterns are documented but implementation is complex. Consider `/gsd:research-phase` if team unfamiliar with star schema patterns.

**Phase 4: TMDL Generation (Week 4-5)**
- **Rationale:** Template functions transform metadata into TMDL syntax. Must handle whitespace (Pitfall 1), identifier quoting (Pitfall 2), and expression isolation (Pitfall 5).
- **Delivers:** Template functions for each TMDL file (database.tmdl, model.tmdl, tables/*.tmdl, relationships.tmdl, expressions.tmdl, .platform, definition.pbism), column/measure/relationship generators, DirectLake partition definitions, deterministic ordering (sort all collections), roundtrip validation (generate → parse → compare).
- **Addresses:** Table stakes: TMDL folder structure, DirectLake partitions, deterministic output. Pitfall 1 (whitespace syntax), Pitfall 2 (identifier quoting), Pitfall 5 (embedded syntax), Pitfall 12 (inconsistent ordering).
- **Stack:** ruamel.yaml for validation, deterministic UUID generation from Phase 1.
- **Research flag:** SKIP for basic templates. MODERATE if adding complex DAX expression handling.

**Phase 5: Business-Friendly Naming & Column Exclusion (Week 5-6)**
- **Rationale:** Critical gaps for v1.0 usability. Technical names and audit columns make models unusable for end users.
- **Delivers:** Name transformation (remove key prefixes, snake_case → Title Case, configurable rules), smart column exclusion (hide surrogate keys, created_by, modified_at, hash columns, ETL metadata), pattern-based detection with configurable patterns, metadata-driven customization (YAML config for naming rules and exclusion patterns).
- **Addresses:** Table stakes gaps: business-friendly naming, smart column exclusion. Should have: metadata-driven customization.
- **Stack:** Configuration dataclasses (pydantic for validation), pattern matching with regex.
- **Research flag:** SKIP — name transformation is standard ETL pattern.

**Phase 6: Validation & Error Reporting (Week 6)**
- **Rationale:** Complete the table stakes gap (basic validation) and surface confidence levels for user review.
- **Delivers:** Relationship validation (naming conflicts, reserved words, circular dependencies), relationship confidence scoring (name similarity, data type match, cardinality), validation report (warnings for low-confidence relationships, errors for invalid relationships), pre-deployment validation gate (block deployment on errors).
- **Addresses:** Table stakes gap: basic validation. Should have: relationship confidence scoring.
- **Stack:** pytest for validation logic, report generation with simple text formatting.
- **Research flag:** SKIP — validation patterns are straightforward.

**Phase 7: Output Layer & Watermark Preservation (Week 7)**
- **Rationale:** Dual output strategy enables both Git workflows (folder) and automation (API). Watermark preservation is unique differentiator requiring lineageTag handling (Pitfall 11).
- **Delivers:** Filesystem writer (create TMDL folder structure), watermark detection (parse existing files for watermark comment), lineageTag preservation (reuse existing tags for unchanged objects, generate new tags for new objects), dual output mode (folder or API), deterministic file ordering.
- **Addresses:** Table stakes: dry-run mode, watermark preservation. Pitfall 11 (lineageTag preservation).
- **Stack:** pathlib for filesystem, ruamel.yaml for parsing existing TMDL.
- **Research flag:** SKIP — watermark pattern is well-defined in requirements.

**Phase 8: Fabric REST API Deployment (Week 8)**
- **Rationale:** Enables automation workflows. Must handle concurrent operations (Pitfall 10), cross-environment binding (Pitfall 8), and LRO polling.
- **Delivers:** Fabric REST API client (POST semantic model with base64-encoded definition parts), LRO polling (poll operation status until complete), concurrent operation handling (wait before subsequent operations), connection binding API integration (resolve workspace/lakehouse GUID, update data source after cross-environment deployment), retry logic with exponential backoff.
- **Addresses:** Table stakes: REST API deployment. Pitfall 8 (cross-environment data source binding), Pitfall 10 (concurrent operations).
- **Stack:** httpx for HTTP client, azure-identity for API token, LRO polling pattern.
- **Research flag:** MODERATE — Fabric REST API has documentation but LRO polling and connection binding require careful implementation. Consider `/gsd:research-phase` for deployment pipeline patterns.

**Phase 9: Pipeline Orchestration & Public API (Week 9)**
- **Rationale:** Coordinate all phases into cohesive workflow. Public API provides single entry point with sensible defaults.
- **Delivers:** Pipeline orchestrator (call schema → classify → infer → generate → output), public API function (generate_semantic_model() with config validation), error handling (wrap exceptions with context), logging (structured logging for debugging), end-to-end integration tests.
- **Addresses:** Integration of all phases, user-facing API.
- **Stack:** All prior phases, pytest for integration tests.
- **Research flag:** SKIP — orchestration pattern is straightforward composition.

**Phase 10: Build System & CI/CD (Week 10)**
- **Rationale:** Project requirements specify make targets, pre-commit hooks, dynamic versioning. Required for developer workflow.
- **Delivers:** pyproject.toml configuration (hatchling build backend, setuptools-scm for versioning, ruff/mypy/pytest config), Makefile targets (make lint, make typecheck, make test, make check), pre-commit hook (run make check + commit message validation), CI pipeline (run make check on PR, publish to PyPI on tag).
- **Addresses:** Project requirements: make targets, pre-commit hooks, git tag versioning.
- **Stack:** hatchling, setuptools-scm, pre-commit, ruff, mypy, pytest.
- **Research flag:** SKIP — build system configuration is well-documented.

### Phase Ordering Rationale

- **Phases 1-2 establish foundation:** Domain utilities and schema operations are prerequisites for all other work. Deterministic UUIDs and TMDL validation must be in place before generating any TMDL files.
- **Phases 3-4 build core pipeline:** Relationship inference depends on schema metadata from Phase 2. TMDL generation depends on relationships from Phase 3. This is the critical path for basic functionality.
- **Phase 5 closes usability gaps:** Business naming and column exclusion transform technical output into user-friendly models. Cannot ship v1.0 without this.
- **Phase 6 adds validation:** Should be done after core generation works, to validate generated output before deployment.
- **Phases 7-8 add output modes:** Filesystem output enables Git workflows, REST API enables automation. Both depend on completed TMDL generation from Phase 4.
- **Phases 9-10 finalize product:** Orchestration ties everything together, build system enables distribution.

**Critical path dependencies:**
- Phase 1 (foundation) must complete before any other phase starts
- Phase 2 (schema) must complete before Phase 3 (relationships)
- Phase 3 (relationships) must complete before Phase 4 (TMDL)
- Phase 4 (TMDL) must complete before Phase 5 (naming), Phase 6 (validation), Phase 7 (output)
- Phase 5-7 can run in parallel (independent features)
- Phase 8 (deployment) depends on Phase 7 (output layer)
- Phase 9 (orchestration) depends on all prior phases
- Phase 10 (build) can run in parallel with Phase 9

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 3 (Relationship Inference):** MODERATE — Role-playing dimension patterns are complex, team may need research on base key extraction heuristics and inactive relationship handling. Consider `/gsd:research-phase` if unfamiliar with star schema modeling.
- **Phase 8 (Fabric REST API Deployment):** MODERATE — LRO polling patterns and connection binding API integration require careful implementation. Fabric REST API documentation is good but practical deployment patterns may need research.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Foundation):** Deterministic UUID generation, type mapping, and token refresh are well-documented patterns.
- **Phase 2 (Schema Discovery):** SQL introspection via INFORMATION_SCHEMA is standard pattern.
- **Phase 4 (TMDL Generation):** Template functions are straightforward code generation pattern.
- **Phase 5 (Naming & Exclusion):** Name transformation and pattern matching are standard ETL patterns.
- **Phase 6 (Validation):** Validation logic is straightforward business rules.
- **Phase 7 (Output Layer):** Filesystem I/O and watermark parsing are standard patterns.
- **Phase 9 (Orchestration):** Pipeline coordination is straightforward function composition.
- **Phase 10 (Build System):** Python packaging with hatchling and setuptools-scm is well-documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core technologies (mssql-python, pytest, ruff, mypy, httpx, azure-identity) verified via official docs and PyPI. TMDL handling with ruamel.yaml is MEDIUM (limited Python examples) but library is mature. |
| Features | MEDIUM | Table stakes verified with official Microsoft docs (HIGH confidence). Differentiators based on community patterns and tool observation (MEDIUM). Anti-features based on community wisdom, not official guidance (MEDIUM). |
| Architecture | HIGH | Functional pipeline patterns well-documented in data engineering literature. Component boundaries and separation of concerns are established best practices. Testability strategy is standard TDD approach. |
| Pitfalls | MEDIUM-HIGH | Critical pitfalls verified with official docs and multiple community posts (HIGH). Moderate pitfalls based on community experience (MEDIUM). Recovery strategies are inferred from general patterns (MEDIUM). |

**Overall confidence:** MEDIUM-HIGH

Research is solid for core technology choices and architecture patterns. The stack is mature and well-documented. Critical pitfalls have strong evidence from official sources and community consensus. Main uncertainty is in TMDL-specific patterns (limited Python examples, most tools use .NET) and role-playing dimension handling (complex pattern with sparse documentation). These gaps are addressed by flagging Phase 3 and Phase 8 for potential deeper research during planning.

### Gaps to Address

- **TMDL Python examples sparse:** Most TMDL tooling is .NET-based (AMO/TOM, Tabular Editor). Python examples for TMDL generation are limited. Mitigation: use ruamel.yaml for parsing/validation, test roundtrip extensively, reference official TMDL spec for syntax rules.

- **Role-playing dimension automation patterns unclear:** Limited public documentation on automated role-playing dimension detection and inactive relationship handling. Mitigation: research during Phase 3 planning, test against known role-playing scenarios (Date dimension with OrderDate/ShipDate/DueDate), validate with domain experts.

- **Fabric REST API connection binding details:** Connection binding API for cross-environment deployment is documented but practical patterns need validation. Mitigation: research during Phase 8 planning, test end-to-end Dev → Test → Prod deployment, document manual steps if full automation not achievable.

- **Watermark preservation edge cases:** Watermark pattern is unique to this implementation, not found in other tools. Edge cases (partially generated files, corrupted watermarks, manual edits to generated files) need validation. Mitigation: comprehensive testing during Phase 7, document expected behavior clearly, provide escape hatch (delete output folder to force full regeneration).

- **Token refresh strategy for long-running operations:** Token expiration handling is clear in principle but implementation details for background refresh need validation. Mitigation: test with artificial delays during Phase 1, log token expiration times for debugging, implement retry logic on 401 errors.

## Sources

### Primary (HIGH confidence)
- [TMDL Overview - Microsoft Learn](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025) — TMDL syntax, whitespace rules, identifier quoting
- [Fabric REST API: Create Semantic Model - Microsoft Learn](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/create-semantic-model) — Deployment patterns, LRO polling
- [mssql-python GA Announcement - Microsoft Tech Community](https://techcommunity.microsoft.com/blog/sqlserver/announcing-general-availability-of-the-mssql-python-driver/4470788) — Driver selection rationale
- [Direct Lake Overview - Microsoft Learn](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview) — DirectLake constraints, view fallback behavior
- [Azure Identity - DefaultAzureCredential - Microsoft Learn](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential?view=azure-python) — Token authentication patterns
- [Python in Fabric Notebooks - Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/using-python-experience-on-notebook) — Runtime environment constraints

### Secondary (MEDIUM confidence)
- [Why Power BI developers should care about TMDL - endjin](https://endjin.com/blog/2025/01/why-power-bi-developers-should-care-about-the-tabular-model-definition-language-tmdl) — TMDL code generation techniques
- [Functional Programming Paradigm for Python Pipelines - arXiv](https://arxiv.org/html/2405.16956v1) — FP pipeline architecture patterns
- [Data Pipeline Design Patterns - Start Data Engineering](https://www.startdataengineering.com/post/code-patterns/) — Metadata-driven design, composable patterns
- [Role-Playing Dimensions in Fabric DirectLake - Chris Webb's Blog](https://blog.crossjoin.co.uk/2024/09/29/role-playing-dimensions-in-fabric-directlake-semantic-models/) — Role-playing dimension patterns
- [Controlling Direct Lake Fallback Behavior - Fabric Guru](https://fabric.guru/controlling-direct-lake-fallback-behavior) — View fallback diagnostics
- [Tabular Editor TMDL Documentation](https://docs.tabulareditor.com/te3/features/tmdl.html) — TMDL tooling patterns

### Tertiary (LOW confidence, needs validation)
- [Semantic Model Best Practices for AI - Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-science/semantic-model-best-practices) — General modeling guidance
- [AnalyticsCreator Semantic Model Automation](https://www.analyticscreator.com/blog/why-a-data-warehouse-foundation-is-vital-for-power-bi) — Competitor feature analysis (marketing content)
- Community forum posts on token expiration, relationship validation, ordering issues — Practical issues verified by multiple independent reports

---
*Research completed: 2026-02-09*
*Ready for roadmap: yes*
