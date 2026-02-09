# Codebase Concerns

**Analysis Date:** 2026-02-09

## Tech Debt

**Large monolithic gsd-tools.js file:**
- Issue: Core CLI tool is 4,500+ lines in a single file with 333+ loops/iterations
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (4503 lines)
- Impact: Difficult to test individual commands, high complexity, hard to maintain separate command logic
- Fix approach: Split into modular command handlers (e.g., `commands/state.js`, `commands/phase.js`, `commands/scaffold.js`) with shared utilities in separate files. Reduces cognitive load per file.

**Complex YAML/frontmatter parser:**
- Issue: Manual stack-based parser for YAML frontmatter (lines 248-321) lacks standard YAML validation
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (extractFrontmatter function, lines 248-321)
- Impact: Fragile to malformed YAML input, silent failures on complex structures, no error recovery
- Fix approach: Use established YAML parsing library (e.g., js-yaml) instead of custom parsing. Validates against schema and provides clear error messages.

**Unsafe JSON.parse without try-catch in critical path:**
- Issue: Line 4252 parses `--fields` JSON flag without error handling: `JSON.parse(args[fieldsIdx + 1])`
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (line 4252)
- Impact: CLI crashes with unhelpful error if user provides invalid JSON via `--fields` flag
- Fix approach: Wrap in try-catch block, return clear error message like other JSON.parse calls (lines 629, 2028)

**Inconsistent error handling patterns:**
- Issue: Some functions use try-catch (lines 627-633), others fail silently (JSON.parse at line 4252), others throw via `error()` function
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (scattered)
- Impact: Unpredictable error behavior, hard for users to diagnose CLI failures
- Fix approach: Establish single error handling pattern - wrap all I/O operations in try-catch, always use `error()` function for user-facing failures

**Missing input validation on user-provided paths:**
- Issue: Phase numbers, file paths, and field names accepted without validation before use in git commands
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (execGit function, line 218; normalizePhaseName, line 239)
- Impact: Could fail silently or produce unexpected results with invalid input (e.g., phase "99..abc")
- Fix approach: Add validation functions for phase numbers (must be `\d+(\.\d+)?`), file paths (no traversal), field names (alphanumeric + underscore)

## Known Bugs

**Shell injection risk in isGitIgnored function:**
- Symptoms: Path with special characters might cause git command to fail or behave unexpectedly
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (line 208)
- Trigger: Running with a file path containing backticks or $(cmd) sequences
- Workaround: Current escaping removes non-alphanumeric chars, mostly safe but overly restrictive
- Current implementation: Uses regex `/[^a-zA-Z0-9._\-/]/g` to allow only safe chars, catches most injection attempts

**YAML parsing loses array-like structures:**
- Symptoms: YAML arrays in frontmatter may be converted to objects or scalars incorrectly
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (lines 280-320, especially line 307-309)
- Trigger: Nested arrays or mixed content in frontmatter
- Workaround: Keep YAML simple, use inline arrays `[item1, item2]`
- Impact: May lose data or convert structure type unexpectedly when round-tripping frontmatter

**Test coverage gaps in gsd-tools.test.js:**
- Symptoms: 94 test suites/cases for 4,500 lines of code (~2% coverage of lines) - major gaps likely
- Files: `.claude/get-shit-done/bin/gsd-tools.test.js` (2033 lines)
- Trigger: Running commands with unusual edge cases or error conditions
- Impact: Untested code paths could silently fail or produce wrong output in production

## Security Considerations

**Makefile exposes dangerous permission bypass:**
- Risk: `make claude` target uses `--dangerously-skip-permissions` flag which disables Claude Code's permission system
- Files: `Makefile` (line 9)
- Current mitigation: Documented as intentional (comment says "Run Claude with full permissions")
- Recommendations: Remove or guard this target. If needed for development, add warning comment explaining risks. Consider alternative: use standard `claude` command and grant permissions interactively only when needed.

