# Testing Patterns

**Analysis Date:** 2026-02-09

## Test Framework

**Runner:**
- Node.js built-in `test` module (`node:test`)
- Version: Node.js 18+ (uses native test runner, not Jest/Vitest)
- Config: No configuration file required - tests run directly with `node <test-file>`

**Assertion Library:**
- Node.js built-in `assert` module (`node:assert`)
- Methods: `assert.ok()`, `assert.strictEqual()`, `assert.deepStrictEqual()`

**Run Commands:**
```bash
node /path/to/gsd-tools.test.js         # Run all tests
node --test 'pattern' /path/to/test     # Run matching tests (with pattern support in Node 20+)
```

## Test File Organization

**Location:**
- Co-located with source: `gsd-tools.js` and `gsd-tools.test.js` in same directory
- Path: `/workspaces/semantic-model-generator/.claude/get-shit-done/bin/`

**Naming:**
- Pattern: `{source-file}.test.js`
- Test file: `gsd-tools.test.js` for `gsd-tools.js`

**Structure:**
```
describe('feature name', () => {
  let tmpDir;                    // Shared test state

  beforeEach(() => {
    tmpDir = createTempProject();  // Setup
  });

  afterEach(() => {
    cleanup(tmpDir);             // Teardown
  });

  test('specific behavior', () => {
    // Test body
    assert.ok(condition, 'message');
  });
});
```

## Test Structure

**Suite Organization:**

The test file is organized by command/feature being tested:
1. `history-digest command` - Tests for SUMMARY.md frontmatter extraction
2. `phases list command` - Tests for phase directory listing
3. `roadmap get-phase command` - Tests for ROADMAP.md parsing
4. `phase add command` - Tests for adding new phases
5. `todo complete command` - Tests for todo file movement
6. `scaffold command` - Tests for file scaffolding

**Each describe block:**
- Groups related tests for one command
- Includes dedicated setup/teardown
- Tests both success and failure paths

**Example from `gsd-tools.test.js` (lines 42-62):**
```javascript
describe('history-digest command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('empty phases directory returns valid schema', () => {
    const result = runGsdTools('history-digest', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);

    const digest = JSON.parse(result.output);

    assert.deepStrictEqual(digest.phases, {}, 'phases should be empty object');
    assert.deepStrictEqual(digest.decisions, [], 'decisions should be empty array');
    assert.deepStrictEqual(digest.tech_stack, [], 'tech_stack should be empty array');
  });
});
```

**Patterns:**
- Setup: Create temporary project directory with required structure
- Teardown: Recursively delete temporary directory
- Execution: Call `runGsdTools()` helper function
- Assertion: Check output structure and values

## Mocking

**Framework:** No explicit mocking library
- Custom `runGsdTools()` helper spawns actual CLI process
- Mocking done via temporary file system state
- Process isolation through spawned child processes

**Patterns:**

File system mocking via temporary directories:
```javascript
function createTempProject() {
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'gsd-test-'));
  fs.mkdirSync(path.join(tmpDir, '.planning', 'phases'), { recursive: true });
  return tmpDir;
}

function cleanup(tmpDir) {
  fs.rmSync(tmpDir, { recursive: true, force: true });
}
```

Command execution wrapping:
```javascript
function runGsdTools(args, cwd = process.cwd()) {
  try {
    const result = execSync(`node "${TOOLS_PATH}" ${args}`, {
      cwd,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return { success: true, output: result.trim() };
  } catch (err) {
    return {
      success: false,
      output: err.stdout?.toString().trim() || '',
      error: err.stderr?.toString().trim() || err.message,
    };
  }
}
```

**What to Mock:**
- File system state (via temp directories)
- Environment/working directory (via `cwd` parameter)
- Command arguments (via helper function)

**What NOT to Mock:**
- Core command logic (tests should execute real code)
- JSON parsing (should test real parsing behavior)
- YAML/frontmatter extraction (critical to test with actual content)

## Fixtures and Factories

**Test Data:**

Inline fixture creation in test setup:
```javascript
test('nested frontmatter fields extracted correctly', () => {
  const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-foundation');
  fs.mkdirSync(phaseDir, { recursive: true });

  const summaryContent = `---
phase: "01"
name: "Foundation Setup"
dependency-graph:
  provides:
    - "Database schema"
    - "Auth system"
  affects:
    - "API layer"
tech-stack:
  added:
    - "prisma"
    - "jose"
patterns-established:
  - "Repository pattern"
  - "JWT auth flow"
key-decisions:
  - "Use Prisma over Drizzle"
  - "JWT in httpOnly cookies"
---

# Summary content here
`;

  fs.writeFileSync(path.join(phaseDir, '01-01-SUMMARY.md'), summaryContent);
  // ... assertions
});
```

