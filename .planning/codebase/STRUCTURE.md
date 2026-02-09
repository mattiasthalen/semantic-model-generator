# Codebase Structure

**Analysis Date:** 2026-02-09

## Directory Layout

```
.claude/
├── agents/                          # Agent role definitions (11 specialized agents)
│   ├── gsd-codebase-mapper.md       # Maps target codebase, writes STACK/ARCH/CONVENTIONS/etc
│   ├── gsd-debugger.md              # Debugs failing plans
│   ├── gsd-executor.md              # Executes PLAN.md files with atomic commits
│   ├── gsd-integration-checker.md   # Validates external integrations
│   ├── gsd-phase-researcher.md      # Researches phase implementation approaches
│   ├── gsd-plan-checker.md          # Validates PLAN.md structure and feasibility
│   ├── gsd-planner.md               # Creates executable PLAN.md files
│   ├── gsd-project-researcher.md    # Initial research for project setup
│   ├── gsd-research-synthesizer.md  # Synthesizes research into actionable insights
│   ├── gsd-roadmapper.md            # Creates ROADMAP.md from requirements
│   └── gsd-verifier.md              # Verifies executed work against success criteria
├── commands/
│   └── gsd/                         # User-facing slash commands (41 commands)
│       ├── map-codebase.md          # /gsd:map-codebase — analyze target codebase
│       ├── new-project.md           # /gsd:new-project — initialize project
│       ├── plan-phase.md            # /gsd:plan-phase — create phase plans
│       ├── execute-phase.md         # /gsd:execute-phase — run phase plans
│       ├── verify-work.md           # /gsd:verify-work — verify execution
│       ├── add-phase.md             # /gsd:add-phase — add phase to roadmap
│       ├── progress.md              # /gsd:progress — show project progress
│       ├── quick.md                 # /gsd:quick — fast iteration mode
│       └── [37 more commands]       # Other operations (phase mgmt, todos, debugging)
├── get-shit-done/
│   ├── bin/
│   │   ├── gsd-tools.js             # CLI utility for state, git, phase operations (52K lines)
│   │   └── gsd-tools.test.js        # Unit tests for gsd-tools commands
│   ├── references/                  # Documentation and decision references
│   │   ├── model-profiles.md        # Models for each agent role
│   │   ├── model-profile-resolution.md  # How to pick correct model
│   │   ├── phase-argument-parsing.md    # Parse phase numbers (1, 2.1, etc)
│   │   ├── decimal-phase-calculation.md # Math for nested phases
│   │   ├── planning-config.md       # Config schema for .planning/config.json
│   │   ├── git-integration.md       # Git branching and commit patterns
│   │   ├── questioning.md           # Deep questioning protocol
│   │   ├── tdd.md                   # Test-driven development patterns
│   │   ├── ui-brand.md              # UI styling and brand guidelines
│   │   ├── verification-patterns.md # Verification and testing patterns
│   │   ├── checkpoints.md           # Checkpoint protocol for long plans
│   │   ├── continuation-format.md   # Resume/continuation format
│   │   └── [more references]        # Other decision docs
│   ├── templates/
│   │   ├── codebase/                # Templates for codebase analysis
│   │   │   ├── stack.md             # STACK.md template
│   │   │   ├── integrations.md      # INTEGRATIONS.md template
│   │   │   ├── architecture.md      # ARCHITECTURE.md template
│   │   │   ├── structure.md         # STRUCTURE.md template
│   │   │   ├── conventions.md       # CONVENTIONS.md template
│   │   │   ├── testing.md           # TESTING.md template
│   │   │   └── concerns.md          # CONCERNS.md template
│   │   ├── config.json              # Project config template
│   │   ├── state.md                 # STATE.md template
│   │   ├── roadmap.md               # ROADMAP.md template
│   │   ├── phase-prompt.md          # Phase discovery template
│   │   ├── context.md               # CONTEXT.md template (user decisions)
│   │   ├── milestone.md             # MILESTONE.md template
│   │   ├── summary.md               # SUMMARY.md template
│   │   ├── verification-report.md   # VERIFICATION.md template
│   │   ├── research-project/        # Research project templates
│   │   │   ├── ARCHITECTURE.md
│   │   │   ├── STACK.md
│   │   │   ├── FEATURES.md
│   │   │   └── PITFALLS.md
│   │   └── [more templates]         # Other artifact templates
│   ├── workflows/                   # Multi-step orchestration workflows (30 workflows)
│   │   ├── new-project.md           # Initialize project through questioning
│   │   ├── map-codebase.md          # Spawn parallel mappers for codebase analysis
│   │   ├── plan-phase.md            # Research + plan + verify for phase
│   │   ├── execute-phase.md         # Wave-based parallel plan execution
│   │   ├── execute-plan.md          # Execute single PLAN.md file
│   │   ├── verify-phase.md          # Verify phase execution completeness
│   │   ├── verify-work.md           # Detailed verification with gap closure
│   │   ├── discover-phase.md        # Initial phase discovery
│   │   ├── discuss-phase.md         # Gather user decisions (CONTEXT.md)
│   │   ├── add-phase.md             # Add new phase to roadmap
│   │   ├── complete-milestone.md    # Archive milestone, merge branches
│   │   └── [20 more workflows]      # Other operation workflows
│   ├── VERSION                      # Version file (1.18.0)
│   └── README.md                    # GSD framework documentation
├── hooks/
│   ├── gsd-check-update.js          # Runs on session start to check for updates
│   └── gsd-statusline.js            # Renders progress statusline in editor
├── settings.json                    # Claude Code settings (hooks config)
└── gsd-file-manifest.json           # File tracking with SHA256 hashes

.planning/                           # Project artifacts (created by /gsd:new-project)
├── STATE.md                         # Project metadata and progress state
├── ROADMAP.md                       # Phase breakdown and goals
├── REQUIREMENTS.md                  # Table stakes + features
├── codebase/                        # Target codebase analysis (created by /gsd:map-codebase)
│   ├── STACK.md                     # Technologies and dependencies
│   ├── INTEGRATIONS.md              # External APIs and services
│   ├── ARCHITECTURE.md              # System design patterns
│   ├── STRUCTURE.md                 # Directory organization
│   ├── CONVENTIONS.md               # Coding conventions
│   ├── TESTING.md                   # Test patterns
│   └── CONCERNS.md                  # Technical debt and issues
├── config.json                      # Planning config (commit_docs, branching, search)
├── phases/                          # Phase execution artifacts
│   ├── 01-phase-name/
│   │   ├── 01-01-PLAN.md            # First plan in phase
│   │   ├── 01-02-PLAN.md            # Second plan
│   │   ├── 01-01-SUMMARY.md         # Execution results for plan 01
│   │   ├── 01-02-SUMMARY.md         # Execution results for plan 02
│   │   ├── 01-CONTEXT.md            # User decisions for phase
│   │   ├── 01-RESEARCH.md           # Phase research findings
│   │   ├── 01-VERIFICATION.md       # Phase verification report
│   │   └── 01-UAT.md                # User acceptance test results
│   └── [more phases...]
└── MILESTONES.md                    # Completed milestone archive

.gitignore                           # Standard ignores + optional .planning/
Makefile                             # Helper targets (e.g., `make claude`)
```

