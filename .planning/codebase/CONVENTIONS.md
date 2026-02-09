# Coding Conventions

**Analysis Date:** 2026-02-09

## Naming Patterns

**Files:**
- Command-line tools: `.js` suffix with kebab-case for multi-word names
  - Examples: `gsd-tools.js`, `gsd-tools.test.js`, `gsd-check-update.js`
- Hooks: prefix with `gsd-`, snake_case or kebab-case
  - Examples: `gsd-check-update.js`, `gsd-statusline.js`

**Functions:**
- Command handlers: `cmd` prefix with PascalCase suffix
  - Examples: `cmdGenerateSlug()`, `cmdCurrentTimestamp()`, `cmdHistoryDigest()`
- Helper functions: camelCase, descriptive names
  - Examples: `parseIncludeFlag()`, `safeReadFile()`, `loadConfig()`, `execGit()`
- State management: `cmd` + action verb + resource
  - Examples: `cmdStateLoad()`, `cmdStateGet()`, `cmdStateUpdate()`

**Variables:**
- camelCase for local variables and parameters
- UPPERCASE_SNAKE_CASE for constants and configuration objects
  - Example: `MODEL_PROFILES`, `defaults`
- Descriptive names with no abbreviations unless self-evident
  - Good: `includeValue`, `frontmatter`, `phaseDir`
  - Avoid: `val`, `fm`, `pd`

**Types:**
- Objects representing structured data use descriptive names
  - Example: `result = { success: true, output: '...' }`
- Configuration objects: noun + configuration pattern
  - Example: `scaffoldOptions = { phase, name }`

## Code Style

**Formatting:**
- No explicit linter/formatter configured in codebase
- Tab width: 2 spaces (inferred from source code)
- Line endings: LF (Unix style)
- No semicolons at end of statements in some files, but used consistently within files

**Structure:**
- Modular organization with clear section separators using visual dividers
- Section format: `// ─── Section Name ───────────────────────────────────────`
- Major sections group related functions:
  - Model Profile Table
  - Helpers
  - Commands
  - State Progression Engine
  - Frontmatter CRUD
  - Verification Suite
  - Roadmap Analysis
  - Phase operations (Add, Insert, Remove, Complete)
  - Milestone Complete
  - Validate Consistency
  - Progress Render
  - Todo Complete
  - Scaffold
  - Compound Commands
  - CLI Router

**Linting:**
- No ESLint or Prettier configuration files detected
- Code follows loose but consistent style conventions

## Import Organization

**Order:**
1. Node.js built-in modules (`fs`, `path`, `os`, `child_process`, etc.)
2. No external dependencies in primary codebase
3. Local function calls within same module

**Path Aliases:**
- Not detected - file paths used as absolute paths for node execution
- Bash scripts use relative path resolution for locating gsd-tools.js

**Example from `gsd-tools.js`:**
```javascript
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
```

**Example from test file:**
```javascript
const { test, describe, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
```

## Error Handling

**Patterns:**
- Centralized `error()` function for fatal errors
  - Writes to `process.stderr` and exits with code 1
  - Usage: `error('Missing required argument')`
- Try-catch blocks for file I/O and risky operations
  - Silent failure with fallbacks when appropriate
  - Example: `safeReadFile()` returns `null` on failure instead of throwing
- Null coalescing for optional values
  - Pattern: `value ?? defaultValue`

**Exit codes:**
- 0: Success
- 1: Fatal error

**Example from `gsd-tools.js`:**
```javascript
function error(message) {
  process.stderr.write('Error: ' + message + '\n');
  process.exit(1);
}

function safeReadFile(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf-8');
  } catch {
    return null;
  }
}
```

## Logging

**Framework:** Console I/O (stdout/stderr)

**Patterns:**
- `process.stdout.write()` for regular output
- `process.stderr.write()` for errors
- JSON output for structured data (when not `--raw` flag)
- Raw text output with `--raw` flag for piping

**Example:**
```javascript
function output(result, raw, rawValue) {
  if (raw && rawValue !== undefined) {
    process.stdout.write(String(rawValue));
  } else {
    process.stdout.write(JSON.stringify(result, null, 2));
  }
  process.exit(0);
}
```

## Comments

**When to Comment:**
- Complex parsing logic (e.g., YAML/frontmatter parsing)
- Non-obvious algorithmic decisions
- Section separators for major code blocks
- Inline comments for state machine logic

**JSDoc/TSDoc:**
- Not used consistently across the codebase
- File headers include high-level description (e.g., `gsd-check-update.js` header explains purpose)

**Example of section comments:**
```javascript
// Stack to track nested objects: [{obj, key, indent}]
// obj = object to write to, key = current key collecting array items, indent = indentation level
let stack = [{ obj: frontmatter, key: null, indent: -1 }];
```

## Function Design

**Size:**
- Typical range: 20-80 lines for command handlers
- Larger functions (200+ lines) contain repetitive parsing logic
- Short helpers (5-10 lines) for utility operations

**Parameters:**
- No function uses more than 3 explicit parameters
- Options/context passed as objects when needed
- `cwd` parameter standard for file system operations
- `raw` flag standard for output formatting

**Return Values:**
- Command handlers: call `output()` or `error()` rather than returning
- Helper functions: return structured objects or null/false on failure
- No promise/async patterns detected

**Example:**
```javascript
function cmdGenerateSlug(text, raw) {
  if (!text) {
    error('text required for slug generation');
  }

  const slug = text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

  const result = { slug };
  output(result, raw, slug);
}
```

## Module Design

**Exports:**
- Main file: `gsd-tools.js` calls `main()` at module end (not exported)
- Single entry point for CLI execution
- All functions scoped to module (no explicit exports)

**Barrel Files:**
- Not used - single monolithic file approach for CLI tool

## Configuration and Constants

**Constants:**
- `MODEL_PROFILES` object at top level defines AI model configurations
- Configuration objects are read from `.planning/config.json` at runtime
- Nested configuration loading with fallbacks to defaults

**Example:**
```javascript
const MODEL_PROFILES = {
  'gsd-planner':              { quality: 'opus', balanced: 'opus',   budget: 'sonnet' },
  'gsd-roadmapper':           { quality: 'opus', balanced: 'sonnet', budget: 'sonnet' },
  'gsd-executor':             { quality: 'opus', balanced: 'sonnet', budget: 'sonnet' },
  // ... more profiles
};

const defaults = {
  model_profile: 'balanced',
  commit_docs: true,
  search_gitignored: false,
  // ... more defaults
};
```

## Common Patterns

**Command Processing:**
All CLI commands follow dispatch pattern in main router (lines 4129-4501 in `gsd-tools.js`):
```javascript
case 'command-name': {
  const subcommand = args[1];
  if (subcommand === 'specific') {
    cmdSpecificHandler(cwd, args[2], raw);
  } else {
    error('Unknown subcommand. Available: ...');
  }
  break;
}
```

**Argument Parsing:**
- Flag-based: `args.indexOf('--flag')` to find flag position
- Value extraction: `args[flagIndex + 1]` for next argument
- Helper: `parseIncludeFlag()` for comma-separated values

**Path Normalization:**
- YAML frontmatter parsing uses regex and string manipulation
- No path library used for parsing frontmatter (custom stack-based parser in `extractFrontmatter()`)

---

*Convention analysis: 2026-02-09*
