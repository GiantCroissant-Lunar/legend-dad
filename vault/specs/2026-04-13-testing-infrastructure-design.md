---
date: 2026-04-13
status: approved
tags: [testing, infrastructure, spec]
---

# Testing Infrastructure Design

## Overview

Set up a unified testing infrastructure across all layers of the legend-dad project: Python utility scripts, Node.js game server, Godot game logic, and browser E2E verification.

## Current State

| Layer | Runner | Tests | Status |
|---|---|---|---|
| Python (scripts/) | pytest | 32 | Working |
| Node.js (game-server/) | Custom scripts | 2 scripts (test-mcp.js, test-agent.js) | Manual, no runner |
| Godot (complete-app/) | None | 0 | No tests |
| Browser E2E | None | 0 | No tests |
| Unified command | None | N/A | No `task test` |

## Target State

| Layer | Runner | Location | Tests |
|---|---|---|---|
| Python | pytest | `tests/` | Existing 32 (unchanged) |
| Node.js | Vitest | `project/server/packages/game-server/src/__tests__/` | Migrated from test-mcp.js + test-agent.js |
| Godot | GUT v9 | `project/hosts/complete-app/tests/` | Scaffold (1 example) |
| Browser E2E | Playwright | `project/server/packages/e2e/tests/` | Smoke + MCP round-trip |
| Unified | Taskfile | `Taskfile.yml` | `task test` runs all |

## Architecture: Monorepo-Level Orchestration (Approach A)

Each test runner owns its scope within its natural home directory. The Taskfile orchestrates all suites. Playwright lives in a dedicated pnpm workspace package (`@legend-dad/e2e`).

```
legend-dad/
├── project/
│   ├── hosts/complete-app/
│   │   ├── addons/gut/                  # GUT addon (new)
│   │   └── tests/                       # GUT tests (new)
│   │       ├── test_example.gd
│   │       └── .gutconfig.json
│   └── server/
│       ├── packages/
│       │   ├── game-server/
│       │   │   ├── vitest.config.js     # New
│       │   │   └── src/__tests__/       # New
│       │   │       ├── helpers/
│       │   │       │   ├── mock-godot.js
│       │   │       │   └── test-server.js
│       │   │       ├── mcp-transport.test.js
│       │   │       └── agent.test.js
│       │   └── e2e/                     # New package
│       │       ├── package.json
│       │       ├── playwright.config.js
│       │       └── tests/
│       │           ├── smoke.spec.js
│       │           └── mcp-roundtrip.spec.js
│       └── pnpm-workspace.yaml          # Already includes packages/*
├── tests/                               # Existing pytest (unchanged)
└── Taskfile.yml                         # New test:* tasks
```

## Component Details

### 1. Vitest — Server Integration Tests

**Location:** `project/server/packages/game-server/`

**Config:** `vitest.config.js` — ESM, default timeout 15s (tests spin up real HTTP/WS servers).

**Shared helpers extracted from existing test scripts:**

- `src/__tests__/helpers/mock-godot.js` — Mock Godot WS client: connects, handshakes, responds to commands (get_state, move, interact, switch_era). Both test-mcp.js and test-agent.js duplicate this logic today.
- `src/__tests__/helpers/test-server.js` — Boots an isolated HTTP + WS + MCP server on a random available port, returns a cleanup function. Eliminates hardcoded :3098/:3099 ports.

**Test files:**

- `mcp-transport.test.js` — Migrates 19 assertions from test-mcp.js into describe/it blocks. Covers: MCP initialize, tools/list, get_state, move, poll_events, poll drains queue.
- `agent.test.js` — Migrates test-agent.js. Tagged with a custom `integration` marker. Skipped unless API key env vars are present (ZAI_API_KEY or ALIBABA_API_KEY). Tests agent tool-calling loop with mock Godot.

**Dependencies added:** `vitest` (devDependency in game-server).

**Scripts in package.json:** `"test": "vitest run"`, `"test:watch": "vitest"`.

**Cleanup:** Delete `src/test-mcp.js` and `src/test-agent.js` after migration is verified.

### 2. Playwright — Browser E2E Tests

**Location:** `project/server/packages/e2e/` (new pnpm workspace package `@legend-dad/e2e`).

**Dependencies:** `@playwright/test` (devDependency).

**Config:** `playwright.config.js`
- Chromium only (game targets web browsers)
- Base URL: `http://localhost:8080`
- `webServer` auto-starts both servers before tests:

```js
webServer: [
  {
    command: 'node src/index.js',
    cwd: '../game-server',
    port: 3000,
    reuseExistingServer: true,
  },
  {
    command: 'node ../../../../scripts/serve_web.js ../../../../build/_artifacts/latest/web',
    port: 8080,
    reuseExistingServer: true,
  },
]
```

If servers are already running (from `task dev`), Playwright reuses them.

**Test files:**

- `smoke.spec.js` — Navigates to localhost:8080, waits for the Godot canvas element to render, asserts WS connection was established. 30s timeout for WASM load.
- `mcp-roundtrip.spec.js` — Performs smoke check, then makes MCP HTTP calls (initialize, tools/list, call move) via Playwright's `request` context, verifies Godot state change is reflected.

**Screenshots:** Saved to `build/_artifacts/latest/screenshots/` (already gitignored).

### 3. GUT — Godot Unit Tests (Scaffold Only)

**Installation:** GUT v9.x from bitwes/Gut — pure GDScript, web-export compatible. Installed to `project/hosts/complete-app/addons/gut/`.

**Config:** `.gutconfig.json` at `project/hosts/complete-app/.gutconfig.json`:

```json
{
  "dirs": ["res://tests/"],
  "prefix": "test_",
  "suffix": ".gd",
  "include_subdirs": true
}
```

**Scaffold test:** `project/hosts/complete-app/tests/test_example.gd` — one trivial test extending `GutTest`, asserts true, proves the runner works.

**Headless runner command:**

```bash
$GODOT_PATH --headless --path project/hosts/complete-app -s addons/gut/gut_cmdln.gd -gexit
```

**Scope:** Scaffold only. No game logic tests yet. Expand once ECS systems and GameActions bus are stable.

### 4. Taskfile — Unified Commands

```yaml
test:
  desc: Run all test suites
  cmds:
    - task: test:python
    - task: test:server
    - task: test:godot
    - task: test:e2e

test:python:
  desc: Run Python tests (pytest)
  cmds:
    - python3 -m pytest tests/ -v

test:server:
  desc: Run game-server integration tests (vitest)
  dir: "{{.GAME_SERVER_DIR}}"
  cmds:
    - pnpm test

test:godot:
  desc: Run Godot unit tests (GUT, headless)
  cmds:
    - >-
      {{.GODOT_PATH}} --headless
      --path {{.GODOT_PROJECT_DIR}}
      -s addons/gut/gut_cmdln.gd -gexit

test:e2e:
  desc: Run browser E2E tests (Playwright)
  dir: "project/server/packages/e2e"
  cmds:
    - pnpm exec playwright test
```

**Execution order:** pytest -> vitest -> GUT -> Playwright (fastest first, fail fast on cheap tests).

## Out of Scope

- CI/CD pipeline (future work)
- Test coverage thresholds
- Meaningful GUT tests (beyond scaffold)
- Performance/load testing
- Cross-browser testing (Chromium only for now)

## Dependencies

| Package | Version | Where |
|---|---|---|
| vitest | latest | game-server devDependency |
| @playwright/test | latest | e2e devDependency |
| GUT | v9.x | Godot addon (committed to repo) |
