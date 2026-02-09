# Domain Pitfalls

**Domain:** Python TMDL Semantic Model Generator for Microsoft Fabric
**Researched:** 2026-02-09
**Confidence:** MEDIUM-HIGH

## Critical Pitfalls

Mistakes that cause rewrites, deployment failures, or major issues.

---

### Pitfall 1: Whitespace-Sensitive TMDL Syntax Violations

**What goes wrong:**
Generated TMDL fails to parse with `TmdlFormatException` due to incorrect indentation, mixed tabs/spaces, or malformed multi-line expressions. Power BI Desktop and Fabric reject the files entirely.

**Why it happens:**
TMDL is whitespace-sensitive like Python but with stricter rules. Developers treat it like JSON/XML where whitespace doesn't matter. Multi-line DAX expressions must be indented exactly one level deeper than parent properties, and all outer indentation is stripped beyond the parent object level.

**Consequences:**
- Complete deployment failure - no partial success
- Cryptic error messages that don't point to exact location
- Files appear valid visually but fail parsing
- Wasted time debugging invisible whitespace issues

**Prevention:**
- Use single tabs consistently (not spaces) for TMDL indentation
- Multi-line expressions: indent exactly one level deeper than properties
- Use backtick-enclosed expressions (`` ``` ``) when preserving exact formatting
- Run TMDL parser validation before deployment
- Test with Microsoft's TMDL parser library (available on PyPI: `tmdl-parser`)

**Warning signs:**
- `TmdlFormatException: invalid keyword or indentation` errors
- Files that look correct but fail to import
- Inconsistent serialization round-trips (write → read → write produces different output)

**Phase to address:**
Phase 1 (Core TMDL Generation) - Build validation into generation pipeline from day one. Include unit tests that parse generated TMDL.

**Sources:**
- [Tabular Model Definition Language (TMDL) | Microsoft Learn](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025)
- [TMDL Overview on GitHub](https://github.com/MicrosoftDocs/bi-shared-docs/blob/main/docs/analysis-services/tmdl/tmdl-overview.md)
- [Why Power BI developers should care about TMDL](https://endjin.com/blog/2025/01/why-power-bi-developers-should-care-about-the-tabular-model-definition-language-tmdl)

---

### Pitfall 2: Incorrect Identifier Quoting

**What goes wrong:**
Object names with special characters (dots, spaces, colons, equals signs, single quotes) cause parsing errors or reference failures. Generated TMDL uses unquoted identifiers that should be quoted, or incorrectly escapes quotes.

**Why it happens:**
TMDL requires single quotes around identifiers containing `. = : ' ` or whitespace. Internal single quotes must be escaped with double single quotes (`'Customer''s Data'`). Text properties use double quotes with different escaping rules (internal double quotes escaped with double double quotes). Developers assume quoting rules are the same across identifier contexts.

**Consequences:**
- Object reference failures: "refers to an object which cannot be found"
- Silent failures where relationships reference wrong objects
- Inconsistent behavior between valid-looking and actually-valid references
- Deployment succeeds but semantic model is broken

**Prevention:**
- Quote all table/column/measure names that contain special characters: `. = : ' ` or spaces
- Escape internal single quotes: `'Customer''s Data'` for apostrophes
- For text properties (descriptions, display folders): use double quotes, escape with `""`
- Use fully qualified references for clarity: `column: 'Table 1'.'Column 1'`
- Build quoting logic as reusable function, tested independently

**Warning signs:**
- "Object not found" errors during deployment
- Relationships appear in TMDL but don't work in reports
- Measures reference columns but show #ERROR
- Compare original column names to TMDL - mismatches indicate quoting issues

**Phase to address:**
Phase 1 (Core TMDL Generation) - Build robust identifier quoting as foundational utility. Test with warehouse schemas containing special characters.

**Sources:**
- [Tabular Model Definition Language (TMDL) | Microsoft Learn](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025)
- [TMDL Syntax on GitHub](https://github.com/MicrosoftDocs/bi-shared-docs/blob/main/docs/analysis-services/tmdl/tmdl-overview.md)
- [Community: TMDL refers to an object which cannot be found](https://community.fabric.microsoft.com/t5/Desktop/TMDL-refers-to-an-object-which-cannot-be-found/m-p/4711826)

---

### Pitfall 3: Non-Deterministic UUID Generation

**What goes wrong:**
Every generation run produces different UUIDs for objects even when semantically identical. Git shows massive diffs. Deployments always appear as "changes" even when nothing functionally changed. Merge conflicts become impossible to resolve.

**Why it happens:**
Using `uuid.uuid4()` (random) instead of `uuid.uuid5()` (deterministic, hash-based). Each run generates fresh random UUIDs. TMDL requires unique IDs for objects but doesn't enforce determinism - the generator must.

**Consequences:**
- Git becomes unusable - every generation is a complete rewrite
- Cannot detect actual semantic changes
- Deployment pipelines always trigger unnecessary updates
- Collaboration impossible - constant merge conflicts
- Watermark/lineageTag preservation fails - treated as new objects
- Lost ability to track model evolution over time

**Prevention:**
- Use `uuid.uuid5()` with consistent namespace UUID and stable input strings
- Input string format: `f"{workspace_id}:{table_name}:{object_type}:{object_name}"`
- Generate namespace UUID once per project, commit to config
- For existing objects from API: preserve their UUIDs explicitly (watermark preservation)
- Test: generate twice, compare outputs byte-for-byte - must be identical
- Document UUID generation strategy in code

**Warning signs:**
- Every Git commit shows 100% file changes in TMDL
- Deployment always shows "all objects modified"
- Cannot identify actual model changes in PR reviews
- lineageTag values change on every run

**Phase to address:**
Phase 1 (Core TMDL Generation) - Deterministic UUIDs are architectural requirement. Cannot be retrofitted easily. Watermark preservation in Phase 2 depends on this foundation.

**Sources:**
- [UUID Generator: Complete Guide](https://dev.to/hardik_b2d8f0bca/uuid-generator-the-complete-guide-to-universally-unique-identifiers-566d) (LOW confidence - general UUID guidance, not Fabric-specific)
- Project context requirement (deterministic UUIDs explicitly mentioned)

---

### Pitfall 4: DirectLake Views Cause Silent DirectQuery Fallback

**What goes wrong:**
Semantic model appears to be DirectLake but queries are slow. Performance analysis reveals fallback to DirectQuery mode. Root cause: tables sourced from SQL views instead of Delta tables.

**Why it happens:**
Fabric Warehouse/SQL Analytics Endpoint supports both tables and views. Generator connects via SQL, introspects schema, treats views like tables. DirectLake **cannot** use views - queries fall back to DirectQuery per-query execution through SQL engine, bypassing VertiPaq.

**Consequences:**
- 10-100x slower query performance vs. true DirectLake
- Capacity guardrails different for DirectQuery (more restrictive)
- Users complain about slow reports but model appears configured correctly
- Difficult to diagnose - requires Performance Analyzer or SQL Profiler
- DirectQuery fallback consumes more capacity units
- Silent failure - no error, just degraded performance

**Prevention:**
- Query Fabric system tables to distinguish views from tables
- SQL: `SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'`
- Reject views during discovery, or warn users explicitly
- Alternatively: document that views will cause DirectQuery fallback
- For complex queries: recommend creating gold Delta tables via notebooks/pipelines
- Add validation: test model's DirectLakeBehavior property after deployment
- Monitor: query performance metrics to detect fallback in production

**Warning signs:**
- Query Performance Analyzer shows "Storage Engine" = "DirectQuery" instead of "VertipaqSE"
- Slow report loads for small data volumes
- Capacity metrics show high SQL Analytics Endpoint usage
- Users report inconsistent performance (fallback is query-specific)

**Phase to address:**
Phase 1 (Schema Discovery) - Filter out views during introspection. Phase 3 (Validation) - Add post-deployment checks for fallback behavior.

**Sources:**
- [Direct Lake overview | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview)
- [Controlling Direct Lake Fallback Behavior](https://fabric.guru/controlling-direct-lake-fallback-behavior)
- [Leveraging pure Direct Lake mode for maximum query performance](https://powerbi.microsoft.com/en-us/blog/leveraging-pure-direct-lake-mode-for-maximum-query-performance/)
- [Develop Direct Lake semantic models](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-develop)

---

### Pitfall 5: Embedded DAX/M Syntax Injection in TMDL

**What goes wrong:**
Generated TMDL appears valid but contains DAX syntax inside TMDL properties or TMDL syntax inside DAX expressions. Parser accepts it but semantic model is corrupt or measures don't execute.

**Why it happens:**
TMDL files contain **three or more different syntaxes**: TMDL metadata, DAX expressions, Power Query (M) expressions, and potentially annotations. LLMs and naive generators confuse syntax contexts - emitting DAX keywords in TMDL sections or TMDL indentation inside DAX strings. Multi-line expressions use backticks (`` ``` ``) for verbatim content, but developers forget to use them or misunderstand scope.

**Consequences:**
- Measures compile but produce wrong results
- Expressions fail at query time with cryptic DAX errors
- Parser accepts file but semantic model is invalid
- Very difficult to debug - syntax looks "close enough"
- Lost trust in generated output

**Prevention:**
- Treat DAX/M expressions as opaque strings - never parse or modify them
- Always use backtick-enclosed expressions (`` ``` ``) for multi-line DAX/M
- Use template engines carefully - escape sequence conflicts (e.g., Jinja `{{ }}` in DAX)
- Test with complex DAX: CALCULATE, FILTER, variables, comments, quoted identifiers
- Validate: attempt to evaluate each measure in isolation after deployment
- Code review: manually inspect generated DAX in TMDL - should be unchanged from source

**Warning signs:**
- Measures show #ERROR in reports after successful deployment
- DAX expressions contain TMDL keywords (`column:`, `measure =`, `formatString:`)
- Multi-line expressions don't preserve original formatting
- Comments in DAX expressions cause parsing errors

**Phase to address:**
Phase 1 (Core TMDL Generation) - Treat expressions as opaque. Phase 2 (DAX Generation) if generating measures - isolate DAX generation completely from TMDL serialization.

**Sources:**
- [Tabular Model Definition Language (TMDL)](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025)
- [AI agents that work with TMDL files](https://tabulareditor.com/blog/ai-agents-that-work-with-tmdl-files)
- [Why Power BI developers should care about TMDL](https://endjin.com/blog/2025/01/why-power-bi-developers-should-care-about-the-tabular-model-definition-language-tmdl)

---

### Pitfall 6: Inactive Relationships Ignored for Role-Playing Dimensions

**What goes wrong:**
Role-playing dimensions (e.g., Date table related to OrderDate, ShipDate, DueDate) appear in model but only one relationship works. Other date columns produce blank values or wrong aggregations.

**Why it happens:**
Only one relationship between two tables can be active. Additional relationships must be `isActive: false`. Generator creates all relationships as active, TOM/Fabric silently marks extras as inactive, but doesn't communicate which. Developers forget to generate `isActive` property. DAX measures must use `USERELATIONSHIP()` for inactive relationships, but generator doesn't create these measures or document which relationships are inactive.

**Consequences:**
- Silent data errors - wrong dates in aggregations
- Only first relationship works, others appear in model but don't filter
- Users confused why "ShipDate" slicer doesn't filter measures
- Requires manual DAX measures per inactive relationship
- Documentation gap - users don't know which relationships are inactive

**Prevention:**
- Explicitly generate `isActive: false` for role-playing dimension relationships
- Document strategy: first relationship active, subsequent inactive (or use heuristic: most recent date field active)
- Generate helper measures for inactive relationships: `Sales by Ship Date =: CALCULATE([Sales], USERELATIONSHIP(...))`
- In TMDL comments, document which relationships are active/inactive and why
- Validate: post-deployment, query relationship catalog and verify active/inactive status matches intent
- Consider generating separate dimension tables if user prefers (memory tradeoff vs. complexity)

**Warning signs:**
- Multiple relationships between Date and Fact tables all show `isActive: true`
- Deployment succeeds but Power BI shows some relationships as inactive
- Measures return wrong values when filtering by certain date columns
- No USERELATIONSHIP measures for inactive relationships

**Phase to address:**
Phase 2 (Relationships) - Handle role-playing dimensions explicitly. Phase 2 (DAX Measures) if generating measures - create USERELATIONSHIP wrappers.

**Sources:**
- [Welcome to Power BI theatre: Role-Playing Dimensions!](https://data-mozart.com/welcome-to-powerbi-thetare-role-playing-dimensions/)
- [Role playing dimensions and USERELATIONSHIP](https://community.fabric.microsoft.com/t5/Desktop/role-playing-dimensions-and-USERELATIONSHIP/td-p/3402810)
- [Multiple Role-Playing Dimension and RLS](https://community.fabric.microsoft.com/t5/Desktop/Multiple-Role-Playing-Dimension-and-RLS/td-p/4326752)

---

### Pitfall 7: Token Expiration During Long-Running Generation

**What goes wrong:**
Generator starts successfully, introspects schema, generates TMDL, but fails during deployment with authentication error. Error message: "Token expired" or "Unauthorized".

**Why it happens:**
Entra ID OAuth tokens expire in ~1 hour. Generation from large warehouses can take 30+ minutes. Token acquired at start is expired by deployment time. Most mssql-python examples show token acquired once at connection time and reused.

**Consequences:**
- Deployment fails after most work is complete
- Wasted computation and time
- Non-deterministic failures (works for small schemas, fails for large)
- Difficult to reproduce in testing (small test schemas complete quickly)
- Users blame Fabric API instability, not token lifetime

**Prevention:**
- Implement token refresh strategy: acquire new token before API calls if current token TTL < 5 minutes
- Use Azure Identity library's `get_token()` with automatic refresh
- For long-running operations: background thread refreshes token every 30 minutes
- Separate token for SQL connection vs. REST API - refresh independently
- Add retry logic: if 401 Unauthorized, refresh token and retry once
- Test with artificial delay: `time.sleep(3600)` before deployment to verify token refresh works
- Log token expiration times for debugging

**Warning signs:**
- Intermittent failures on large warehouses, success on small ones
- Errors correlate with execution time > 60 minutes
- "Token expired" or 401 errors during deployment phase
- Success rate degrades over time in long-running notebooks

**Phase to address:**
Phase 1 (Authentication) - Build token refresh into authentication layer. All API clients should use refreshable token source, not static token.

**Sources:**
- [Token expiry issues refreshing a semantic model](https://community.fabric.microsoft.com/t5/Service/Token-expiry-issues-refreshing-a-semantic-model/m-p/3811479)
- [Semantic model is failing to refresh](https://community.fabric.microsoft.com/t5/Service/Semantic-model-is-failing-to-refresh/m-p/4780837)
- [Power BI Error: Refresh token expired](https://community.fabric.microsoft.com/t5/Service/Power-BI-Error-Refresh-token-expired/m-p/3507454)

---

### Pitfall 8: Deploying DirectLake Model Without Connection Reconfiguration

**What goes wrong:**
Semantic model deploys successfully to Fabric workspace but shows errors when opened. Reports display "Cannot connect to data source". Model still references source environment's SQL endpoint GUID instead of target environment.

**Why it happens:**
DirectLake connection strings reference SQL Analytics Endpoint by **GUID**, not friendly name. Deploying TMDL across environments (Dev → Test → Prod) doesn't automatically rebind data sources. Fabric deployment pipelines have limited support for DirectLake semantic models - data source deployment rules "currently not supported for semantic models created in Direct Lake OneLake mode."

**Consequences:**
- Model deployed but unusable
- Data source points to wrong environment (Test model queries Dev warehouse)
- Requires manual reconfiguration in Fabric UI per deployment
- Breaks CI/CD automation goals
- Model appears in workspace but all queries fail

**Prevention:**
- Generate connection strings with parameterized endpoint GUIDs
- Use Fabric REST API for connection binding: POST to update data source after deployment
- For cross-environment: query target workspace to resolve lakehouse/warehouse GUID before deployment
- Alternative: use Fabric Git integration + deployment rules (when supported for DirectLake)
- Test deployment end-to-end: Dev → Test workspace, verify model queries correct warehouse
- Document manual reconfiguration steps if full automation not achievable
- Consider generating environment-specific TMDL files with correct GUIDs pre-baked

**Warning signs:**
- Successful deployment response but model shows errors in UI
- Lineage view shows model connected to wrong lakehouse
- Queries fail with "Cannot connect to data source"
- Model refresh fails immediately after deployment

**Phase to address:**
Phase 3 (Deployment) - Handle cross-environment data source binding. Phase 1 should generate parameterized connection strings to enable Phase 3 reconfiguration.

**Sources:**
- [Data Source Deployment Rules for Semantic Models](https://community.fabric.microsoft.com/t5/Fabric-platform/Data-Source-Deployment-Rules-for-Semantic-Models-in-Direct-Lake/m-p/4802247)
- [Deploy a working Direct Lake semantic model with fabric-cicd](https://www.kevinrchant.com/2025/08/18/deploy-a-working-direct-lake-semantic-model-with-fabric-cicd-and-fabric-cli/)
- [Announcing a new Fabric REST API for connection binding](https://powerbi.microsoft.com/en-us/blog/announcing-a-new-fabric-rest-api-for-connection-binding-of-semantic-models/)

---

## Moderate Pitfalls

Mistakes that cause technical debt or require workarounds.

### Pitfall 9: Referential Integrity Violations from Unvalidated Relationships

**What goes wrong:**
Generated relationships look correct in model but reports show unexpected (Blank) rows or error messages. Slicers don't filter as expected.

**Why it happens:**
DirectLake models have limited validation. Keys in Fabric Data Warehouse/SQL Analytics Endpoint are **not enforced** - primary/foreign keys are metadata only. Generator assumes warehouse enforces constraints and creates relationships blindly. If dimension table has duplicates in key column or fact table has orphaned foreign keys, relationships appear valid but produce errors at query time.

**Prevention:**
- Query data to validate relationships before generating TMDL:
  - Check for duplicates in "one" side: `SELECT key_column, COUNT(*) ... GROUP BY ... HAVING COUNT(*) > 1`
  - Check for orphans in "many" side: `SELECT COUNT(*) FROM fact WHERE fk NOT IN (SELECT pk FROM dim)`
- Generate warnings/errors if violations found: "Cannot create relationship due to X duplicates"
- Option: generate with `assumeReferentialIntegrity: true` if data is clean (improves performance)
- Document validation results: "Relationship created. Warning: 47 orphaned rows will show as (Blank)"
- Consider adding data quality checks as prerequisite to generation

**Warning signs:**
- Reports show (Blank) category for numeric measures
- Visuals display error: "Can't display the data because relationships have duplicate values"
- Slicers fail to filter fact tables
- Different visuals show inconsistent totals

**Phase to address:**
Phase 2 (Relationships) - Validate before generating. Phase 3 (Validation) - Post-deployment smoke tests can catch this.

**Sources:**
- [Direct Lake relationships - duplicates, null values](https://community.fabric.microsoft.com/t5/Fabric-platform/Direct-Lake-relationships-duplicates-null-values-assume/m-p/3627839)
- [Validate semantic model relationships](https://tabulareditor.com/blog/validate-semantic-model-relationships)
- [Create semantic model relationships](https://tabulareditor.com/blog/create-semantic-model-relationships)

---

### Pitfall 10: Fabric REST API Concurrent Operation Conflicts

**What goes wrong:**
Deployment succeeds but subsequent refresh triggers "operation already in progress" error. Pipeline retries fail. Manual refresh shows error: "Another operation is running."

**Why it happens:**
Fabric REST API rejects concurrent operations on same semantic model. Deployment triggers automatic refresh. Generator attempts to trigger refresh immediately after deployment before prior operation completes. API returns 400 error with unclear message.

**Prevention:**
- After deployment POST, poll GET operation status before triggering refresh
- Use Fabric operation status API: check `status` field until "Succeeded" or "Failed"
- Implement exponential backoff: wait 5s, 10s, 20s, 40s between status checks
- Respect Retry-After header if provided in 429/503 responses
- For pipelines: use native "Semantic Model Refresh" activity with built-in conflict handling
- Document expected wait times: "Initial deployment may take 2-5 minutes"
- Add `--wait` flag to CLI: block until deployment complete before returning

**Warning signs:**
- Deployment succeeds but refresh fails with "operation in progress"
- Intermittent failures when running generator repeatedly
- 400 Bad Request errors with unhelpful error messages
- Success on first run, failures on subsequent rapid runs

**Phase to address:**
Phase 3 (Deployment) - Implement polling and retry logic. Phase 4 (CLI) - Expose wait/polling options to users.

**Sources:**
- [Reliably refreshing a Semantic Model from Microsoft Fabric Pipelines](https://endjin.com/blog/2025/10/refresh-semantic-model-fabric-pipelines)
- [Semantic Model Auto Refresh After Failure](https://azurepocmain.github.io/fabricpocmain.github.io/articles/semantic-model-auto-refresh-after-failure.html)
- [Fabric Data Factory Spotlight: Semantic model refresh activity](https://thedataarchdesk.com/fabric-data-factory-spotlight-semantic-model-refresh-activity/)

---

### Pitfall 11: Missing lineageTag Preservation on Updates

**What goes wrong:**
Updating existing semantic model treats all objects as new. Power BI loses history, downstream dependencies break, deployment pipelines fail to recognize objects.

**Why it happens:**
Each TMDL object has a `lineageTag` (UUID) that identifies it across versions. Generator creates new lineageTags on every run instead of preserving existing ones. Power BI uses lineageTags to track object identity - new tags mean "deleted old object, created new object" instead of "updated existing object."

**Prevention:**
- Before generating: GET existing semantic model definition via REST API
- Parse existing TMDL: extract lineageTag for each table/column/measure
- During generation: reuse lineageTag if object name matches existing object
- Only generate new lineageTag for truly new objects
- Use deterministic UUID generation (Pitfall 3) for new objects
- Test: update existing model, verify lineageTags unchanged for unmodified objects
- Document strategy in code: "Watermark preservation via lineageTag matching"

**Warning signs:**
- Every deployment shows "all objects deleted, all objects created"
- Power BI deployment pipeline Compare view shows 100% changes
- Downstream reports break after "update" (treated as deletion + recreation)
- Cannot deploy incrementally - always full replacement

**Phase to address:**
Phase 2 (Updates) - Requires GET before PUT pattern. Depends on deterministic UUID generation from Phase 1.

**Sources:**
- [Items - Update Semantic Model Definition | REST API](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/update-semantic-model-definition)
- [Items - Get Semantic Model | REST API](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/get-semantic-model)
- Project context requirement (watermark preservation explicitly mentioned)

---

### Pitfall 12: Inconsistent Table/Column Ordering Across Generations

**What goes wrong:**
Git diffs show table/column order changes even when no semantic changes occurred. Large diffs obscure actual changes. Merge conflicts frequent.

**Why it happens:**
TMDL serializer uses default ordering unless specified. Generator iterates schema in database query order (non-deterministic) or Python dict iteration order (insertion order, not alphabetical). Tables appear in different order in `model.tmdl` across runs.

**Prevention:**
- Sort tables alphabetically before generating TMDL: `sorted(tables, key=lambda t: t.name)`
- Sort columns within each table
- Sort measures, relationships, and all collections consistently
- Use `ref` keyword in TMDL to preserve explicit collection ordering
- Test: generate twice from same schema, diff outputs - should be identical
- Consider semantic ordering: fact tables before dimensions, or dimension → fact for readability

**Warning signs:**
- Git diffs show table reordering but no content changes
- PR reviews difficult - hard to spot actual changes
- Merge conflicts in `model.tmdl` even when teams work on different tables

**Phase to address:**
Phase 1 (Core TMDL Generation) - Deterministic ordering is foundational. Sort all collections before serialization.

**Sources:**
- [Ordering of tables in model.tmdl · Issue #1195](https://github.com/TabularEditor/TabularEditor/issues/1195)
- [TMDL format with object level granularity · Discussion #1198](https://github.com/TabularEditor/TabularEditor3/discussions/1198)

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hard-code workspace GUIDs in connection strings | Faster to implement | Cannot deploy to other environments without manual editing | Never - defeats automation purpose |
| Generate all relationships as active | Simpler logic | Role-playing dimensions broken, silent data errors | Never - breaks common pattern |
| Skip TMDL validation parsing | Faster generation | Production failures, wasted debugging time | Only in early prototyping |
| Use random UUIDs instead of deterministic | Easier implementation | Git unusable, watermark preservation impossible | Never for production code |
| Assume warehouse enforces referential integrity | No validation queries needed | Silent relationship errors in reports | Only if warehouse has enforced constraints |
| Single token acquisition at startup | Simpler auth code | Token expiration failures on long-running jobs | Only for schemas completing in <30 min |
| Generate TMDL without roundtrip test | Faster test suite | Discover parsing errors in production | Early prototyping only |
| Ignore DirectLake fallback scenarios | Simpler model generation | Poor performance, confused users | Never - fallback is silent |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Fabric Warehouse mssql-python | Using `https://analysis.windows.net/powerbi/api/.default` scope | Use `https://api.fabric.microsoft.com/.default` for Fabric or validate both scopes work |
| Fabric REST API authentication | Reusing SQL connection token for REST API | Acquire separate token for REST API with correct scope |
| SQL Analytics Endpoint connection | Referencing by friendly name | Use GUID from workspace item metadata |
| DirectLake data source | Querying views and tables equally | Filter out views - they cause DirectQuery fallback |
| Token authentication with pyodbc | Passing token string directly | Convert to UTF-8 bytes, encode to Windows format, pass via `SQL_COPT_SS_ACCESS_TOKEN` |
| Concurrent API operations | Firing refresh immediately after deployment | Poll operation status until complete before next operation |
| Cross-environment deployment | Assuming data sources rebind automatically | Use connection binding REST API to update source after deployment |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous SQL queries for large schemas | Generator hangs, timeouts | Use pagination, async queries, or batch introspection | >1000 tables or >100k total columns |
| Loading entire semantic model into memory | Out of memory errors | Stream TMDL file generation, write incrementally | Models >1GB serialized TMDL |
| Single-threaded table processing | Slow generation for large warehouses | Parallelize table introspection and TMDL generation | >100 tables |
| No caching of warehouse schema | Repeated queries on every run | Cache schema metadata, invalidate on change | >500 tables or frequent runs |
| Generating DAX measures for all metric combinations | Exponential measure growth | Generate core measures, use calculation groups | >10 fact tables with >5 time dimensions each |
| Full model regeneration on every change | Slow feedback loop | Incremental updates - only regenerate changed objects | Models >50 tables |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Hardcoding Entra ID client secrets in code | Credential exposure in Git | Use Azure Key Vault or managed identity |
| Logging Fabric REST API responses with tokens | Token leakage in logs | Redact tokens before logging, use token fingerprints |
| Storing generated TMDL with embedded credentials | Credential exposure | TMDL connections use token auth, never embed passwords |
| Using same service principal for all environments | Dev credentials access Prod data | Separate service principals per environment |
| Not validating connection string parameters | SQL injection in server name | Validate/sanitize all user-provided connection parameters |
| Exposing workspace/item GUIDs as secrets | Over-securing non-sensitive IDs | GUIDs are not secrets - focus on tokens/keys |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **TMDL Generation:** Generated files parse with TMDL parser, not just "look right"
- [ ] **Identifier Quoting:** Tested with schemas containing `.`, `=`, `:`, `'`, spaces in names
- [ ] **UUID Determinism:** Verified byte-for-byte identical output on repeated generation
- [ ] **Token Refresh:** Tested with artificial delay >60 min to verify refresh logic works
- [ ] **DirectLake Views:** Filtered out during schema discovery, or explicit warning shown
- [ ] **Relationship Validation:** Checked for duplicates (one-side) and orphans (many-side)
- [ ] **Inactive Relationships:** Explicitly set `isActive: false` for role-playing dimensions
- [ ] **Cross-Environment Deployment:** Tested Dev → Test → Prod with different workspace GUIDs
- [ ] **Concurrent Operation Handling:** Implemented polling before triggering subsequent operations
- [ ] **Watermark Preservation:** lineageTags preserved for existing objects on updates
- [ ] **Expression Isolation:** DAX/M expressions treated as opaque, never modified/parsed
- [ ] **Error Handling:** REST API errors logged with correlation IDs for debugging
- [ ] **Deterministic Ordering:** Collections sorted consistently for clean Git diffs
- [ ] **Roundtrip Testing:** Generated TMDL → deserialize → serialize → compare to original

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Whitespace parsing errors | LOW | Run TMDL parser to identify exact location, fix indentation, regenerate |
| Incorrect identifier quoting | MEDIUM | Parse error messages for object names, add quoting logic, regenerate |
| Non-deterministic UUIDs | HIGH | Rewrite UUID generation logic, accept one-time large Git diff, document |
| DirectLake view fallback | MEDIUM | Create gold Delta tables from views, update generator filter, regenerate |
| Embedded syntax confusion | MEDIUM | Use backtick expressions, isolate DAX generation, regenerate affected objects |
| Missing inactive relationships | LOW | Manually edit TMDL to add `isActive: false`, or regenerate with fixed logic |
| Token expiration mid-run | LOW | Implement token refresh, rerun generator from checkpoint if available |
| Wrong data source after deployment | LOW | Use connection binding API to update, or regenerate with correct GUID |
| Referential integrity violations | HIGH | Fix warehouse data quality issues, regenerate relationships with validation |
| Concurrent operation conflicts | LOW | Wait for operation completion, retry deployment/refresh |
| Lost lineageTags on update | HIGH | No recovery - downstream dependencies broken, treat as fresh deployment |
| Inconsistent ordering | LOW | Implement sorting, accept one-time Git diff, enforce in CI |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Whitespace-sensitive syntax | Phase 1: Core TMDL Generation | Parse with TMDL parser library in unit tests |
| Identifier quoting | Phase 1: Core TMDL Generation | Test with special characters in schema |
| Non-deterministic UUIDs | Phase 1: Core TMDL Generation | Generate twice, byte-compare outputs |
| DirectLake view fallback | Phase 1: Schema Discovery | Query INFORMATION_SCHEMA.TABLES for TABLE_TYPE |
| Embedded syntax confusion | Phase 1: Expression Handling | Roundtrip test with complex DAX/M expressions |
| Inactive relationships | Phase 2: Relationship Generation | Validate isActive property in generated TMDL |
| Token expiration | Phase 1: Authentication | Test with 60+ minute artificial delay |
| Wrong data source after deploy | Phase 3: Deployment | Test cross-environment deployment |
| Referential integrity violations | Phase 2: Relationship Validation | Query for duplicates/orphans before relationship creation |
| Concurrent operation conflicts | Phase 3: Deployment | Poll operation status before subsequent calls |
| Lost lineageTags | Phase 2: Update Operations | Compare lineageTags before/after update |
| Inconsistent ordering | Phase 1: Core TMDL Generation | Git diff on repeated generation - verify no order changes |

---

## Sources

### Official Documentation (HIGH Confidence)
- [Tabular Model Definition Language (TMDL) | Microsoft Learn](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview?view=sql-analysis-services-2025)
- [Direct Lake overview | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview)
- [Develop Direct Lake semantic models | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-develop)
- [Items - Update Semantic Model Definition | REST API](https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/update-semantic-model-definition)
- [Warehouse Connectivity | Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-warehouse/connectivity)

### Official GitHub and Extensions (HIGH Confidence)
- [TMDL Overview on GitHub](https://github.com/MicrosoftDocs/bi-shared-docs/blob/main/docs/analysis-services/tmdl/tmdl-overview.md)
- [Microsoft TMDL Parser on GitHub](https://github.com/microsoft/tmdl-parser)

### Official Blogs and Announcements (MEDIUM-HIGH Confidence)
- [Leveraging pure Direct Lake mode for maximum query performance](https://powerbi.microsoft.com/en-us/blog/leveraging-pure-direct-lake-mode-for-maximum-query-performance/)
- [Announcing a new Fabric REST API for connection binding](https://powerbi.microsoft.com/en-us/blog/announcing-a-new-fabric-rest-api-for-connection-binding-of-semantic-models/)

### Community Expert Blogs (MEDIUM Confidence)
- [Why Power BI developers should care about TMDL | endjin](https://endjin.com/blog/2025/01/why-power-bi-developers-should-care-about-the-tabular-model-definition-language-tmdl)
- [Controlling Direct Lake Fallback Behavior | Fabric Guru](https://fabric.guru/controlling-direct-lake-fallback-behavior)
- [Reliably refreshing a Semantic Model from Microsoft Fabric Pipelines | endjin](https://endjin.com/blog/2025/10/refresh-semantic-model-fabric-pipelines)
- [Deploy a working Direct Lake semantic model with fabric-cicd | K Chant](https://www.kevinrchant.com/2025/08/18/deploy-a-working-direct-lake-semantic-model-with-fabric-cicd-and-fabric-cli/)
- [Connect to Microsoft Fabric Warehouse using Python and SQLAlchemy | Medium](https://medium.com/@mariusz_kujawski/connect-to-microsoft-fabric-warehouse-using-python-and-sqlalchemy-1e1179855037)
- [All the different ways to authenticate to Azure SQL, Synapse, and Fabric | Sam Debruyn](https://debruyn.dev/2025/all-the-different-ways-to-authenticate-to-azure-sql-synapse-and-fabric/)

### Microsoft Fabric Community (MEDIUM Confidence - Multiple Corroborating Posts)
- [Data Source Deployment Rules for Semantic Models](https://community.fabric.microsoft.com/t5/Fabric-platform/Data-Source-Deployment-Rules-for-Semantic-Models-in-Direct-Lake/m-p/4802247)
- [Token expiry issues refreshing a semantic model](https://community.fabric.microsoft.com/t5/Service/Token-expiry-issues-refreshing-a-semantic-model/m-p/3811479)
- [Direct Lake relationships - duplicates, null values](https://community.fabric.microsoft.com/t5/Fabric-platform/Direct-Lake-relationships-duplicates-null-values-assume/m-p/3627839)
- [Role playing dimensions and USERELATIONSHIP](https://community.fabric.microsoft.com/t5/Desktop/role-playing-dimensions-and-USERELATIONSHIP/td-p/3402810)

### Tabular Editor Community (MEDIUM Confidence)
- [AI agents that work with TMDL files](https://tabulareditor.com/blog/ai-agents-that-work-with-tmdl-files)
- [Validate semantic model relationships](https://tabulareditor.com/blog/validate-semantic-model-relationships)
- [Create semantic model relationships](https://tabulareditor.com/blog/create-semantic-model-relationships)

### GitHub Issues (MEDIUM Confidence - Specific Technical Issues)
- [Ordering of tables in model.tmdl · Issue #1195](https://github.com/TabularEditor/TabularEditor/issues/1195)
- [Power BI Desktop can't open TMDL from TE: Parsing error](https://github.com/TabularEditor/TabularEditor/issues/1185)

---

*Pitfalls research for: Python TMDL Semantic Model Generator for Microsoft Fabric*
*Researched: 2026-02-09*
*Domain: DirectLake Semantic Model Generation for Fabric Data Warehouse*
