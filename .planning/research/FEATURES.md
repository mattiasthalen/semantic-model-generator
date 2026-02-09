# Feature Landscape

**Domain:** TMDL/Semantic Model Generator for Microsoft Fabric
**Researched:** 2026-02-09
**Confidence:** MEDIUM

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Schema inference from metadata** | Standard pattern - all semantic model generators read source schema to build models | LOW | Read INFORMATION_SCHEMA.COLUMNS from Fabric warehouse (already implemented) |
| **Fact/dimension classification** | Core star schema requirement - users expect automatic detection of table types | MEDIUM | Key-based classification (1 key = dimension, 2+ = fact) is standard heuristic (already implemented) |
| **Relationship inference** | Manual relationship creation is time-consuming; automation is expected | MEDIUM | Key matching across tables with naming convention support (already implemented) |
| **TMDL folder structure generation** | Standard TMDL output format required for compatibility | LOW | database.tmdl, model.tmdl, tables/, relationships.tmdl, expressions.tmdl (already implemented) |
| **DirectLake partition support** | Default mode for Fabric warehouse semantic models; not supporting this = broken for primary use case | MEDIUM | DirectLake on SQL mode with proper parquet reference (already implemented) |
| **Business-friendly naming** | Technical names (snake_case, prefixes) must convert to business names | MEDIUM | Column/table name transformation, removing technical artifacts |
| **Basic validation** | Schema errors caught before deployment prevent failed refreshes | MEDIUM | Relationship validity, naming conflicts, reserved words, circular dependencies |
| **Dry-run mode** | Users need to preview generated model before deployment | LOW | Folder output mode (already implemented) |
| **Deployment to Fabric** | Manual deployment is friction; push via API expected | MEDIUM | REST API integration with proper authentication (already implemented) |
| **Include/exclude table filtering** | Not all tables belong in semantic model; selective inclusion expected | LOW | Table list configuration (already implemented) |
| **Schema filtering** | Multi-schema warehouses need per-schema control | LOW | Schema list configuration (already implemented) |
| **Deterministic output** | Regeneration must not cause false diffs in source control | MEDIUM | Stable object IDs, consistent ordering (already implemented with deterministic UUIDs) |

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Role-playing dimension support** | Handles date/dimension reuse (OrderDate, ShipDate, etc.) - rare in auto-generators | HIGH | Detect multiple FK references to same dimension, create inactive relationships with proper naming |
| **Watermark-based preservation** | Allows manual edits alongside automation - most tools are regenerate-everything | HIGH | Preserve content between watermarks during regeneration (already implemented) |
| **Python library (not CLI)** | Embeddable in Fabric notebooks = native workflow for Fabric users | LOW | Already implemented; differentiator vs standalone tools |
| **Metadata-driven customization** | JSON/YAML config for naming rules, relationship hints, custom properties | MEDIUM | External config file defines transformations, overrides, business rules |
| **Relationship confidence scoring** | Flag uncertain inferred relationships for review | MEDIUM | Score relationships by name similarity, data type match, cardinality; surface low-confidence for validation |
| **Automatic measure table** | Separate measures from facts (best practice often skipped in auto-generation) | LOW | Create dedicated measure table, move all measures there |
| **Smart column exclusion** | Auto-hide technical columns (IDs, audit fields, ETL metadata) | MEDIUM | Pattern-based detection: surrogate keys, created_by, modified_at, hash columns, etc. |
| **Calculation group scaffolding** | Generate time intelligence or other calc group templates | HIGH | Pre-built calc groups for common patterns (YTD, MTD, YoY, etc.) - requires understanding of user's measures |
| **Semantic lineage metadata** | Embed source table/column mappings in descriptions for traceability | LOW | Add lineage info to TMDL descriptions: "Source: warehouse.schema.table.column" |
| **Relationship naming conventions** | Readable relationship names vs default "Table1_Table2" | LOW | Name relationships descriptively: "FactSales_to_DimDate_OrderDate" |
| **Composite model support** | Mix DirectLake with import/DirectQuery for hybrid scenarios | HIGH | Allow some tables to be import mode (e.g., for calculated tables or external sources) |
| **Incremental refresh configuration** | Generate incremental refresh policies for large fact tables | MEDIUM | Detect date columns, configure RangeStart/RangeEnd parameters, set policies |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Automatic measure generation** | Measures are business logic - auto-generation creates noise (SUM everything) not insight | Document measure patterns; provide measure templates users can adapt |
| **Complex AI/ML inference** | Inferring business semantics (hierarchies, display folders, measure logic) from schema alone = guesswork | Use simple heuristics; let users configure via metadata |
| **GUI configuration** | Python library in notebooks = code-based config is native; GUI adds complexity | YAML/JSON config files + Python API |
| **Schema migration** | Changing source schema = different domain; not a generator's job | Regenerate from new schema; watermarks preserve manual work |
| **Full DAX optimization** | DAX performance tuning requires context (data volume, cardinality, usage patterns) | Generate naive DAX; provide Best Practice Analyzer integration hooks |
| **Multi-source consolidation** | Joining data from multiple warehouses/databases = ETL concern, not modeling | Assume single warehouse; ETL upstream should consolidate |
| **Real-time refresh orchestration** | Refresh scheduling = platform concern (Fabric pipelines) | Generate model; let Fabric handle refresh |
| **Custom visual generation** | Report layer concern, not semantic model | Stop at semantic model; users build reports |
| **Automatic RLS (Row-Level Security)** | Security rules = business logic requiring deep domain knowledge | Provide RLS scaffolding/templates; users fill in logic |
| **Automatic object-level security** | Same as RLS - security policy requires business understanding | Scaffold roles structure; users configure permissions |