## Directory Purposes

**`.claude/agents/`:**
- Purpose: Specialized agent implementations for focused tasks
- Contains: Agent role definitions with tool configs and execution patterns
- Key files: `gsd-executor.md` (plan execution), `gsd-planner.md` (plan creation), `gsd-codebase-mapper.md` (codebase analysis)

**`.claude/commands/gsd/`:**
- Purpose: User-facing entry points to GSD workflows
- Contains: Markdown command definitions that declare execution context and tool allowlists
- Pattern: One file per command (e.g., `/gsd:new-project` → `new-project.md`)
- Key files: `map-codebase.md`, `new-project.md`, `plan-phase.md`, `execute-phase.md`

**`.claude/get-shit-done/bin/`:**
- Purpose: CLI tools for state management and orchestration
- Contains: `gsd-tools.js` (52K line main utility) and tests
- Usage: Invoked from workflows/agents via `node gsd-tools.js <command>`

**`.claude/get-shit-done/references/`:**
- Purpose: Decision documentation and pattern references
- Contains: Model profiles, phase calculation logic, questioning protocols, brand guides
- Key files: `model-profiles.md` (which Claude model to use), `planning-config.md` (config schema)

**`.claude/get-shit-done/templates/`:**
- Purpose: Starter content and scaffolding
- Contains: Markdown templates for artifacts, JSON config template
- Subdir `codebase/`: Templates for target codebase analysis documents

**`.claude/get-shit-done/workflows/`:**
- Purpose: Multi-step orchestration procedures
- Contains: Step-by-step workflows with bash commands, decision gates, Task spawning
- Key files: `new-project.md`, `plan-phase.md`, `execute-phase.md`, `map-codebase.md`

**`.planning/`:**
- Purpose: Project state and execution artifacts
- Created: By `/gsd:new-project` command
- Contains: STATE.md, ROADMAP.md, REQUIREMENTS.md, phase directories, codebase analysis
- Committed: Yes (unless config.json sets `commit_docs: false`)

**`.planning/codebase/`:**
- Purpose: Analysis of target codebase (not GSD framework)
- Created: By `/gsd:map-codebase` via parallel mapper agents
- Contains: 7 documents (STACK.md, ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, INTEGRATIONS.md, CONCERNS.md)