**Shell escaping in execGit may be insufficient:**
- Risk: Custom escaping implementation might miss edge cases that dedicated libraries handle
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (lines 220-223)
- Current mitigation: Uses safe character whitelist, reduces attack surface significantly
- Recommendations: Use `cross-spawn` or `execa` library which handles shell escaping more robustly across platforms

**Hardcoded paths and environment assumptions:**
- Risk: Assumes `.claude/get-shit-done/` structure exists; no validation
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (throughout), `.claude/hooks/gsd-check-update.js` (lines 16-17)
- Current mitigation: Runtime checks exist for some paths (e.g., line 3668 checks for code files)
- Recommendations: Add startup validation that required directories/files exist; clear error messages if structure broken

**Background process spawning in hooks:**
- Risk: `gsd-check-update.js` spawns background process to fetch npm version (line 25), could be exploited
- Files: `.claude/hooks/gsd-check-update.js` (lines 25-65)
- Current mitigation: Uses `spawn` not `exec`, JSON-validated input, timeout set to 10s
- Recommendations: Consider checksumming or signing the version file; validate npm registry response format more strictly

## Performance Bottlenecks

**Synchronous file I/O in CLI tool:**
- Problem: All operations use `fs.readFileSync` and `fs.writeFileSync` (blocking I/O)
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (100+ instances)
- Cause: CLI is synchronous by design to support shell scripting, but large files/many operations will block
- Improvement path: For batch operations (e.g., commit multiple files), consider parallel async I/O in separate utility; keep CLI interface synchronous

**Complex nested loops in YAML parser:**
- Problem: extractFrontmatter uses stack with O(n²) potential in pathological cases (nested objects with frequent lookups)
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (lines 260-318, especially line 306-309 which loops through all parent keys)
- Cause: Line 306-309 iterates all parent.obj keys to find parent reference - could fail with large objects
- Improvement path: Track parent reference in stack instead of searching; use Map instead of Object.keys loop

**Git command execution for every state operation:**
- Problem: Each phase operation spawns new git process via execSync, overhead multiplies with many phases
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (line 224, execGit called repeatedly)
- Cause: No git operation batching or caching
- Improvement path: Batch multiple git operations in single invocation; cache results per session

## Fragile Areas

**Phase numbering and normalization logic:**
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (lines 239-245, normalizePhaseName)
- Why fragile: Assumes 2-digit padding for first component; complex decimal phases like "1.2.3" may not work as expected
- Safe modification: Never change padding logic without updating all phase directory lookups; add tests for edge cases like "0.0", "99.99"
- Test coverage: Only tested in gsd-tools.test.js with simple cases (no multi-decimal testing)

**Frontmatter round-trip (parse → modify → reconstruct):**
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (extractFrontmatter lines 248-321 + reconstructFrontmatter lines 323+)
- Why fragile: Conversion between YAML and JS objects can lose type info (arrays become objects); manual parsing doesn't preserve original formatting
- Safe modification: Never modify frontmatter extraction logic without testing round-trip on existing .planning/ files; test with comments in YAML
- Test coverage: gsd-tools.test.js has basic tests but no complex YAML round-trip validation

**Git status detection and dirty-state handling:**
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (execGit function lines 218-237)
- Why fragile: Assumes git always available; doesn't handle submodules, merge conflicts, or detached HEAD gracefully
- Safe modification: Always validate git is available before git operations; wrap all git calls in error checking
- Test coverage: Tests don't cover missing git or corrupted git state

**State.md parsing and updates:**
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (state operations - likely incomplete coverage)
- Why fragile: Manual YAML parsing means any malformed STATE.md breaks tools; no atomic updates
- Safe modification: Back up STATE.md before modifications; validate parsed structure matches expected schema
- Test coverage: Test suite exists but unknown depth of state operation coverage

## Scaling Limits

**Single-file storage of all project state:**
- Current capacity: STATE.md probably safe for <1000 phases, but json parsing and writes become slow
- Limit: With many phases/milestones, O(n) parse-modify-write-all pattern will be bottleneck
- Scaling path: Consider splitting STATE into STATE.md (summary only) + separate phase/.../state.json files for phase-specific data

