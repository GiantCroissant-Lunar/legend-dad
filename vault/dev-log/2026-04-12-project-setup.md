---
date: 2026-04-12
agent: claude-code
branch: main
version: 0.1.0-22
tags: [setup, tooling, godot, server, skills]
---

# Initial project setup — full dev environment from scratch

## Summary

Set up the complete Godot 4.6 web game project from an empty repo. Built the entire dev toolchain (Taskfile, biome, ruff, pre-commit, git-cliff, GitVersion), Node.js WebSocket server with pnpm workspaces, versioned build pipeline, agent skills framework (18 skills ported from ultima-magic), and Obsidian vault structure.

## Changes

- `b5f36cb` docs: add design spec for Godot web project setup
- `1f77df9` docs: add implementation plan for project setup
- `657f920` chore: scaffold Obsidian vault structure
- `a12b190` chore: add pyproject.toml with ruff config
- `325fffb` chore: add root .gitignore and .editorconfig
- `8da4209` feat: add pnpm workspace with game-server package and biome
- `59a745e` feat: add Godot web export preset
- `7ab5694` feat: add Taskfile.yml with dev workflow commands
- `5d52b91` feat: add Python script to download Godot web export templates
- `86cde54` chore: add git-cliff changelog config
- `73720c6` chore: add pre-commit config with biome, ruff, and safety hooks
- `08e652a` test: verify ruff catches lint errors
- `c499361` feat: add GitVersion, rename builds/ to build/, versioned artifact flow
- `8c31ec6` fix: use absolute path for Godot web export output
- `93cf3f8` feat: add agent skills framework (18 skills across 4 categories)
- `8a3a0e3` fix: update world skill vault paths, replace sirv with COOP/COEP server
- `9f1a209` feat: add HTTPS mode to serve_web.js for cross-machine testing
- `54506bd` refactor: merge docs/ into vault/ as single source of truth
- `e55eb47` docs: add AGENTS.md and CLAUDE.md pointer
- `c25381f` feat: add dev-log agent skill for cross-agent session logging

## Decisions

- **Separate static + WS servers** (Approach B) — game client connects to WS server independently, so both local and itch.io builds can use the same server
- **pnpm workspaces under project/server/** — keeps Node.js files out of root, supports future packages (shared types, agent scripts)
- **Custom serve_web.js instead of sirv-cli** — sirv-cli does not support custom response headers; Godot WASM requires COOP/COEP headers for SharedArrayBuffer
- **GitVersion trunk-based** — `main` produces `0.1.0-N`, feature branches produce `0.1.0-feature-name.N`
- **Versioned build artifacts** — `build/_artifacts/{version}/web/` with `latest` symlink, per-version screenshots/replay dirs
- **vault/ as single source of truth** — merged docs/ into vault/, all documentation lives in Obsidian
- **AGENTS.md + CLAUDE.md pointer** — AGENTS.md is agent-agnostic, CLAUDE.md points to it
- **Excluded .agent/ from ruff pre-commit** — upstream skill scripts have lint issues, not our code to fix
- **Tailscale available but HTTPS certs require paid plan** — added self-signed cert mode as fallback for cross-machine testing

## Blockers

- Tailscale cert generation requires paid plan (`tailscale cert` returns 500)
- Claude in Chrome extension connects to Windows browser, not Mac — cross-machine testing needs HTTPS
- Playwright MCP browser version mismatch (expected chromium-1200, installed 1217) — resolved with symlink

## Next Steps

- [ ] Add a main scene to the Godot project (currently empty — "no main scene defined")
- [ ] Define WebSocket message protocol between Godot client and Node.js server
- [ ] Set up Playwright test infrastructure for automated game verification
- [ ] Create first game feature RFC in vault
- [ ] Enable Tailscale Serve on tailnet admin for seamless cross-machine HTTPS
