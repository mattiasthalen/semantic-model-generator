# Technology Stack

**Analysis Date:** 2026-02-09

## Languages

**Primary:**
- Python 3.11 - Core application development (configured in devcontainer)

**Secondary:**
- JavaScript/Node.js - Build tooling, hooks, and development scripts
- Markdown - Documentation and configuration

## Runtime

**Environment:**
- Python 3.11 (via `mcr.microsoft.com/devcontainers/python:3.11-bookworm`)
- Node.js (latest, via devcontainer feature)

**Package Manager:**
- UV (Astral Python package manager) - Primary Python dependency management
  - Lockfile: Not yet created (project in bootstrap phase)
- npm (for Node.js tooling)

## Frameworks

**Development Framework:**
- Get-Shit-Done (GSD) v1.18.0 - Project management and structured development workflow
  - Agent-based orchestration for planning, executing, and verifying phases
  - Located: `.claude/get-shit-done/`

**Testing:**
- Not yet configured

**Build/Dev:**
- Claude Code - AI-powered development environment
- GitHub CLI - Version control integration
- Makefile - Basic automation (see `Makefile`)

## Key Dependencies

**Infrastructure:**
- get-shit-done-cc v1.18.0 - Project management framework
  - Provides agents for codebase mapping, planning, execution, verification
  - Uses structured prompts and templates for consistent development

**Development Tools:**
- gitlens - VS Code extension for Git visualization
- claude-code - VS Code extension for AI code assistance

## Configuration

**Environment:**
- Devcontainer-based development environment
- Configuration: `.devcontainer/devcontainer.json`
- Base image: Debian Bookworm with Python 3.11
- GitHub authentication configured via `ghcr.io/devcontainers/features/github-cli:1`

**Build:**
- Makefile for local development commands
- Python environment managed through devcontainer

## Platform Requirements

**Development:**
- Docker/Devcontainer capable machine
- VS Code with Dev Containers extension
- Git configuration for commits

**Production:**
- Python 3.11 runtime
- Dependencies installed via UV

---

*Stack analysis: 2026-02-09*