**Git repository growth with long phase history:**
- Current capacity: Works fine for 100s of phases, commits will grow repo size
- Limit: 1000s of commits + large .planning/ directory could make git operations slow
- Scaling path: Archive old milestones to separate branch; compress .planning/ periodically

**In-memory JSON parsing of large frontmatter:**
- Current capacity: Single JSON/YAML parse fine for <1MB files
- Limit: If frontmatter contains large nested structures or many array items, memory spikes possible
- Scaling path: Stream-parse YAML instead of loading full content; consider binary format for large metadata

## Dependencies at Risk

**No dependency management:**
- Risk: Uses Node.js built-ins only (fs, path, child_process, os); no package.json means no reproducible environment
- Impact: If code relies on node modules later, no version pinning; incompatibility with different Node versions possible
- Migration plan: Add package.json with explicit Node version in .nvmrc; pin versions for any new dependencies (js-yaml, etc)

**Custom YAML parser instead of standard library:**
- Risk: Manual YAML parsing may diverge from spec with complex documents; no maintenance
- Impact: Data loss on complex YAML; incompatible with standard YAML tools
- Migration plan: Gradually migrate to js-yaml library; validate all existing .planning/ files parse correctly

**Git availability assumption:**
- Risk: Code fails completely if git not available or corrupted
- Impact: CLI tools non-functional without git
- Migration plan: Add startup check for git; provide clear error message and fallback for non-git-initialized directories

## Missing Critical Features

**No configuration validation schema:**
- Problem: config.json structure undefined - tools accept any JSON
- Blocks: Can't provide meaningful error messages when config is malformed
- Fix approach: Define explicit schema (TypeScript interface or JSON Schema) and validate on load

**No transaction/rollback mechanism:**
- Problem: If multi-step operation fails (e.g., commit-then-update-state), inconsistency possible
- Blocks: Can't safely retry failed operations without manual cleanup
- Fix approach: Implement checkpointing - write intermediate states to temp files, rollback on error

**No logging or debugging output:**
- Problem: When operations fail, users have no visibility into what went wrong
- Blocks: Troubleshooting issues requires running commands manually
- Fix approach: Add `--debug` flag to all commands; log to `.planning/debug.log`

**No atomic multi-file operations:**
- Problem: Phase operations might update multiple files (phase dir, ROADMAP, STATE) non-atomically
- Blocks: Git history could show partial updates
- Fix approach: Batch file writes, single commit at end; or use git transactions (git worktree)

## Test Coverage Gaps

**gsd-tools.js command coverage:**
- What's not tested: Commands spanning lines 4300-4500 (init, template, frontmatter, verify) likely have minimal tests
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (lines 4200-4503)
- Risk: init commands that scaffold entire phases could fail silently or create malformed structures
- Priority: HIGH - init commands are critical path for new projects

**Error handling test cases:**
- What's not tested: All error paths in JSON.parse, file I/O, git operations
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (scattered error handling)
- Risk: Error messages might be unhelpful or missing in edge cases
- Priority: MEDIUM - affects user experience but not core functionality

**Shell escaping security tests:**
- What's not tested: execGit with special characters, paths with spaces/quotes
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (execGit function)
- Risk: Shell injection if escaping logic has gaps
- Priority: HIGH - security risk if shell injection possible

**Cross-platform compatibility:**
- What's not tested: Windows path handling, line ending handling, git command variations
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (git operations), hooks (spawn operations)
- Risk: Tools might fail on Windows or WSL due to path format differences
- Priority: MEDIUM - affects Windows developers

**YAML round-trip validation:**
- What's not tested: Complex nested YAML, preservation of comments, quote styles
- Files: `.claude/get-shit-done/bin/gsd-tools.js` (extractFrontmatter + reconstructFrontmatter)
- Risk: Data loss when parsing and re-serializing YAML
- Priority: MEDIUM - affects data integrity on frontmatter edits

---

*Concerns audit: 2026-02-09*
