---
name: repomix
description: Use when packing repo files into a single AI-friendly context file — for external LLM review, documentation generation, or context window optimization.
category: 04-tooling
layer: tooling
related_skills:
  - "@context-discovery"
  - "@qmd-search"
  - "@docling"
---

# Repomix Skill

[Repomix](https://github.com/yamadashy/repomix) consolidates repository code into a single, AI-optimized file. Use it to create codebase snapshots for LLM consumption, external AI review, or documentation generation.

## When to Use

- Preparing codebase context for an external LLM (Claude, ChatGPT, etc.)
- Generating a snapshot of a package or subsystem for review
- Creating compressed code summaries to fit within token limits
- Sharing project structure and code with stakeholders
- Feeding code to AI for test generation, refactoring suggestions, or docs
- Archiving a point-in-time view of a module

## CLI Usage

### Basic Packing

```bash
# Pack entire repo
repomix

# Pack specific directory (e.g., a single package)
repomix project/packages/com.giantcroissant.game.grid

# Pack with glob selection
repomix --include "Runtime/**/*.cs"

# Pack remote repo
repomix --remote yamadashy/repomix
repomix --remote https://github.com/owner/repo
```

### Output Formats

```bash
# XML (default — best for AI parsing)
repomix --style xml

# Markdown (human-readable)
repomix --style markdown

# JSON (programmatic use)
repomix --style json

# Custom output path
repomix --output docs/snapshots/grid-snapshot.xml
```

### Token Optimization

```bash
# Compress: extract only essential code structure via Tree-sitter
repomix --compress

# Compress a specific package for LLM context
repomix project/packages/com.giantcroissant.game.grid --compress --output grid-compressed.xml
```

### File Selection

```bash
# Include only C# runtime files
repomix --include "Runtime/**/*.cs"

# Exclude tests and editor scripts
repomix --ignore "Tests/**,Editor/**"

# Pipe file list from stdin
git diff --name-only main | repomix --stdin
```

### Git Context

```bash
# Include recent commit history
repomix --include-logs

# Include last 20 commits
repomix --include-logs-count 20

# Include diff information
repomix --include-diffs
```

## Configuration File

Create `repomix.config.json` for persistent settings:

```bash
repomix --init
```

Example config for this project:

```json
{
  "include": ["project/packages/**/*.cs", "project/packages/**/package.json"],
  "ignore": ["**/Tests/**", "**/Editor/**", "**/*.meta"],
  "output": {
    "style": "xml",
    "filePath": "repomix-output.xml"
  }
}
```

## Workflow: Package Snapshot for AI Review

```bash
# 1. Pack a single game package (compressed)
repomix project/packages/com.giantcroissant.game.grid \
  --compress \
  --include "Runtime/**/*.cs,package.json" \
  --style xml \
  --output docs/snapshots/grid-review.xml

# 2. Token count is shown in output — check it fits context window

# 3. Feed to external AI or attach to a conversation
```

## Workflow: Full Project Overview

```bash
# Pack all packages with compression for high-level review
repomix project/packages \
  --compress \
  --ignore "**/Tests/**,**/*.meta" \
  --style markdown \
  --output docs/snapshots/project-overview.md
```

## Workflow: Changed Files Only

```bash
# Pack only files changed since main branch
git diff --name-only main | repomix --stdin --style xml --output review.xml

# Pack files from a specific commit range
git diff --name-only HEAD~5..HEAD | repomix --stdin --compress
```

## Security

- **Secretlint** built-in — automatically detects API keys, passwords, tokens
- Respects `.gitignore`, `.ignore`, and `.repomixignore`
- Review output before sharing externally

## Important Notes

- Default output format is XML — best for AI comprehension
- `--compress` uses Tree-sitter to extract signatures, types, and structure while dropping implementation details — great for fitting large codebases into context
- Token counts are reported per-file and total — use to estimate LLM context usage
- Output includes directory structure tree, file metadata, and content
- Already installed globally via npm
