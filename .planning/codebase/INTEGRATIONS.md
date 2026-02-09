# External Integrations

**Analysis Date:** 2026-02-09

## APIs & External Services

**GitHub:**
- GitHub CLI integration via devcontainer feature
- Used for: Version control operations, PR management, git hooks
  - SDK/Client: GitHub CLI (ghcr.io/devcontainers/features/github-cli:1)
  - Auth: SSH keys or personal access tokens (managed via devcontainer secrets)

**Claude AI (Anthropic):**
- Claude Code integration for AI-assisted development
- Used for: Code generation, analysis, planning, and execution within GSD framework
  - SDK/Client: Claude Code VS Code extension
  - Auth: Session-based via Claude authentication

**npm Registry:**
- Used for: GSD framework package distribution and updates
  - Service: npmjs.com
  - Package: get-shit-done-cc

## Data Storage

**Databases:**
- Not yet integrated

**File Storage:**
- Local filesystem only
  - Project files: Repository root
  - Planning/state: `.planning/` directory
  - Configuration: `.claude/` directory

**Caching:**
- None configured

## Authentication & Identity

**Auth Provider:**
- GitHub authentication
  - Implementation: Devcontainer feature integration with system SSH keys
  - Scope: Repository access for version control

**Git Configuration:**
- Managed through devcontainer with GitHub CLI

## Monitoring & Observability

**Error Tracking:**
- None configured

**Logs:**
- Console output from CLI commands
- Makefile targets log to stdout

## CI/CD & Deployment

**Hosting:**
- Not yet configured

**CI Pipeline:**
- None configured
- GSD framework provides local phase execution and verification

## Environment Configuration

**Required env vars:**
- None explicitly defined yet
- Available: Standard shell environment variables from devcontainer
- Git credentials available via SSH when configured in devcontainer

**Secrets location:**
- Environment secrets managed by devcontainer
- SSH keys for GitHub: System SSH configuration (passed to devcontainer)
- Personal access tokens: Could be stored in devcontainer environment

## Webhooks & Callbacks

**Incoming:**
- None configured

**Outgoing:**
- Git hooks infrastructure available via `.claude/hooks/`
- GSD update check hook: `.claude/hooks/gsd-check-update.js`
  - Triggers: SessionStart hook in Claude Code
  - Action: Checks for GSD framework updates from npm registry

---

*Integration audit: 2026-02-09*
