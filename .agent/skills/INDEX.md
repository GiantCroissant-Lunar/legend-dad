# Skills Index

Numbered categories create an implicit dependency hierarchy — lower numbers are more foundational and consumed by higher-numbered layers.

## 00-meta — Governance & Meta-Skills

| Skill | Description | Related Skills |
|---|---|---|
| `skill-creator` | Create, test, and improve agent skills. Meta-skill for the skill system itself. | — |
| `rfc-orchestrator` | Map RFC features to skill compositions and dispatch implementation phases. | `@context-discovery`, `@validation-guard` |
| `context-discovery` | **Mandatory pre-flight**: scan project state, check Godot/server/tooling health, produce ContextReport before any implementation. | `@rfc-orchestrator`, `@validation-guard` |
| `validation-guard` | **Mandatory post-flight**: verify linting, mandatory rule compliance, build integrity, pre-commit checks after implementation. | `@rfc-orchestrator`, `@context-discovery` |
| `autoloop` | Autonomous iteration protocol — keep/discard cycle, git-as-state-machine, context window management, simplicity-weighted evaluation. | `@rfc-orchestrator`, `@validation-guard`, `@skill-creator` |
| `implementation-review` | Three-pass code review: Pass 0 design intent vs RFC, Pass 1 critical issues, Pass 2 informational. AUTO/ASK/ESCALATE triage. | `@rfc-orchestrator`, `@validation-guard`, `@context-discovery` |
| `rfc-review` | Structured RFC review with quantitative scoring across 6 dimensions. | `@rfc-orchestrator`, `@context-discovery` |
| `dev-log` | **Mandatory end-of-session**: write a structured log entry to `vault/dev-log/` recording what was done, decisions made, and next steps. All agents must use this. | `@context-discovery`, `@validation-guard`, `@autoloop` |

## 01-godot — Engine Reference

| Skill | Description | Related Skills |
|---|---|---|
| `godot-api` | Godot 4.6.2 class API lookup (forked context). Per-class markdown docs generated from the Godot source repo, plus a GDScript syntax reference. Invoke for method signatures, signal lookups, or "which class does X". | `@context-discovery` |

## 03-presentation — UI & Design

| Skill | Description | Related Skills |
|---|---|---|
| `ui-ux-pro-max` | UI/UX design intelligence — 67 styles, 96 palettes, 57 font pairings, 25 charts, 13 stacks. Searchable database with BM25 search and design system generation. | — |

## 04-tooling — Automation & Reference

| Skill | Description | Related Skills |
|---|---|---|
| `agent-browser` | Browser automation CLI — navigate, snapshot, interact, screenshot, scrape, test web apps. | — |
| `docling` | Convert documents (PDF, DOCX, PPTX, images) to structured markdown for KB ingestion. | `@qmd-search` |
| `repomix` | Pack repo/files into single AI-friendly file for LLM context, external review, docs generation. | `@context-discovery`, `@qmd-search`, `@docling` |
| `qmd-search` | Local hybrid search (BM25 + vector + reranking) over project docs and skills via QMD. | `@context-discovery`, `@rfc-orchestrator`, `@docling` |
| `notebooklm` | Query Google NotebookLM notebooks — create, add sources, query, cross-search, audio summaries. | `@docling`, `@qmd-search` |

## 05-world — World Bible & Lore

| Skill | Description | Related Skills |
|---|---|---|
| `world-writer` | Generate world bible pages for the Obsidian vault using prompt templates and existing lore. | `@lore-checker`, `@lore-extractor` |
| `world-refiner` | Iteratively score and improve vault pages against 8 measurable quality metrics. | `@world-writer`, `@lore-checker` |
| `lore-checker` | Validate vault pages against the master timeline and existing canon for contradictions. | `@world-writer`, `@lore-extractor` |
| `lore-extractor` | Extract world facts from RFCs and design docs into vault-formatted pages. | `@world-writer`, `@lore-checker`, `@rfc-orchestrator` |
| `articy-prep` | Format reviewed vault pages into Articy-import-ready structured data. | `@world-writer`, `@lore-checker` |

## Agent Workflow

**Standard** (human-in-the-loop):
```
@context-discovery → @rfc-orchestrator → Load skills → Implement → @validation-guard → task build
```

**Autonomous** (via `@autoloop` — hands-free iterative implementation):
```
@context-discovery → @rfc-orchestrator → Create branch → LOOP { implement → commit → lint → @validation-guard (inline) → keep/discard → log } → Full validation → Report
```

## Frontmatter Schema

Every SKILL.md has YAML frontmatter with these fields:

```yaml
---
name: skill-name                    # Unique identifier
description: ...                    # Triggers skill loading — be specific
category: 00-meta                   # Numbered category directory
layer: governance|presentation|tooling|world
always_active: true|false           # If true, rules apply to ALL code (optional)
related_skills:                     # @skill-name cross-references
  - "@validation-guard"
---
```

**Layers** (implicit dependency: lower consumes higher):
- `governance` — meta-skills that orchestrate other skills
- `engine` — engine-specific reference (Godot API, quirks)
- `presentation` — UI/UX design
- `tooling` — automation, browser, docs, search
- `world` — world bible, lore generation, narrative consistency

## 06-gameplay — Game Interaction

| Skill | Description | Related Skills |
|---|---|---|
| `game-player` | Play the Legend Dad game via MCP tools — move, interact, switch eras, observe state, react to events. For AI agents operating as game players. | `@context-discovery`, `@dev-log` |

## Conventions

- **Cross-references** use `@skill-name` notation (e.g., `@validation-guard`)
- **Mandatory rules** (enforced via `@validation-guard`):
  1. All JS uses `const`/`let`, never `var`
  2. biome + ruff must pass before committing
  3. No hardcoded ports or secrets in source
  4. Build artifacts never committed to git
  5. Server config via environment variables
  6. GDScript follows Godot style guide
