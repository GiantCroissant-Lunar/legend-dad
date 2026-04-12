# AGENTS.md — legend-dad

Project conventions for AI coding agents (Claude, Copilot, Codex, etc.).

## Project Overview

Godot 4.6 web game with a Node.js WebSocket server. Intended for browser-based play with automated agent testing via Playwright.

## Tech Stack

| Layer | Technology |
|---|---|
| Game engine | Godot 4.6.2 (GDScript, no mono) |
| Game server | Node.js (ws), pnpm workspaces |
| Utility scripts | Python 3.11+ |
| JS/TS linting | biome (config at `project/server/biome.json`) |
| Python linting | ruff (config at `pyproject.toml`) |
| Task runner | Taskfile.yml (go-task) |
| Versioning | GitVersion (trunk-based, `GitVersion.yml`) |
| Changelog | git-cliff (`cliff.toml`) |
| Pre-commit | biome, ruff, trailing whitespace, .godot guard |
| Documentation | Obsidian vault (`vault/`) |

## Project Structure

```
legend-dad/
├── project/
│   ├── hosts/complete-app/     # Godot 4.6 project
│   └── server/                 # pnpm workspace root
│       ├── biome.json
│       ├── pnpm-workspace.yaml
│       └── packages/
│           └── game-server/    # WebSocket server
├── build/
│   └── _artifacts/             # Versioned build output (gitignored)
│       ├── {version}/web/      # Godot web export
│       └── latest -> {version} # Symlink to latest build
├── scripts/                    # Cross-platform utility scripts
├── vault/                      # Obsidian vault — single source of truth
│   ├── architecture/           # System architecture docs
│   ├── design/                 # Game design docs
│   ├── references/             # External references
│   ├── specs/                  # Feature specs
│   ├── plans/                  # Implementation plans
│   ├── world/                  # World bible / lore
│   └── dev-log/                # Session logs from all agents
├── .agent/skills/              # Agent skill definitions
├── Taskfile.yml                # All dev commands
├── GitVersion.yml              # Versioning config
└── AGENTS.md                   # This file
```

## Key Commands

```bash
task setup          # Install deps, download Godot export templates, install pre-commit
task build          # Export Godot web build to build/_artifacts/{version}/
task dev            # Start WS server (nodemon) + static file server
task serve          # Serve latest web build only
task serve:https    # Serve over HTTPS (cross-machine testing)
task lint           # biome + ruff
task format         # biome format + ruff format
task version        # Print current GitVersion SemVer
task clean          # Remove all build artifacts
task changelog      # Generate CHANGELOG.md via git-cliff
```

## Branching & Versioning

- **Trunk-based**: `main` is the trunk
- **Feature branches**: `feature/*` — version becomes `0.1.0-feature-name.N`
- **Fix branches**: `fix/*` — version becomes `0.1.0-fix-name.N`
- **Tags**: Create `v0.1.0` tag for releases
- **Worktrees**: Use `git worktree` for parallel feature work

## Mandatory Rules

1. **Conventional commits** — all commits use `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `ci:` prefixes
2. **Pre-commit must pass** — never skip hooks (`--no-verify` is forbidden)
3. **biome + ruff must pass** before committing
4. **No hardcoded ports or secrets** in source — use env vars
5. **Build artifacts never committed** — `build/_artifacts/` is gitignored
6. **GDScript follows Godot style guide** — tabs, snake_case
7. **JS uses `const`/`let`** — never `var`
8. **All documentation in `vault/`** — no `docs/` directory

## Ports

| Service | Port | Configurable via |
|---|---|---|
| Static file server | 8080 | `SERVE_PORT` env var |
| WebSocket server | 3000 | `PORT` env var |
| HTTPS static server | 8443 | `SERVE_PORT` env var |

## Agent Skills

Agent skills live in `.agent/skills/` organized by numbered categories:
- `00-meta` — governance (context-discovery, validation-guard, autoloop, etc.)
- `03-presentation` — UI/UX design
- `04-tooling` — browser automation, doc search, repomix
- `05-world` — world bible, lore generation

Always run `@context-discovery` before implementation work and `@validation-guard` after.

## Session Logging (Mandatory)

**Every agent must write a dev-log entry before ending a session.** See `@dev-log` skill for full format.

- Write to: `vault/dev-log/YYYY-MM-DD-{slug}.md`
- Include: summary, commits, decisions, blockers, next steps
- Set `agent:` field to identify which agent wrote the entry
- Run `dotnet-gitversion /showvariable SemVer` for the version field
- This applies to all agents: Claude Code, Codex, Copilot, Cursor, human

## Godot Conventions

- Godot project lives at `project/hosts/complete-app/`
- Godot binary: env var `GODOT_PATH` or default at `/Users/apprenticegc/Work/lunar-horse/tools/Godot.app/Contents/MacOS/Godot`
- Export templates must be installed (`task setup` handles this)
- Never commit `.godot/` cache directory (pre-commit hook enforces this)
- Web export goes through `task build`, not the Godot editor

## Server Conventions

- All Node.js code under `project/server/`
- pnpm workspaces — new packages go in `project/server/packages/`
- Package naming: `@legend-dad/<package-name>`
- ES modules (`"type": "module"` in package.json)
- nodemon for dev, entry point is always `src/index.js`

## Testing

- Playwright for browser-based game verification
- Server on `localhost:8080` (secure context, SharedArrayBuffer works)
- For cross-machine testing use `task serve:https`
- Screenshots stored in `build/_artifacts/{version}/screenshots/`
- Replay data stored in `build/_artifacts/{version}/replay/`