**`.planning/phases/{padded}-{slug}/`:**
- Purpose: Container for one phase's plans, research, context, and summaries
- Created: By `gsd-tools phase add`
- Contains: PLAN.md files (01-01-PLAN.md, 01-02-PLAN.md, etc), SUMMARY.md files, RESEARCH.md, CONTEXT.md, VERIFICATION.md

## Key File Locations

**Entry Points:**
- User commands: `.claude/commands/gsd/*.md` (slash command definitions)
- Workflows: `.claude/get-shit-done/workflows/*.md` (orchestration procedures)
- Agents: `.claude/agents/gsd-*.md` (focused implementations)
- CLI: `.claude/get-shit-done/bin/gsd-tools.js` (state/git operations)

**Configuration:**
- `.planning/config.json` - Project planning config (commit_docs, branching, search)
- `.claude/settings.json` - Claude Code settings (hooks)
- `.claude/gsd-file-manifest.json` - File tracking with hashes
- `Makefile` - Development helpers

**Core Logic:**
- Plan generation: `gsd-planner.md` agent
- Plan verification: `gsd-plan-checker.md` agent
- Plan execution: `gsd-executor.md` agent
- Codebase analysis: `gsd-codebase-mapper.md` agent
- State management: `gsd-tools.js` CLI utility

**Testing:**
- `.claude/get-shit-done/bin/gsd-tools.test.js` - Unit tests for CLI utility

## Naming Conventions

**Files:**
- Commands: `kebab-case.md` (e.g., `new-project.md`, `map-codebase.md`)
- Agents: `gsd-kebab-case.md` prefix (e.g., `gsd-executor.md`, `gsd-planner.md`)
- Workflows: `kebab-case.md` (e.g., `new-project.md`, `execute-phase.md`)
- Project artifacts: `UPPERCASE.md` or `PADDED-NUMBER-NAME.md` (e.g., `STATE.md`, `01-01-PLAN.md`)
- Codebase analysis: `UPPERCASE.md` (e.g., `STACK.md`, `ARCHITECTURE.md`)

**Directories:**
- Command group: `gsd/` (contains all `/gsd:*` commands)
- Phase directories: `{PADDED_PHASE}-{slug}` (e.g., `01-foundation`, `02-authentication`)
- Type directories: Named by purpose (`agents`, `commands`, `workflows`, `templates`, `references`)

**Frontmatter Fields:**
- Required: `name` (command/agent name), `description` (what it does)
- Plan metadata: `phase`, `plan`, `type`, `wave`, `depends_on`, `autonomous`, `tdd`, `gap_closure`
- Optional: `color` (visual indicator in CLI)

## Where to Add New Code

**New Agent:**
- Primary location: `.claude/agents/gsd-{agent-name}.md`
- Pattern: Copy `gsd-executor.md` structure with role, context, execution steps
- Tool declarations in frontmatter (e.g., `tools: Read, Write, Bash, Grep`)

**New Command:**
- Primary location: `.claude/commands/gsd/{command-name}.md`
- Pattern: Declare `name`, `description`, `argument-hint`, `allowed-tools`, `execution_context` reference
- Execution context should reference workflow in `.claude/get-shit-done/workflows/`

**New Workflow:**
- Primary location: `.claude/get-shit-done/workflows/{workflow-name}.md`
- Pattern: `<purpose>`, `<required_reading>`, `<process>` with numbered steps
- Each step includes bash commands, decision gates, Task spawning, and continuation path

**Utilities/Helpers:**
- Shared CLI tools: `.claude/get-shit-done/bin/gsd-tools.js`
- Reference docs: `.claude/get-shit-done/references/` (decision docs, patterns)
- Model decisions: Update `.claude/get-shit-done/references/model-profiles.md`

**Templates:**
- Artifact templates: `.claude/get-shit-done/templates/` (named by use: `state.md`, `roadmap.md`, `plan.md`)
- Codebase templates: `.claude/get-shit-done/templates/codebase/` (UPPERCASE.md files)

## Special Directories

**`.claude/get-shit-done/`:**
- Purpose: GSD framework core (not application code)
- Generated: No (all hand-authored)
- Committed: Yes (this is the framework repository)
- Versioning: VERSION file tracks framework version (1.18.0)

**`.planning/`:**
- Purpose: Project-specific planning artifacts
- Generated: Yes (created by commands/workflows)
- Committed: Configurable (config.json `commit_docs` field controls)
- Git ignore option: Add to `.gitignore` for client/OSS projects

**`.claude/hooks/`:**
- Purpose: Initialization and status hooks
- Generated: No (hand-authored)
- Committed: Yes (part of framework setup)
- Execution: Runs automatically (SessionStart, statusLine defined in settings.json)

---

*Structure analysis: 2026-02-09*
