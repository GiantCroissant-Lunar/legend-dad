---
date: 2026-04-15
agent: claude-code
branch: main
version: 0.1.0-257
tags: [dev-log, content-runtime-split, hot-reload, godot, pck, web]
---

# Session Dev-Log — Manual Hot Reload

Built on top of the content-runtime-split followups (`vault/dev-log/2026-04-15-content-runtime-followups.md`). Adds in-game F9 trigger that re-fetches the content manifest, detects changed bundle hashes, and swaps in new PCKs without a page reload.

Explicitly scoped to **manual** hot reload — no file watcher, no auto detection. Matches user requirement: "we just need it can be hot reload, we can trigger it in game to load/unload, so auto detection is not necessary at all."

## End-to-end flow

1. Edit a content source under `project/shared/content/{kind}/{bundle-id}/`.
2. Run `task content:build -- {bundle-id}` from the host shell. New `{bundle-id}@{newHash}.pck` written to `build/_artifacts/pck/`; manifest at `project/shared/data/content_manifest.json` updated.
3. In the running game (browser tab): press **F9**.
4. `ContentManager.reload_all_loaded()` fetches `http://localhost:7600/manifest.json` (new game-server endpoint), compares each loaded bundle's content_hash against the new manifest, calls `reload_bundle()` for any that changed.
5. Per changed bundle: emit `bundle_will_reload` (consumers free their refs), `_loaded.erase()`, `load_bundle(id, replace_files=true)` (re-fetches PCK with `ProjectSettings.load_resource_pack(replace=true)`), emit `bundle_loaded` (consumers re-instantiate from fresh resources).
6. Activity log shows `Hot reload: hud-core (XXXms)`.

Verified by an e2e test (`tests/hot-reload.spec.js`):
```
[test] initial hud-core hash: 6747a4
[test] rebuilding hud-core bundle
[test] hud-core hashes seen: ["6747a4","c29174"]
1 passed (16.6s)
```

## Pieces

### Game server (`/manifest.json` endpoint)

`project/server/packages/game-server/src/index.js`. Single new route serving `project/shared/data/content_manifest.json` from disk with `Cache-Control: no-store`. The manifest baked into `complete-app.pck` is frozen at engine-export time and references stale hashes — fetching at runtime is the only way to discover post-rebuild content.

### `ContentManager` reload API

`project/hosts/complete-app/scripts/content_manager.gd`. New surface:

- `reload_manifest() -> bool` — web fetches `MANIFEST_HTTP_URL`; native re-reads `res://data/content_manifest.json`. Replaces `_manifest` in place.
- `reload_bundle(id) -> bool` — emits `bundle_will_reload`, removes from `_loaded`, sets `_just_reloaded[id]`, calls `load_bundle(id, replace_files=true)`. Existing `bundle_loaded` signal fires on success.
- `reload_all_loaded() -> Array[String]` — snapshots loaded set + hashes, calls `reload_manifest()`, then `reload_bundle()` per bundle whose hash changed. Returns the list reloaded so the caller can show feedback.

Plus parameter additions:
- `load_bundle(id, replace_files=false)` — passes through to `ProjectSettings.load_resource_pack(path, replace_files)` and to `_load_pck_web`.
- `_load_pck_web(name, replace_files=false)` — same.

And the **resource cache bypass**: `_load_resource_by_kind` now checks `_just_reloaded[bundle_id]`. If set, uses `ResourceLoader.load(path, "", CACHE_MODE_REPLACE_DEEP)` and clears the flag. Without this, Godot's resource cache returns the old `HudWidgetDefinition` and the consumer never sees the new PackedScene.

### Main scene hooks

`project/hosts/complete-app/scripts/main.gd`. Three pieces:

- `_install_hud_core_widgets()` — extracted helper. Frees existing widgets if present, then re-instantiates `activity_log_panel` + `minimap` and re-applies layout. Idempotent. Used by initial setup AND `_on_bundle_reloaded`.
- `_on_bundle_will_reload(id)` — frees this bundle's widgets so the old PCK's resources can release.
- `_on_bundle_reloaded(id)` — re-instantiates. Only fires for hot reload (the initial `bundle_loaded` from boot.gd happens before `main.gd._ready` connects the signal). Mid-combat hud-battle reload is supported (preserves BattleManager state, swaps overlay; party/enemies re-bound).
- `_unhandled_input` adds an F9 → `_hot_reload_content()` branch. Logs `Hot reload: ...` to ActivityLog.

### Input binding

`project/hosts/complete-app/project.godot`. New `reload_content` action mapped to F9 (keycode 4194342). F9 chosen over F5 (browser reload), Ctrl+R (browser reload), F12 (devtools), F11 (fullscreen).

## E2E test (`tests/hot-reload.spec.js`)

Boots the game, snapshots `activity_log_panel.gd`, modifies a `Color()` constant, runs `task content:build -- hud-core` via `child_process.execSync`, presses F9 via Playwright keyboard, asserts the network log contains TWO distinct `hud-core@{hash}.pck` URLs. Restores the source in `finally` and rebuilds back to the original hash so subsequent runs start from a known state.

Same constraints as the lazy-bundle test:
- Must run `--headed` (hidden tab throttling stalls Godot's main loop)
- Drives via Playwright keyboard, not MCP (avoids stale-WS-client races when other browser tabs are open)

## Known limitations

- **HUD-only.** `LocationManager` has its own loader (separate from `ContentManager`) and its own `_fetch_pck_web`. Tilemap hot reload would require an analogous teardown/re-instantiate dance — not done in this session. F9 currently only reloads bundles registered in the content manifest (hud-core, hud-battle).
- **No partial reload.** F9 always reloads everything in the loaded set whose hash changed. There's no "reload just hud-core" command yet — easy to add if needed.
- **Manifest URL is hardcoded to localhost:7600.** Same issue as `LocationManager.PCK_SERVER_URL`. If you want to deploy somewhere other than localhost:7600 for the game-server, both URLs need to read from a runtime-configurable source (URL query param, ProjectSettings, or a server-side config file).
- **WS protocol unaware of the swap.** If the game-server cares about the bundle version, it would need a notification message on reload. Not relevant for the current Mastra agent setup.
- **Godot 4 doesn't expose a real PCK unload.** The old PCK's bytes stay in memory. `replace_files=true` overlays new files; `_just_reloaded` + `CACHE_MODE_REPLACE_DEEP` ensure the resource cache hands out fresh instances. Memory of the prior PCK is reclaimed only when the runtime stops referencing it.

## Worth doing next

- **Per-bundle reload command via MCP tool** so an agent (or a script) can trigger reloads remotely without keyboard simulation.
- **`LocationManager` consolidation onto `ContentManager`** — once that's done, location PCKs get hot reload for free.
- **Configurable `MANIFEST_HTTP_URL`** — read from `OS.get_cmdline_args()` / `JavaScriptBridge` query param so non-localhost deployments work.
- **Reload toast in HUD** — currently logs to ActivityLog only. A short-lived overlay would be more visible.

## Files changed

```
project/server/packages/game-server/src/index.js                +29 (manifest endpoint)
project/hosts/complete-app/scripts/content_manager.gd           +99 (reload API)
project/hosts/complete-app/scripts/main.gd                      +85 (F9 + signal hooks)
project/hosts/complete-app/project.godot                        +5  (reload_content action)
project/server/packages/e2e/tests/hot-reload.spec.js            new (regression test)
```
