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
│   ├── shared/                 # Single source of truth shared by both Godot projects
│   │   ├── addons/             # Vendored Godot addons (linked into both host projects)
│   │   ├── lib/                # Shared GDScript: Resource defs, enums, contracts
│   │   ├── shaders/            # Shared shaders
│   │   ├── data/               # Static registries + generated content_manifest.json
│   │   └── content/            # Source content authored in content-app
│   │       └── {kind}/{bundle-id}/  # e.g. hud/hud-core, enemies/enemies-forest
│   ├── hosts/
│   │   ├── complete-app/       # Thin runtime "player" — boot, ContentManager, WS
│   │   └── content-app/        # Authoring + preview harness, builds PCKs
│   └── server/                 # pnpm workspace root
│       ├── biome.json
│       ├── pnpm-workspace.yaml
│       └── packages/
│           └── game-server/    # WebSocket server
├── build/
│   └── _artifacts/             # Versioned build output (gitignored)
│       ├── pck/                # Built content bundles ({id}@{hash}.pck)
│       ├── {version}/web/      # Godot web export (includes pck/ subdir)
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

`project/hosts/{complete-app,content-app}/{addons,lib,shaders,data,content}` are NOT real directories — they are symlinks (Mac/Linux) or directory junctions (Windows) into `project/shared/`, recreated by `task share:link` (called from `task setup`). **Edit files under `project/shared/`, never through the host-project links** — a pre-commit hook rejects writes to the linked paths.

## Key Commands

```bash
task setup                        # Install deps + share:link + setup:godot + templates
task share:link                   # (Re)create cross-platform links from host projects to shared/
task setup:godot                  # Seed each host project's .godot/ cache headlessly
task build                        # Export Godot web build (includes pck/) to build/_artifacts/
task dev                          # Start WS server (nodemon) + static file server
task serve                        # Serve latest web build only
task serve:https                  # Serve over HTTPS (cross-machine testing)
task lint                         # biome + ruff
task format                       # biome format + ruff format
task version                      # Print current GitVersion SemVer
task clean                        # Remove all build artifacts
task changelog                    # Generate CHANGELOG.md via git-cliff
task test                         # Run all test suites (pytest, vitest, GUT, playwright)
task test:python                  # Python tests only
task test:server                  # Game server tests only
task test:godot                   # Godot unit tests only (headless)
task test:e2e                     # Browser E2E tests only (requires web build)
task tileset:preprocess -- {biome}    # Slice ComfyUI output into clean atlas
task pck:manifest -- {location}       # Generate location PCK manifest from LDtk data
task pck:build -- {location}          # Full location PCK build (manifest + Godot pack)
task content:build -- {bundle-id}     # Build a single content bundle into a PCK
task content:build:all                # Build every bundle under shared/content/**/bundle.json
task content:manifest                 # Regenerate shared/data/content_manifest.json
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
5. **No hardcoded adjustable values** — tile sizes, grid dimensions, speeds, cooldowns, zoom levels, and any gameplay-tunable constant must be read from data (LDtk project, config files, scene metadata) or defined in a single shared config source. Never scatter magic numbers across files. If a value could reasonably change, it must have exactly one source of truth.
6. **Build artifacts never committed** — `build/_artifacts/` is gitignored
7. **GDScript follows Godot style guide** — tabs, snake_case
8. **JS uses `const`/`let`** — never `var`
9. **All documentation in `vault/`** — no `docs/` directory

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

- Two cooperating Godot 4.6.2 projects:
  - `project/hosts/complete-app/` — thin runtime "player" shipped to web. Contains kernel scripts (boot, ContentManager, autoloads, WS client) and the boot scene only. All gameplay content loads at runtime via PCK bundles.
  - `project/hosts/content-app/` — authoring + preview harness. Contains the `preview/` scenes that mock the kernel for isolated iteration on widgets/enemies/NPCs. Builds PCKs into `build/_artifacts/pck/`.
- Godot binary: env var `GODOT_PATH` or default at `/Users/apprenticegc/Work/lunar-horse/tools/Godot.app/Contents/MacOS/Godot`
- Export templates must be installed (`task setup` handles this)
- Never commit `.godot/` cache directory (pre-commit hook enforces this)
- Web export goes through `task build`, not the Godot editor
- After cloning or any change to autoloads/class_name globals, run `task setup:godot` to seed `.godot/uid_cache.bin` for both host projects. Without it, headless commands (`task test:godot`, `task build`) fail with "Unrecognized UID" cascading parse errors.

## Cross-Platform Sharing

`project/shared/` is the single source of truth for addons, shared GDScript libs, shaders, registries, and source content. Both host projects reference it via OS-appropriate links created by `task share:link` (called from `task setup`):

- macOS / Linux: relative POSIX symlinks (`ln -s`)
- Windows: directory junctions (`mklink /J`) — no admin or developer mode required

Only `content-app` links `shared/content/` (importing the same source from two projects creates `.import` ownership conflicts). The `complete-app` runtime never sees raw source content — it loads built PCKs.

A pre-commit hook (`shared-link-guard`) rejects any commit with files inside the linked paths. Edit files under `project/shared/` directly.

## Content Pipeline

| Command | Purpose |
|---|---|
| `task content:build -- {bundle-id}` | Build one content bundle into `build/_artifacts/pck/{id}@{hash}.pck`, regenerate manifest |
| `task content:build:all` | Iterate every `bundle.json` and build each |
| `task content:manifest` | Regenerate `project/shared/data/content_manifest.json` from existing PCKs |

Authoring workflow:
1. Open `project/hosts/content-app/` in Godot
2. Edit/add resources under `res://content/{kind}/{bundle-id}/`
3. Use `res://preview/preview_main.tscn` to iterate (mock kernel, isolated harness)
4. `task content:build -- {bundle-id}` packs the bundle
5. Test in `complete-app` (or the web build)

