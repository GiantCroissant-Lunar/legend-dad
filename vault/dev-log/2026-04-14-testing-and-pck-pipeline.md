---
date: 2026-04-14
agent: claude-code
branch: main
version: 0.1.0-pck-tileset-pipeline.1
tags: [dev-log, testing, comfyui, pck, tileset, pipeline]
---

# Session Dev-Log — 2026-04-14

## What Was Built

### Testing Infrastructure (13 commits)

Set up unified testing across all project layers:

- **Vitest** for game-server integration tests — migrated 19 assertions from test-mcp.js into proper test suite (6 test cases). Agent integration test made opt-in (`RUN_AGENT_TESTS=1`) due to LLM API flakiness.
- **Playwright** E2E package (`@legend-dad/e2e`) with smoke test (canvas + WS handshake) and MCP round-trip test. Auto-starts servers via `webServer` config.
- **GUT v9.6.0** scaffold for Godot unit tests (1 example test). Required upgrade from v9.3.0 for Godot 4.6.2 compatibility.
- **Taskfile orchestration**: `task test` (all), `task test:{python,server,godot,e2e}`

Old test-mcp.js and test-agent.js deleted after migration. Shared helpers extracted: mock-godot.js and test-server.js (random port allocation).

### ComfyUI Pipeline Fix (1 commit)

Fixed critical bugs in the ComfyUI headless pipeline:
- Rewrote `workflow-loader.mjs` editor→API conversion — was passing PrimitiveNode to API (doesn't exist), not wiring links, missing widget mappings for PixelArt-Detector nodes
- Fixed tileset-runner override targets (CLIPTextEncode 5/6 not PrimitiveNode 3/4)
- Fixed download filename collisions (prefixed with stage: raw_, pixelated_, grayscale_)
- Fixed PixelArtDetectorConverter palette enum validation

### ComfyUI Mac Setup

- Installed ComfyUI-PixelArt-Detector custom node + pyclustering deps
- Created grayscale-16.png palette swatch (16×1)
- Verified full 3-stage generation: raw → pixelated → grayscale quantized

### PCK Tileset Pipeline (8 commits)

End-to-end pipeline from ComfyUI grayscale tiles to Godot runtime:

- **`scripts/tileset_preprocess.py`** — slices 512×512 ComfyUI output into clean 32px tile atlas
- **`scripts/pck_manifest.py`** — reads LDtk IntGrid data, generates manifest.json with tile properties (walkability, type)
- **`scripts/pck_builder.gd`** — Godot headless tool script: reads manifest, creates TileSet resource with atlas source + custom data layers, packs into .pck
- **`scripts/location_manager.gd`** — autoload singleton: loads/unloads location PCKs, applies palette shader, swaps era palettes, falls back to TilesetFactory when PCK unavailable
- **`data/locations.json`** — location registry (3 locations mapped to biomes)
- **`scripts/run_godot_checked.py`** — vendored from project-agent-union, catches Godot false-green exits
- Taskfile commands: `tileset:preprocess`, `pck:manifest`, `pck:build`

Pipeline verified E2E: `task pck:build -- whispering-woods` produces a 3.6 MB PCK with tileset + palettes.

## Commits (this session)

### Testing Infrastructure
- `chore: add vitest to game-server package`
- `test: extract reusable mock-godot WS client helper`
- `test: extract test-server helper with random port allocation`
- `test: migrate MCP transport tests to vitest`
- `test: migrate agent integration test to vitest (skip without API key)`
- `chore: remove old test scripts, fix agent test flakiness`
- `feat: add @legend-dad/e2e playwright package with smoke and MCP round-trip tests`
- `chore: upgrade GUT to v9.6.0 for Godot 4.6.2 compatibility`
- `test: add GUT scaffold test for Godot`
- `feat: add unified test commands to taskfile`
- `fix: make agent integration test opt-in (RUN_AGENT_TESTS=1)`
- `docs: update AGENTS.md with testing infrastructure`

### ComfyUI Fix
- `fix: comfyui pipeline — editor→API conversion, node wiring, download naming`

### PCK Pipeline
- `chore: vendor run_godot_checked.py from project-agent-union`
- `feat: add tileset preprocessing script with tests`
- `feat: add PCK manifest generator with LDtk IntGrid data`
- `feat: add location registry for PCK loading`
- `feat: add LocationManager autoload with PCK loading and fallback`
- `feat: add Godot headless PCK builder tool script`
- `feat: integrate LocationManager into main.gd with fallback`
- `feat: add tileset:preprocess and pck:build taskfile commands`

## Test Results

| Suite | Count | Status |
|---|---|---|
| pytest | 70 | All pass |
| vitest | 6 + 1 skipped | All pass (agent skipped without RUN_AGENT_TESTS=1) |
| GUT | 1 | Pass |
| Playwright | Not run (needs web build) | Ready |

## Decisions

1. **GUT v9.6.0** over v9.3.0 — v9.3.0 has `GutUtils` class_name errors in Godot 4.6.2 headless
2. **Agent test opt-in** — real LLM API calls are slow and non-deterministic, shouldn't block routine `task test:server`
3. **Approach C (hybrid)** for PCK pipeline — Python for image processing + LDtk data, Godot headless for TileSet resource creation (guaranteed format compatibility)
4. **One PCK per location** — self-contained (tileset, atlas, palettes), loaded/unloaded as player moves
5. **TilesetFactory as permanent fallback** — game always runs even without generated tilesets

## Known Issues

1. **Grayscale output has warm tones** — PixelArt-Detector's palette conversion uses NES fallback instead of grayscale-16 palette from paletteList. Needs tuning in the ComfyUI workflow nodes.
2. **PCK unload limitation** — Godot 4.x doesn't have a clean `unload_resource_pack()` API. Resources stay in memory until scene change. Acceptable for current scope.
3. **Mastra `onsessioninitialized` override** — still outstanding from prior session (see 2026-04-13 handover)

## Environment

- macOS (juis-mac-mini), Mac Mini M4
- Node v25.8.0, pnpm 10.18.0
- Godot 4.6.2
- ComfyUI running at localhost:8188 (SDXL + pixel-art-xl LoRA)
- SurrealDB on port 6480