## Feature Dependencies

```
Schema Inference (base)
    └──> Fact/Dimension Classification
            └──> Relationship Inference
                    └──> Role-Playing Dimension Support (requires multiple relationships)
    └──> Column Exclusion (requires schema understanding)
    └──> Business-Friendly Naming (operates on schema)

TMDL Folder Generation (base)
    └──> Deterministic Output (requires consistent TMDL serialization)
    └──> Watermark Preservation (requires parsing existing TMDL)
    └──> DirectLake Partitions (requires partition definition in TMDL)

Validation (base)
    └──> Relationship Confidence Scoring (subset of validation)

Deployment to Fabric
    └──> Validation (must validate before deploy)

Metadata-Driven Customization
    └──> enhances ALL features (naming, relationships, exclusions, etc.)

Calculation Group Scaffolding
    └──conflicts with──> Simple Measure Generation (both address measure patterns, but calc groups are better)
```

### Dependency Notes

- **Schema Inference is foundational**: All classification, naming, and relationship features depend on understanding the source schema first
- **Role-playing dimensions require relationship inference**: Can't detect role-playing until relationships are inferred
- **Watermark preservation requires TMDL parsing**: Must read existing TMDL to identify preserved sections
- **Validation gates deployment**: Should never deploy invalid models
- **Metadata config is cross-cutting**: Can influence naming, relationships, classification, exclusions

## MVP Recommendation

### Launch With (v1.0)

Based on existing implementation and table stakes analysis:

- [x] Schema inference from INFORMATION_SCHEMA
- [x] Fact/dimension classification (key-based)
- [x] Relationship inference with key matching
- [x] TMDL folder structure generation
- [x] DirectLake partition support
- [x] Include/exclude table/schema filtering
- [x] Deterministic UUID generation
- [x] Watermark-based preservation
- [x] Dry-run folder output mode
- [x] REST API deployment
- [ ] **Basic validation** (relationship validity, naming conflicts)
- [ ] **Business-friendly naming** (remove prefixes, snake_case → Title Case)
- [ ] **Smart column exclusion** (hide technical columns)

**Rationale**: These 12 features (9 done + 3 needed) constitute a complete, production-ready tool. Validation prevents bad deployments. Naming makes models usable. Column exclusion makes models clean.

### Add After Validation (v1.x)

Once core is validated by users:

- [ ] **Role-playing dimension support** — High value but complex; users can manually adjust v1 output
- [ ] **Relationship confidence scoring** — Helps users trust/verify automation
- [ ] **Automatic measure table** — Best practice but not blocking
- [ ] **Semantic lineage metadata** — Governance value grows with adoption
- [ ] **Metadata-driven customization** — Power users will request this
- [ ] **Relationship naming conventions** — Quality-of-life improvement

**Triggers for adding:**
- Role-playing dimensions: User feedback shows manual adjustment is pain point
- Confidence scoring: Users report uncertainty about auto-generated relationships
- Measure table: Users adopt tool widely, want to enforce best practices
- Lineage metadata: Governance/auditing requirements emerge
- Metadata config: Multiple users want different conventions
- Relationship naming: Source control diffs show relationship churn

