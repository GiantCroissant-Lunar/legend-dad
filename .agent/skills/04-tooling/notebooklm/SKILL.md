---
name: notebooklm
description: Query Google NotebookLM notebooks for research context — create notebooks, add sources, query content, cross-notebook search, generate audio/video summaries. Use when gathering external research, querying knowledge bases, or generating audio overviews from collected sources.
category: 04-tooling
layer: tooling
requires:
  python: ">=3.10"
related_skills:
  - "@docling"
  - "@qmd-search"
  - "@context-discovery"
---

# NotebookLM Skill

Access [Google NotebookLM](https://notebooklm.google.com/) programmatically via [notebooklm-mcp-cli](https://github.com/jacob-bd/notebooklm-mcp-cli). Create notebooks, add sources, query content, run cross-notebook searches, and generate audio/video summaries.

## When to Use

- Querying a NotebookLM notebook for research context on a feature
- Adding project docs, URLs, or files as sources to a notebook
- Cross-notebook search across multiple knowledge bases
- Generating audio overviews (podcast-style) from collected sources
- Batch operations across multiple notebooks
- Building multi-step research pipelines

## Installation

```bash
# Install via uv (recommended)
uv tool install notebooklm-mcp-cli

# Authenticate (extracts cookies from browser)
nlm login
nlm login --check   # verify auth status
```

## CLI Usage

### Notebook Management

```bash
# List all notebooks
nlm notebook list

# Create a notebook
nlm notebook create "RFC Research - Combat System"

# Query a notebook (natural language)
nlm notebook query <notebook-id> "What are the key design patterns for turn-based combat?"

# Share a notebook
nlm notebook share <notebook-id> <email> --role reader
```

### Source Management

```bash
# Add a URL source
nlm source add <notebook-id> --url "https://example.com/article"

# Add text directly
nlm source add <notebook-id> --text "Design notes: ..."

# Add a local file (PDF, DOCX, etc.)
nlm source add <notebook-id> --file docs/rfcs/005-combat.md

# Add from Google Drive
nlm source add <notebook-id> --drive <drive-file-id>

# Sync Drive sources
nlm source sync-drive <notebook-id>

# Delete a source
nlm source delete <notebook-id> <source-id>
```

### Content Generation (Audio/Video)

```bash
# Generate audio overview (podcast-style)
nlm studio create <notebook-id> --type audio

# Generate with custom instructions
nlm studio create <notebook-id> --type audio --instructions "Focus on combat mechanics and balance"

# Revise a generated artifact
nlm studio revise <artifact-id> --instructions "Make it shorter"

# Download generated audio/video
nlm download <artifact-id> --output docs/audio/
```

### Research & Search

```bash
# Cross-notebook search
nlm cross-notebook-query "procedural dungeon generation"

# Start web research
nlm research start <notebook-id> --web "turn-based combat systems in JRPGs"

# Start Drive research
nlm research start <notebook-id> --drive "game design documents"

# Tag management
nlm tag add <notebook-id> "combat" "research"
nlm tag list
```

### Batch & Pipeline Operations

```bash
# Batch operations (JSON array)
nlm batch '[{"action": "query", "notebook_id": "xxx", "query": "..."}]'

# Multi-step pipeline (YAML)
nlm pipeline run pipeline.yaml
```

## MCP Server Configuration

### Automatic Setup (Recommended)

```bash
nlm setup add claude-code
```

### Manual Configuration

Add to Claude Code settings (`settings.json` or `.claude/settings.json`):

```json
{
  "mcpServers": {
    "notebooklm-mcp": {
      "command": "notebooklm-mcp"
    }
  }
}
```

Or without global install (via `uvx`):

```json
{
  "mcpServers": {
    "notebooklm-mcp": {
      "command": "uvx",
      "args": ["--from", "notebooklm-mcp-cli", "notebooklm-mcp"]
    }
  }
}
```

### MCP Tools (35 tools)

| Category | Key Tools |
|---|---|
| Notebook | `notebook_list`, `notebook_create`, `notebook_query`, `notebook_share_get`, `notebook_share_set` |
| Sources | `source_add`, `source_sync_drive`, `source_delete` |
| Generation | `studio_create`, `studio_revise`, `download_artifact` |
| Research | `research_start`, `cross_notebook_query` |
| Batch | `batch`, `pipeline` |
| Tags | `tag_add`, `tag_remove`, `tag_list` |

## Workflow: Research Context for RFC Implementation

```bash
# 1. Create a notebook for the feature
nlm notebook create "RFC-005 Combat Research"

# 2. Add project RFCs and design docs as sources
nlm source add <id> --file docs/rfcs/005-combat.md
nlm source add <id> --file docs/rfcs/006-party.md

# 3. Add external references
nlm source add <id> --url "https://example.com/jrpg-combat-patterns"

# 4. Query for design guidance
nlm notebook query <id> "What damage formula should we use for spell attacks?"

# 5. Generate an audio summary for team review
nlm studio create <id> --type audio --instructions "Summarize combat design decisions"
```

## Workflow: Cross-Notebook Knowledge Search

```bash
# Search across all notebooks for relevant context
nlm cross-notebook-query "how should status effects stack?"

# Use results to inform implementation
```

## Workflow: Pair with @docling for Document Ingestion

```bash
# 1. Convert a PDF to markdown with @docling
docling game-design-spec.pdf --output docs/converted/

# 2. Add the converted content to NotebookLM
nlm source add <notebook-id> --file docs/converted/game-design-spec.md

# 3. Query the notebook
nlm notebook query <notebook-id> "What are the core progression mechanics?"
```

## Important Notes

- **Authentication** uses browser cookie extraction — run `nlm login` before first use
- **Undocumented APIs** — NotebookLM has no official API; this tool uses internal endpoints that may change
- **35 MCP tools** consume context window space — disable the MCP server when not actively using it
- **Rate limits** — Google may throttle requests; add delays for batch operations
- **Browser support**: Chrome, Arc, Brave, Edge, Chromium (cookie extraction)
- **Audio generation** can take 1-5 minutes depending on source volume

## Checklist

- [ ] Run `nlm login --check` to verify authentication before use
- [ ] Create purpose-specific notebooks (one per RFC or research topic)
- [ ] Add relevant project docs as sources before querying
- [ ] Use `cross-notebook-query` for broad searches across all notebooks
- [ ] Disable the MCP server when not actively using NotebookLM (saves context window)
- [ ] Pair with `@docling` for PDF/DOCX sources that need conversion first
