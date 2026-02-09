# Architecture

**Analysis Date:** 2026-02-09

## Pattern Overview

**Overall:** Multi-agent orchestrator system with decoupled specialized agents and centralized command routing

**Key Characteristics:**
- Event-driven workflow orchestration via `.claude/commands/gsd/` entry points
- Stateful project management with `.planning/` directory as source of truth
- Parallel task execution through subagent spawning
- Atomic state transitions via shared gsd-tools CLI utility
- Phase-based decomposition with wave-based execution parallelization

## Layers

**Command Layer:**
- Purpose: User-facing entry points triggering specific workflows
- Location: `.claude/commands/gsd/*.md` (41 command files)
- Contains: Markdown command definitions with argument hints, tool allowlists, execution context references
- Depends on: Workflow layer (via execution_context references)
- Used by: Claude's slash command system

**Workflow Layer:**
- Purpose: Orchestrate multi-step processes with gates, state transitions, and subagent spawning
- Location: `.claude/get-shit-done/workflows/*.md` (30 workflow files)
- Contains: Step-based processes with decision points, bash commands, Task tool spawning
- Depends on: Agent layer (spawns gsd-* agents), gsd-tools CLI, reference layer
- Used by: Command layer via execution_context

**Agent Layer:**
- Purpose: Specialized agents for focused tasks (mapping, planning, execution, verification)
- Location: `.claude/agents/gsd-*.md` (11 agent definitions)
- Contains: Role definitions, tool configurations, execution patterns
- Depends on: gsd-tools CLI, codebase files (via Read/Glob/Grep)
- Used by: Workflows via Task tool with subagent_type parameter

**Tools Layer:**
- Purpose: CLI utility for state management, phase operations, frontmatter manipulation, verification
- Location: `.claude/get-shit-done/bin/gsd-tools.js` (main tool, 52K lines)
- Contains: Commands for state load/update, git commits, phase math, verification
- Depends on: Node.js filesystem, git CLI
- Used by: All workflows and agents via `node gsd-tools.js <command>`

**Reference Layer:**
- Purpose: Documentation and reference materials for decision-making and pattern enforcement
- Location: `.claude/get-shit-done/references/*.md` (14 reference files)
- Contains: Model profile resolution, phase calculation logic, questioning patterns, TDD/UI brand guides
- Depends on: None (read-only)
- Used by: Workflows and agents for context, decision-making, and formatting

**Templates Layer:**
- Purpose: Scaffolding and starter content for planning artifacts
- Location: `.claude/get-shit-done/templates/` (codebase templates, project templates, research templates)
- Contains: Markdown templates for PLAN.md, SUMMARY.md, STATE.md, CONTEXT.md, verification reports
- Depends on: None (static)
- Used by: Workflows during project initialization and phase scaffolding

## Data Flow

**Project Initialization Flow:**

1. Command: `/gsd:new-project` invokes `new-project.md` workflow
2. Workflow: Orchestrate questioning → research → requirements → roadmap
3. State: Create `.planning/STATE.md` with project metadata
4. Roadmap: Create `.planning/ROADMAP.md` with phase breakdown
5. Artifacts: Commit to git, offer planning phase

**Phase Planning Flow:**

1. Command: `/gsd:plan-phase <phase>` invokes `plan-phase.md` workflow
2. Init: Load STATE.md, ROADMAP.md, REQUIREMENTS.md, CONTEXT.md via gsd-tools
3. Research: Spawn gsd-phase-researcher agent (if needed) → write RESEARCH.md
4. Planning: Spawn gsd-planner agent → write multiple PLAN.md files (one per plan in phase)
5. Verification: Spawn gsd-plan-checker agent → validate plans against requirements
6. Revision: If checks fail, loop back to planner with feedback (max 3 iterations)
7. Commit: gsd-tools commit command logs all plans

**Phase Execution Flow:**

1. Command: `/gsd:execute-phase <phase>` invokes `execute-phase.md` workflow
2. Discovery: Find all PLAN.md files in phase directory
3. Waves: Group plans by wave/dependency via frontmatter analysis
4. Parallel: Spawn gsd-executor agents in parallel (one per wave)
5. Execution: Each executor reads PLAN.md, executes tasks atomically with per-task commits
6. Summary: Each executor creates SUMMARY.md with results
7. State: Workflow updates STATE.md with phase progress, runs final verification
8. Verification: If plan verification fails, offer gap closure via /gsd:plan-phase --gaps

**Verification Flow:**

1. Command: `/gsd:verify-work <phase>` invokes `verify-work.md` workflow
2. Verification: Spawn gsd-verifier agent with PLAN.md, SUMMARY.md
3. Check: Verify success criteria, artifacts, commits, key links
4. Report: Create VERIFICATION.md with findings
5. Gap Analysis: If failures detected, spawn gsd-planner with gap closure flag
6. Fix Plans: Create new PLAN.md files addressing gaps
7. Commit: Plans committed, offer re-execution

