---
name: qmd-search
description: Use when searching project documentation, RFCs, or skill content semantically — hybrid BM25 + vector + reranking via local QMD server.
category: 04-tooling
layer: tooling
related_skills:
  - "@context-discovery"
  - "@rfc-orchestrator"
  - "@docling"
---

# QMD Search Skill

Local hybrid search over project documentation using [QMD](https://github.com/tobi/qmd) — combines BM25 keyword search, vector semantic search, and LLM reranking. All local, no API calls.

## When to Use

- Finding relevant RFCs or design decisions for a feature
- Discovering which skills relate to a task
- Searching handover notes for prior context
- Locating patterns, conventions, or architectural decisions across docs
- Pre-flight context gathering (pairs with `@context-discovery`)

## Collections

| Collection | Path | Content |
|---|---|---|
| `docs` | `docs/` | RFCs, handovers, design docs |
| `skills` | `.agent/skills/` | All 18+ agent skill definitions |

## Search Commands

### Recommended: Hybrid Search (best quality)

```bash
qmd query "grid system coordinate conversion" -c docs
qmd query "dependency injection registration" -c skills
qmd query "combat turn order" -c docs -c skills   # search both
```

### Fast: Keyword Search (BM25 only)

```bash
qmd search "VContainer LifetimeScope" -c skills
qmd search "RFC-001" -c docs
```

### Semantic: Vector Search

```bash
qmd vsearch "how to handle async operations without coroutines" -c skills
```

## Output Options

| Flag | Effect |
|---|---|
| `-n 10` | Return 10 results (default: 5) |
| `--files` | File paths only |
| `--full` | Include complete document body |
| `--json` | JSON output for programmatic use |
| `--min-score 0.4` | Filter by relevance threshold (0-1) |
| `--all` | Return all matches |

## Document Retrieval

```bash
# Get a specific document by path
qmd get "rfcs/001-grid-system.md" -c docs

# Get by document ID (returned in search results)
qmd get "#abc123"

# Batch retrieve matching files
qmd multi-get "rfcs/*.md" -c docs
```

## Maintenance

### Re-index After File Changes

```bash
qmd update          # Re-index from filesystem
qmd embed           # Update embeddings for new/changed docs
```

### Add New Collection

```bash
qmd collection add <path> --name <name> --mask "**/*.md"
qmd context add qmd://<name> "<description>"
qmd embed
```

### Check Status

```bash
qmd collection list    # Show all collections
qmd status             # Index health and model info
```

## MCP Integration

QMD exposes an MCP server for direct agent access:

```bash
# Start MCP server (stdio mode — for Claude Code config)
qmd mcp

# Start HTTP mode (background daemon)
qmd mcp --http --daemon
qmd mcp stop
```

**Claude Code settings.json:**
```json
{
  "mcpServers": {
    "qmd": {
      "command": "qmd",
      "args": ["mcp"]
    }
  }
}
```

MCP tools exposed: `query`, `get`, `multi_get`, `status`.

## Workflow Integration

### With @context-discovery

Before implementing any RFC, run a hybrid search to gather context:

```bash
# Find all docs related to the feature
qmd query "overworld map navigation" -c docs -c skills --full

# Then feed results into context-discovery's ContextReport
```

### With @docling

For non-markdown sources (PDFs, DOCX, PPTX), convert with Docling first, then index:

```bash
docling input.pdf --output docs/converted/
qmd update && qmd embed
```

## Important Notes

- **First run** downloads ~2GB of GGUF models (embedding, reranker, query expansion)
- **Never modify** `~/.cache/qmd/index.sqlite` directly
- Models stay loaded in VRAM across MCP requests; dispose after 5 min idle
- Chunking: 900 tokens/chunk, 15% overlap, prefers markdown heading boundaries
