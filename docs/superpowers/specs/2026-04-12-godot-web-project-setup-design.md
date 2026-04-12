# Godot Web Game Project Setup — Design Spec

**Date:** 2026-04-12
**Status:** Approved for iterative implementation

## Summary

Set up a Godot 4.6 web game project with a Node.js WebSocket server, local dev tooling, and infrastructure for automated browser-based testing (Playwright / agent). The game will eventually be uploaded to itch.io, so the architecture separates the game client (Godot web export) from the game server (WebSocket), allowing both local and itch.io builds to connect to the same server.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│  Static Server   │     │  WebSocket Server │
│  (sirv-cli)      │     │  (Node.js + ws)   │
│  :8080           │     │  :3000            │
│  COOP/COEP hdrs  │     │  nodemon in dev   │
└─────────────────┘     └──────────────────┘
        ▲                        ▲
        │                        │
   ┌────┴────┐          ┌───────┴───────┐
   │ Local   │          │ Both local &  │
   │ build   │          │ itch.io build │
   └─────────┘          │ connect here  │
                        └───────────────┘
        ▲                        ▲
        │                        │
   ┌────┴────────────────────────┴────┐
   │  Playwright / Browser Agent      │
   │  targets either local or itch.io │
   └──────────────────────────────────┘
```

## Project Structure

```
legend-dad/
├── project/
│   ├── hosts/
│   │   └── complete-app/          # Godot 4.6 project
│   │       ├── project.godot
│   │       ├── export_presets.cfg  # Web export preset (generated)
│   │       └── ...
│   └── server/                    # pnpm workspace root
│       ├── package.json           # workspace root
│       ├── pnpm-workspace.yaml
│       ├── biome.json             # JS/TS linting & formatting
│       └── packages/
│           └── game-server/       # WebSocket server package
│               ├── package.json
│               ├── src/
│               │   └── index.js
│               └── nodemon.json
├── builds/
│   └── web/                       # Godot web export output (gitignored)
├── scripts/
│   └── download_templates.py      # Downloads Godot 4.6.2 web export templates
├── vault/                         # Obsidian vault — single source of truth
│   ├── .obsidian/                 # Committed (volatile files gitignored)
│   ├── architecture/
│   ├── design/
│   └── references/
├── Taskfile.yml                   # All dev commands
├── cliff.toml                     # git-cliff changelog config
├── .pre-commit-config.yaml        # biome, ruff, gdformat checks
├── .gitignore
└── pyproject.toml                 # ruff config for Python files
```

## Key Decisions

### Separate Processes (Approach B)
- Static file server (`sirv-cli`) and WebSocket server are separate processes
- Same WS server is used for both local and itch.io testing
- Game client reads WS endpoint from a configurable source (query param or Godot project setting)

### pnpm Workspaces
- All Node.js code lives under `project/server/`
- Root stays clean — no Node files at repo root
- Future packages (shared types, agent scripts) go in `project/server/packages/`

### Tooling
- **Taskfile.yml** — single entry point for all commands
- **biome** — JS/TS linting & formatting (inside `project/server/`)
- **ruff** — Python linting & formatting (config at repo root)
- **pre-commit** — runs biome + ruff on staged files
- **git-cliff** — conventional commit changelog generation
- **nodemon** — auto-restart WS server in dev
- **sirv-cli** — static file server with custom COOP/COEP headers

### Godot Web Export
- Export templates downloaded via `scripts/download_templates.py`
- Template version: 4.6.2.stable
- Downloads from Godot GitHub releases
- Installs to OS-appropriate template directory
- `task build` runs headless export: `$GODOT_PATH --headless --export-release "Web" <output>`
- `GODOT_PATH` env var, defaults to `/Users/apprenticegc/Work/lunar-horse/tools/Godot.app/Contents/MacOS/Godot`

### Obsidian Vault
- `.obsidian/` committed to git for shared settings
- Volatile files gitignored: `workspace.json`, `workspace-mobile.json`, plugin caches

## Taskfile Commands (Initial)

| Command        | Description                                              |
|----------------|----------------------------------------------------------|
| `task setup`   | Install pnpm deps, download export templates, pre-commit install |
| `task build`   | Export Godot project to `builds/web/`                    |
| `task dev`     | Start WS server (nodemon) + static server (sirv) in parallel |
| `task serve`   | Static file server only                                  |
| `task lint`    | Run biome + ruff                                         |
| `task format`  | Run biome format + ruff format                           |
| `task clean`   | Remove `builds/web/` contents                            |

## Ports

| Service          | Port |
|------------------|------|
| Static server    | 8080 |
| WebSocket server | 3000 |

## Cross-Platform

- Scripts in Python or Node.js (not bash)
- Taskfile.yml uses cross-platform commands where possible
- `download_templates.py` detects OS for correct template install path
