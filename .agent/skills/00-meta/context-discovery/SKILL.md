---
name: context-discovery
description: Mandatory pre-flight analysis before any implementation. Scans project state, checks dependencies, verifies Godot and server configuration, and produces a ContextReport. Run this FIRST before loading domain skills.
category: 00-meta
layer: governance
always_active: true
related_skills:
  - "@rfc-orchestrator"
  - "@validation-guard"
---

# Context Discovery

Run this skill **before** starting any implementation work. It produces a ContextReport that gates which skills can be applied and surfaces blockers early.

## When to Run

- Before implementing any feature or RFC
- Before making cross-system changes (Godot + server)
- When resuming work after a break (project state may have changed)
- Before creating a new workspace package

## Discovery Steps

Execute these checks in order. Each step produces a section of the ContextReport.

### Step 1: Project State

```
Checks:
- [ ] Git status (uncommitted changes, current branch)
- [ ] GitVersion output (current SemVer)
- [ ] Worktree status (any active worktrees)
- [ ] Pre-commit hooks installed
```

### Step 2: Godot Project Health

```
Checks:
- [ ] Godot version matches project (4.6.x)
- [ ] Export templates installed for current version
- [ ] export_presets.cfg exists and has Web preset
- [ ] Last successful web build (check build/_artifacts/latest symlink)
```

### Step 3: Server Package Inventory

```
Checks:
- [ ] pnpm workspace packages (ls project/server/packages/)
- [ ] Each package's dependencies (read package.json)
- [ ] pnpm-lock.yaml is up to date (pnpm install --frozen-lockfile)
- [ ] Server starts cleanly (node project/server/packages/game-server/src/index.js)
```

### Step 4: Tooling Health

```
Checks:
- [ ] task --list (Taskfile valid)
- [ ] biome check passes (cd project/server && pnpm run lint)
- [ ] ruff check passes (ruff check scripts/)
- [ ] git-cliff works (git-cliff --unreleased)
```

### Step 5: Documentation State

```
Checks:
- [ ] Obsidian vault exists (vault/)
- [ ] Design docs present (vault/design/, vault/architecture/)
- [ ] Specs and plans (docs/superpowers/specs/, docs/superpowers/plans/)
```

## ContextReport Format

After running all checks, produce a summary in this format:

```markdown
## ContextReport — [date]

### Environment
- Godot: [version]
- Node.js: [version]
- Python: [version]
- GitVersion: [SemVer]
- Branch: [branch name]
- Uncommitted changes: [yes/no]
- Active worktrees: [list or none]

### Godot Project
| Check | Status |
|---|---|
| Export templates | installed/missing |
| Web export preset | present/missing |
| Last build | [version] or never |

### Server Packages
| Package | Version | Status |
|---|---|---|
| @legend-dad/game-server | 0.0.1 | ok |
| ... | ... | ... |

### Tooling
| Tool | Status |
|---|---|
| Taskfile | ok/error |
| biome | ok/[N] errors |
| ruff | ok/[N] errors |
| pre-commit | installed/missing |
| git-cliff | ok/error |

### Documentation
- Design docs: [count] files
- Specs: [count] files
- Plans: [count] files

### Blockers
- [list any blockers that prevent proceeding]

### Recommendations
- [what to work on next based on current state]
```

## How to Execute

| Check | Tool/Command |
|---|---|
| Git status | `git status`, `git branch`, `git worktree list` |
| GitVersion | `dotnet-gitversion /showvariable SemVer` |
| Godot version | `$GODOT_PATH --version` |
| Export templates | Check `~/Library/Application Support/Godot/export_templates/` |
| Server health | `cd project/server && pnpm install --frozen-lockfile` |
| Lint checks | `task lint` |
| Taskfile | `task --list` |

## Post-Discovery

Once the ContextReport is produced:

1. Check for **blockers** — resolve before proceeding
2. Consult `@rfc-orchestrator` — determine which skills to load
3. Load the required skills
4. Begin implementation

## Related Skills

- `@rfc-orchestrator` (00-meta) — consult after discovery to plan implementation
- `@validation-guard` (00-meta) — run after implementation to verify compliance