### Future Consideration (v2+)

Defer until product-market fit established and usage patterns understood:

- [ ] **Calculation group scaffolding** — Complex; requires understanding measure patterns
- [ ] **Composite model support** — Niche use case; DirectLake covers most scenarios
- [ ] **Incremental refresh configuration** — Platform handles this; may not be needed

**Why defer:**
- Calculation groups: High complexity, unclear if users want scaffolding vs manual control
- Composite models: Limited demand; DirectLake + import hybrid is edge case
- Incremental refresh: Fabric may auto-configure; need to assess if manual config is valuable

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Basic validation | HIGH | MEDIUM | **P1** |
| Business-friendly naming | HIGH | MEDIUM | **P1** |
| Smart column exclusion | HIGH | MEDIUM | **P1** |
| Role-playing dimension support | HIGH | HIGH | P2 |
| Relationship confidence scoring | MEDIUM | MEDIUM | P2 |
| Automatic measure table | MEDIUM | LOW | P2 |
| Semantic lineage metadata | MEDIUM | LOW | P2 |
| Metadata-driven customization | HIGH | MEDIUM | P2 |
| Relationship naming conventions | LOW | LOW | P2 |
| Calculation group scaffolding | MEDIUM | HIGH | P3 |
| Composite model support | LOW | HIGH | P3 |
| Incremental refresh configuration | LOW | MEDIUM | P3 |

**Priority key:**
- **P1**: Must have for v1.0 launch (closes critical gaps in current implementation)
- **P2**: Should have for v1.x (user-driven based on feedback/usage)
- **P3**: Nice to have for v2+ (defer until patterns emerge)

## Competitor Feature Analysis