Bundle declaration (`bundle.json` per bundle):
```json
{
  "id": "hud-core",
  "kind": "hud",
  "policy": "eager",
  "deps": [],
  "include": ["**/*.tres", "**/*.tscn", "**/*.gd", "*.tres", "*.tscn", "*.gd"],
  "provides": { "widgets": ["activity_log_panel", "minimap"] }
}
```

`HudWidgetDefinition.tres` filenames must equal the widget id used by `ContentManager.get_hud_widget(id)` — e.g., the bundle that provides `"minimap"` saves its definition as `minimap.tres`, not `mini_map_panel.tres`.

## Addon Conventions

- Addons live in `project/shared/addons/` (linked into both host projects' `addons/` via `task share:link`)
- **Web export compatibility is mandatory** — only install addons that are pure GDScript or include WASM binaries. No native-only GDExtensions
- Before installing an addon, check for `.gdextension`, `.so`, `.dll`, `.dylib` files — if present without `.wasm` counterparts, the addon will break web export
- Addons are committed to the repo (no package manager) — pin to a specific version tag
- Enable addons in `project.godot` under `[editor_plugins]`
- **Headless-mode quirk:** addon `_enable_plugin` / `_disable_plugin` callbacks must NOT call `add_autoload_singleton` / `remove_autoload_singleton`. Headless mode never enables plugins, so the autoload entry would be missing. Declare the autoload statically in `project.godot [autoload]` instead. Our GUIDE addon was patched accordingly (commit `f94129c`).

### Installed Addons

| Addon | Version | Source | Web Compatible | Notes |
|---|---|---|---|---|
| Phantom Camera | 0.9.4.2 | [ramokz/phantom-camera](https://github.com/ramokz/phantom-camera) | Yes (pure GDScript) | Cinematic 2D/3D camera system |
| Beehave | 2.9.2 | [bitbrain/beehave](https://github.com/bitbrain/beehave) | Yes (pure GDScript) | Behaviour tree AI. Auto-registers autoloads (metrics, debugger) |
| Dialogue Manager | 3.9.1 | [nathanhoad/godot_dialogue_manager](https://github.com/nathanhoad/godot_dialogue_manager) | Yes (pure GDScript) | Dialogue system with `.dialogue` files, compiler, balloon UI |
| GECS | 7.1.0 | [csprance/gecs](https://github.com/csprance/gecs) | Yes (pure GDScript) | ECS framework. `ECS` autoload errors in headless build (harmless) |
| G.U.I.D.E | 0.9.1 | [godotneers/G.U.I.D.E](https://github.com/godotneers/G.U.I.D.E) | Yes (pure GDScript) | Input mapping, context-based. Minor `cleanup` error in headless export (harmless) |
| GUT | 9.6.0 | [bitwes/Gut](https://github.com/bitwes/Gut) | Yes (pure GDScript) | Unit test framework. Headless runner via `gut_cmdln.gd` |

## Server Conventions

- All Node.js code under `project/server/`
- pnpm workspaces — new packages go in `project/server/packages/`
- Package naming: `@legend-dad/<package-name>`
- ES modules (`"type": "module"` in package.json)
- nodemon for dev, entry point is always `src/index.js`

## Testing

| Layer | Runner | Command | Location |
|---|---|---|---|
| All | Taskfile | `task test` | All suites sequentially |
| Python | pytest | `task test:python` | `tests/` |
| Node.js | Vitest | `task test:server` | `project/server/packages/game-server/src/__tests__/` |
| Godot | GUT | `task test:godot` | `project/hosts/complete-app/tests/` |
| Browser E2E | Playwright | `task test:e2e` | `project/server/packages/e2e/tests/` |

- `task test:server` runs Vitest tests against the game server (MCP transport, agent integration)
- `task test:e2e` auto-starts servers if not already running (requires web build from `task build`)
- Agent integration tests require API keys (`ZAI_API_KEY` or `ALIBABA_API_KEY`) — skipped otherwise
- Playwright uses Chromium only — game targets web browsers
- Screenshots stored in `build/_artifacts/latest/screenshots/`
- Replay data stored in `build/_artifacts/{version}/replay/`
