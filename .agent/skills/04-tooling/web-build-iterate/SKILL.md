---
name: web-build-iterate
description: Iterate on the running web build — spot an issue on screen, edit a content source, rebuild just that bundle, hot-reload via F9, and re-verify. Use when verifying a web build and something looks off or you want to tweak without a full rebuild + page reload.
category: 04-tooling
layer: tooling
related_skills:
  - "@context-discovery"
  - "@validation-guard"
  - "@game-player"
---

# Web Build Iteration

Tight loop for adjusting a running web build without full rebuilds.

## When This Applies

You are running the web build (browser has the game open against `task dev` or `task serve`), you see something wrong — HUD widget color, minimap scale, activity log behavior, battle overlay layout — and you want to try a fix.

**This skill is NOT for:**
- The initial `task build` — use AGENTS.md + Taskfile directly.
- Server-side (`project/server/**`) changes — nodemon reloads on save; just re-hit the action in the browser.
- Engine-level changes (`project.godot`, shared addons, `lib/`, autoloads) — those require full `task build` and a page reload.
- Location PCK content — see "Reload Scope Matrix" below; full page reload today.

## The Loop

```
  verify (screenshot / e2e / play)
      │
      │  spot issue
      ▼
  classify change (scope matrix)
      │
      ├── hot-reloadable? ──┐
      │                     │
      ▼                     │
  edit source               │
      │                     │
      ▼                     │
  task content:build -- {id}│
      │                     │
      ▼                     │
  verify hash flipped       │
      │                     │
      ▼                     │
  F9 in browser ◄───────────┘
      │
      ▼
  re-verify
```

## Step 1 — Map File to Bundle

Content bundles live under `project/shared/content/{kind}/{bundle-id}/` with a `bundle.json` at the root. The edited file's bundle is the nearest ancestor dir containing `bundle.json`.

Current bundles (check `project/shared/content/**/bundle.json` for the live list):

| Source path | Bundle ID | Kind | Reload via |
|---|---|---|---|
| `project/shared/content/hud/hud-core/**` | `hud-core` | hud | F9 |
| `project/shared/content/hud/hud-battle/**` | `hud-battle` | hud | F9 |
| `project/shared/content/locations/**` | location bundles | location | **page reload** (separate loader) |
| `project/shared/content/{enemies,items,npcs,dialogue}/**` | (not yet wired) | — | full build + reload |

If the file you edited has no `bundle.json` ancestor, it's either engine-core or not yet bundled — skip to full `task build`.

## Step 2 — Reload Scope Matrix

| Change type | Rebuild command | Reload mechanism |
|---|---|---|
| GDScript widget in `hud/hud-core/` or `hud/hud-battle/` | `task content:build -- {id}` | **F9** (`ContentManager.reload_all_loaded`) |
| `.tres` / `.tscn` in a hud bundle | `task content:build -- {id}` | **F9** |
| Location tileset / palette / manifest | `task content:build -- {id}` | **page reload** — LocationManager has its own loader, F9 ignores it |
| Engine script, `project.godot`, addon, autoload | `task build` | **page reload** |
| Game-server JS (`project/server/packages/game-server/**`) | nodemon handles it | **re-trigger action** in browser (often no reload needed) |
| Shared `lib/` or `shaders/` | `task build` | **page reload** |

F9 reloads **every** hud bundle whose hash changed — not selective. That's fine; rebuilds that didn't run leave hashes untouched.

## Step 3 — Rebuild the Bundle

```bash
task content:build -- {bundle-id}
```

This writes a fresh `build/_artifacts/pck/{id}@{newHash}.pck` and regenerates `project/shared/data/content_manifest.json`. Does NOT touch the web export.

## Step 4 — Verify the Hash Flipped

Before pressing F9, confirm the game-server is actually serving the new manifest. The old PCK bytes are baked into `complete-app.pck`; only the runtime manifest endpoint knows about the rebuild.

```bash
curl -s http://localhost:7600/manifest.json | jq -r '.bundles["hud-core"].content_hash'
```

Run before and after the rebuild. If the hash didn't change:
- The bundle's sources didn't actually change (check the diff).
- The manifest regeneration failed — re-run `task content:manifest`.
- The game-server is serving a stale file — ensure it was started *after* the latest `task content:manifest`; re-start `task dev` if unsure.

## Step 5 — Trigger Reload

**F9** (keycode 4194342, action `reload_content` in `project.godot`) in the game window.

Expect an activity-log entry: `Hot reload: hud-core (XXXms)`. If no log line, F9 didn't fire — browser might not have focus on the canvas, or another widget ate the key. Click the canvas once and retry.

For non-HUD changes, reload the page (`Ctrl+R` / `Cmd+R` in the browser).

## Step 6 — Re-Verify

- Quick visual: take a fresh screenshot via Playwright or the dev-tool of choice.
- Regression: `task test:e2e` runs the full Playwright suite; `tests/hot-reload.spec.js` specifically exercises the F9 round-trip.
- Behavioral: exercise the feature (walk into battle, open a menu, etc.).

If the issue persists with the new hash confirmed loaded, the fix didn't land — edit again, rebuild, F9 again.

## Gotchas

- **HUD-only hot reload.** `LocationManager.PCK_SERVER_URL` is a separate loader; tilemap reload is a documented follow-up. For now, location edits are page-reload only.
- **Manifest URL hardcoded.** `ContentManager` fetches `http://localhost:7600/manifest.json`. If you changed the game-server host/port, F9 will fail silently — check the browser devtools network tab.
- **No true PCK unload.** Old bundle bytes stay in memory. `replace_files=true` + `CACHE_MODE_REPLACE_DEEP` ensure correctness, but after ~dozens of reloads in one session, memory creeps. Restart the tab if things get weird.
- **Background tab throttling.** Chrome throttles hidden tabs; Godot's main loop stalls, F9 may not register. Keep the tab visible or run Playwright `--headed`.
- **MCP vs keyboard.** Driving F9 through an MCP browser client is flakier than a direct Playwright keyboard press — prefer `playwright_press_key` for automated runs.
- **Three-pass confirmation.** After 3 failed iterate cycles (edit → rebuild → reload → still broken), stop. The root cause is likely upstream (wrong bundle, wrong file, or engine-scope change masquerading as content). Fall back to full `task build` or surface the ambiguity to the user.

## Quick Reference

```bash
# Ensure dev is running (WS on :7600, static serve for /web)
task dev

# Identify bundle id from an edited file
# (grep up the dir tree for bundle.json)
dirname project/shared/content/hud/hud-core/activity_log_panel.gd
# → project/shared/content/hud/hud-core  →  bundle id from bundle.json

# Rebuild one bundle
task content:build -- hud-core

# Check manifest hash served by game-server
curl -s http://localhost:7600/manifest.json | jq '.bundles'

# Full e2e regression (includes hot-reload spec)
task test:e2e
```