**Location:**
- Fixtures are inline within test functions
- No separate fixture files
- Shared setup in `beforeEach()` for common structures

## Coverage

**Requirements:** Not enforced
- No coverage configuration detected
- No coverage badges or reports in CI
- Coverage measurement not part of build process

**View Coverage:**
```bash
node --test --experimental-coverage /path/to/test.js
```

## Test Types

**Unit Tests:**
- Scope: Individual command functionality
- Approach: Execute CLI command via spawned process, verify output/file system changes
- Isolation: Each test has independent temporary file system
- Focus: Command behavior, not internal function units

**Integration Tests:**
- Scope: Multiple commands interacting (phase creation → phase listing)
- Approach: Sequential command execution in same tmpDir
- Example: Create phase with `phase add`, then verify with `phases list`

**E2E Tests:**
- Framework: Not used
- No end-to-end workflow tests detected
- Full feature workflows tested implicitly through integration tests

## Common Patterns

**Async Testing:**
Not applicable - tests use synchronous file I/O and child process execution

**Error Testing:**

Testing error paths:
```javascript
test('malformed SUMMARY.md skipped gracefully', () => {
  const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-test');
  fs.mkdirSync(phaseDir, { recursive: true });

  // Valid summary
  fs.writeFileSync(
    path.join(phaseDir, '01-01-SUMMARY.md'),
    `---
phase: "01"
provides:
  - "Valid feature"
---
`
  );

  // Malformed summary (no frontmatter)
  fs.writeFileSync(
    path.join(phaseDir, '01-02-SUMMARY.md'),
    `# Just a heading
No frontmatter here
`
  );

  const result = runGsdTools('history-digest', tmpDir);
  assert.ok(result.success, `Command should succeed despite malformed files: ${result.error}`);

  const digest = JSON.parse(result.output);
  assert.ok(
    digest.phases['01'].provides.includes('Valid feature'),
    'Valid feature should be extracted'
  );
});
```

Pattern: Create invalid state, verify graceful handling and valid data still extracted.

**Success Path Testing:**
```javascript
test('moves todo from pending to completed', () => {
  const pendingDir = path.join(tmpDir, '.planning', 'todos', 'pending');
  fs.mkdirSync(pendingDir, { recursive: true });
  fs.writeFileSync(
    path.join(pendingDir, 'add-dark-mode.md'),
    `title: Add dark mode\narea: ui\ncreated: 2025-01-01\n`
  );

  const result = runGsdTools('todo complete add-dark-mode.md', tmpDir);
  assert.ok(result.success, `Command failed: ${result.error}`);

  const output = JSON.parse(result.output);
  assert.strictEqual(output.completed, true);

  // Verify moved
  assert.ok(
    !fs.existsSync(path.join(tmpDir, '.planning', 'todos', 'pending', 'add-dark-mode.md')),
    'should be removed from pending'
  );
  assert.ok(
    fs.existsSync(path.join(tmpDir, '.planning', 'todos', 'completed', 'add-dark-mode.md')),
    'should be in completed'
  );

  // Verify completion timestamp added
  const content = fs.readFileSync(
    path.join(tmpDir, '.planning', 'todos', 'completed', 'add-dark-mode.md'),
    'utf-8'
  );
  assert.ok(content.startsWith('completed:'), 'should have completed timestamp');
});
```

Pattern: Check output, verify file system state, verify side effects.

**Backward Compatibility Testing:**
```javascript
test('flat provides field still works (backward compatibility)', () => {
  const phaseDir = path.join(tmpDir, '.planning', 'phases', '01-test');
  fs.mkdirSync(phaseDir, { recursive: true });

  fs.writeFileSync(
    path.join(phaseDir, '01-01-SUMMARY.md'),
    `---
phase: "01"
provides:
  - "Direct provides"
---
`
  );

  const result = runGsdTools('history-digest', tmpDir);
  assert.ok(result.success, `Command failed: ${result.error}`);

  const digest = JSON.parse(result.output);
  assert.deepStrictEqual(
    digest.phases['01'].provides,
    ['Direct provides'],
    'Direct provides should work'
  );
});
```

Pattern: Test old data format still works with new parsing code.

## Test Execution

**Running tests:**
```bash
cd /workspaces/semantic-model-generator/.claude/get-shit-done/bin
node gsd-tools.test.js
```

**Output format:**
- Node.js test runner outputs TAP (Test Anything Protocol) format
- Verbose failure messages with assertion context
- Summary with pass/fail counts

**Test count:**
Current codebase: 30+ test cases across 7 describe blocks

---

*Testing analysis: 2026-02-09*