| Feature | Tabular Editor | AnalyticsCreator | Power BI MCP Server | Our Approach |
|---------|---------------|------------------|---------------------|--------------|
| **Schema inference** | Manual (user builds model) | Automatic from DWH | Manual (user builds model) | **Automatic from Fabric warehouse** |
| **TMDL generation** | Full support (create/edit) | Generates semantic model + TMDL | Full support (create/edit) | **Generate from schema** |
| **Relationship inference** | Manual definition | Automatic from metadata | Manual definition | **Automatic from keys** |
| **Role-playing dimensions** | Manual setup | Not documented | Manual setup | **Target: Automatic detection** |
| **Watermark preservation** | N/A (manual tool) | N/A (full regeneration) | N/A (manual tool) | **Unique: Preserve manual edits** |
| **DirectLake support** | Full support | Full support | Full support | **Full support** |
| **Python library** | .NET API (C#) | Desktop app + CLI | Node.js MCP | **Python (native to Fabric notebooks)** |
| **Deployment** | XMLA/TMSL/REST | Integrated deployment | XMLA/REST | **REST API** |
| **Validation** | Best Practice Analyzer | Built-in validation | N/A | **Target: Schema-based validation** |
| **Metadata config** | UI + scripting | Central metadata model | N/A | **Target: YAML/JSON config** |

**Key Differentiators vs Competitors:**

1. **Tabular Editor**: We automate what they require manual work for (schema → model). They're a model *editor*, we're a model *generator*.

2. **AnalyticsCreator**: Enterprise tool generating full DWH + semantic model. We're lightweight, single-purpose (semantic model only), and Python-native for Fabric notebooks.

3. **Power BI MCP Server**: AI agent integration for model manipulation. We focus on schema-driven generation, not AI-assisted editing.

**Our niche**: Fabric-native, Python-based, schema-driven semantic model generation with preservation of manual edits. Bridges gap between "build everything manually" and "enterprise metadata-driven platform."

## Key Insights from Research

### What's Standard (Must Match)

1. **Star schema assumption**: All semantic model tools assume dimensional modeling (facts + dimensions)
2. **TMDL as lingua franca**: TMDL is the standard format; all tools read/write it
3. **DirectLake as default**: Fabric semantic models use DirectLake unless there's a reason not to
4. **Relationship inference from keys**: FK → PK matching is standard heuristic
5. **Business-friendly naming**: Technical names must be cleaned for end users

### What's Rare (Opportunity)

1. **Preservation of manual edits**: Most tools regenerate everything or require full manual work
2. **Role-playing dimension auto-detection**: Complex feature rarely automated
3. **Python library for notebooks**: Most tools are desktop apps or CLI, not notebook-embeddable
4. **Confidence scoring for relationships**: Most tools present inferred relationships as-is without uncertainty flags

### What's Complex (Avoid)

1. **Measure generation**: Business logic inference is guesswork; generates noise
2. **Semantic inference**: Hierarchies, display folders, formats require business knowledge
3. **Multi-source models**: ETL concern, not modeling concern
4. **Security auto-generation**: RLS/OLS rules = business policy, not schema pattern

## Sources

**Official Microsoft Documentation:**
- [TMDL Overview - Microsoft Learn](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview) - HIGH confidence
- [Power BI Semantic Models in Fabric - Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-warehouse/semantic-models) - HIGH confidence
- [Direct Lake Overview - Microsoft Learn](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview) - HIGH confidence
- [TMDL View in Power BI Desktop - Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-tmdl-view) - HIGH confidence
- [Incremental Refresh Overview - Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/connect-data/incremental-refresh-overview) - HIGH confidence
- [Understand Star Schema - Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema) - HIGH confidence
- [Semantic Model Validation - Microsoft Learn](https://learn.microsoft.com/en-us/power-bi/guidance/powerbi-implementation-planning-content-lifecycle-management-validate) - HIGH confidence

**Microsoft Blog Posts (Recent):**
- [Power BI Modeling MCP Server - GitHub](https://github.com/microsoft/powerbi-modeling-mcp) - MEDIUM confidence (preview feature)
- [TMDL View Generally Available - Power BI Blog](https://powerbi.microsoft.com/en-us/blog/tmdl-view-generally-available/) - HIGH confidence
- [Fabric January 2026 Feature Summary - Fabric Blog](https://blog.fabric.microsoft.com/en-US/blog/fabric-january-2026-feature-summary/) - HIGH confidence
- [Service Principal Support in Semantic Link - Fabric Blog](https://blog.fabric.microsoft.com/en-us/blog/service-principal-support-in-semantic-link-enabling-scalable-secure-automation/) - MEDIUM confidence
- [Fabric REST API for Semantic Models - Power BI Blog](https://powerbi.microsoft.com/en-us/blog/announcing-a-new-fabric-rest-api-for-connection-binding-of-semantic-models/) - HIGH confidence

**Community & Tool Documentation:**
- [Tabular Editor TMDL Documentation](https://docs.tabulareditor.com/te3/features/tmdl.html) - HIGH confidence
- [AnalyticsCreator Semantic Model Automation](https://www.analyticscreator.com/blog/why-a-data-warehouse-foundation-is-vital-for-power-bi) - MEDIUM confidence (marketing content)
- [Role-Playing Dimensions Best Practices - Data Mozart](https://data-mozart.com/welcome-to-powerbi-thetare-role-playing-dimensions/) - MEDIUM confidence
- [Role-Playing Dimensions in Fabric DirectLake - Chris Webb's Blog](https://blog.crossjoin.co.uk/2024/09/29/role-playing-dimensions-in-fabric-directlake-semantic-models/) - MEDIUM confidence
- [Power BI Semantic Model Checklist - Data Goblins](https://data-goblins.com/dataset-checklist) - MEDIUM confidence

**Research & Patterns:**
- [Semantic Model Best Practices for AI - Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-science/semantic-model-best-practices) - HIGH confidence
- [Power BI Copilot Best Practices 2026 - MAQ Software](https://maqsoftware.com/insights/power-bi-copilot-best-practices.html) - LOW confidence (not verified)
- [Data Lineage and Governance - Select Star](https://www.selectstar.com/resources/data-lineage-data-governance) - LOW confidence (general governance, not Power BI specific)

---

**Research confidence: MEDIUM**

**Rationale**: High confidence on table stakes (verified with official docs), medium confidence on differentiators (mix of community patterns and tool observation), low-to-medium confidence on some anti-features (based on community wisdom, not official guidance). Did not find comprehensive public examples of automated semantic model generators with full feature lists - most tools are either manual (Tabular Editor) or enterprise/proprietary (AnalyticsCreator).

**Gaps identified:**
- Limited public documentation on role-playing dimension automation patterns
- No standard for relationship confidence scoring (appears to be novel)
- Watermark preservation pattern not found in other tools (may be unique to this implementation)
- Calculation group scaffolding patterns not well-documented for automation

---

*Feature research for: Python TMDL Semantic Model Generator for Microsoft Fabric*
*Researched: 2026-02-09*