**State Management:**

- **Source of Truth:** `.planning/STATE.md` (frontmatter + markdown sections)
- **State Updates:** gsd-tools `state update <field> <value>` modifies frontmatter
- **Phase Progress:** Tracked in STATE.md frontmatter (current_phase, phases_completed)
- **Decisions:** Recorded in STATE.md with phase, rationale, alternative considered
- **Blockers:** Stored as list in STATE.md, removed when resolved

## Key Abstractions

**Phase:**
- Purpose: Represents one delivery milestone
- Examples: `01-foundation`, `02-authentication`, `03-api`
- Pattern: Directory `.planning/phases/{padded}-{slug}` containing PLAN.md, SUMMARY.md, CONTEXT.md
- Lifecycle: Created during roadmap setup, planned, executed, verified, marked complete

**Plan (PLAN.md):**
- Purpose: Executable specification for one unit of work
- Examples: Multiple plans per phase (e.g., `01-01-PLAN.md`, `01-02-PLAN.md`)
- Pattern: Frontmatter metadata (phase, plan, type, wave, depends_on) + tasks with verification criteria
- Lifecycle: Created by gsd-planner, verified by gsd-plan-checker, executed by gsd-executor

**Task:**
- Purpose: Individual atomic unit of execution
- Examples: "Create database schema", "Implement login endpoint"
- Pattern: Named action in PLAN.md with type (auto, checkpoint), verification criteria, commit message
- Lifecycle: Parsed from PLAN.md, executed atomically, committed individually

**Codebase Mapper Output (.planning/codebase/):**
- Purpose: Reference documents about target codebase structure and conventions
- Examples: STACK.md, ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, INTEGRATIONS.md, CONCERNS.md
- Pattern: Filled from templates by gsd-codebase-mapper agents, loaded by planner/executor for context
- Lifecycle: Created at project start or with `/gsd:map-codebase`, refreshed as needed

**Frontmatter Metadata:**
- Purpose: Structured data in YAML front-matter for parsing and orchestration
- Examples: phase, plan, type, wave, depends_on, autonomous, tdd, gap_closure
- Pattern: YAML between `---` delimiters at document start
- Lifecycle: Set by template fill commands, read by init commands, updated by verification

## Entry Points

**Command Entry Points:**
- Location: `.claude/commands/gsd/*.md` (each a slash command)
- Pattern: `name` field defines command slug (e.g., name: "gsd:new-project" → `/gsd:new-project`)
- Triggers: User slash command invocation in Claude editor
- Responsibilities: Define allowed tools, argument hints, execution context references

**Workflow Entry Points:**
- Location: `.claude/get-shit-done/workflows/*.md`
- Triggers: Referenced by command via `execution_context` field
- Responsibilities: Multi-step orchestration with decision gates and subagent spawning

**Agent Entry Points:**
- Location: `.claude/agents/gsd-*.md`
- Triggers: Spawned by workflow via Task tool with `subagent_type="gsd-<name>"`
- Responsibilities: Execute focused role (research, planning, execution, verification)

**Tool Entry Points:**
- Location: `.claude/get-shit-done/bin/gsd-tools.js`
- Triggers: Invoked via `node gsd-tools.js <command> [args]` in workflows/agents
- Responsibilities: State mutation, git operations, phase math, file verification

## Error Handling

**Strategy:** Fail-fast with structured error messages, halt at decision gates, offer recovery paths

**Patterns:**

- **Init Failures:** Commands check preconditions (project exists? git initialized?) before starting
- **State Validation:** gsd-tools validates frontmatter structure, phase numbering consistency before mutations
- **Agent Failures:** Workflows capture agent output, re-spawn if transient, halt if persistent
- **Secret Detection:** Pre-commit scanning (grep for API key patterns) before git operations
- **Verification Failures:** Detected by gsd-plan-checker, gap closure mode creates fix plans
- **Authentication Gates:** Executor treats auth errors as checkpoints, pauses for user to authenticate

## Cross-Cutting Concerns

**Logging:** Structured bash output via commands with clear stage banners (━━━━━━━━━━━━━━━━━━━━━━━━━━━━)

**Validation:**
- Phase numbering: `gsd-tools validate consistency`
- Frontmatter: `gsd-tools frontmatter validate <file> --schema plan|summary|verification`
- References: `gsd-tools verify references <file>` checks @-refs and file paths
- Commit hashes: `gsd-tools verify commits <h1> [h2]...`

**Authentication:** Multi-channel support via CONTEXT.md decisions and checkpoint gates; executor pauses at auth errors for user input

**State Continuity:** Resume mechanisms via `<completed_tasks>` in executor prompt; session recording in STATE.md prevents loss of context

**Parallel Execution:** Wave-based grouping in execute-phase; uses `depends_on` metadata to determine safe parallelization groups

---

*Architecture analysis: 2026-02-09*
