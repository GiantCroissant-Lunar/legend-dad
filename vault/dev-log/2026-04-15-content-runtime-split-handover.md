---
date: 2026-04-15
agent: claude-code
branch: main (post-merge)
version: 0.1.0-content-runtime-split.1
tags: [handover, content-runtime-split, godot, pck, web]
---

# Handover — Content/Runtime Split (post-merge)

The two-Godot-project content/runtime split landed on `main` via merging `feature/content-runtime-split` (48 commits). End-to-end verified in the browser at session close — the game renders with HUD widgets loaded from `hud-core.pck` fetched at runtime over HTTP. This doc captures everything the next session needs to keep going.

## Before You Touch Anything

Run `task setup` from a fresh clone or after pulling main. It now does five things in order:
1. `pip install --user jsonschema`
2. Download Godot export templates
3. `pnpm install` under `project/server/`
4. `pre-commit install`
5. `task share:link` — recreates the cross-platform symlinks/junctions from `project/hosts/{complete-app,content-app}/{addons,lib,shaders,data,content}` into `project/shared/`
6. `task setup:godot` — opens each host project headlessly to seed `.godot/uid_cache.bin` (without this, `task test:godot` and `task build` fail with "Unrecognized UID" cascades)

The 9 link paths under `project/hosts/*/` are gitignored. Do NOT edit through them — a pre-commit hook (`shared-link-guard`) rejects writes inside the linked dirs. Edit files at their real location under `project/shared/` instead.

## What's New

### Folders
- `project/shared/` — single source of truth for addons, shared GDScript libs, shaders, data registries, source content. Outside both Godot host projects so neither owns it.
- `project/hosts/content-app/` — second Godot project for content authoring + preview harness. Builds PCKs.
- `project/hosts/complete-app/` is now thin: kernel scripts, ContentManager, boot scene, location PCK pipeline.

### Autoloads (in complete-app/project.godot)
- `ContentManager` — new. Reads `res://data/content_manifest.json`, loads/unloads PCK bundles. API is documented at `project/shared/lib/contracts/content_manager_api.gd`. Source at `project/hosts/complete-app/scripts/content_manager.gd`.
- All previous autoloads (`GameActions`, `LocationManager`, etc.) unchanged.

### Taskfile commands
- `task share:link` — (re)create cross-platform links
- `task setup:godot` — seed `.godot/` caches headlessly
- `task content:build -- {bundle-id}` — pack one bundle into `build/_artifacts/pck/{id}@{hash}.pck`, regenerate manifest
- `task content:build:all` — iterate every `bundle.json` under `shared/content/**`
- `task content:manifest` — regenerate `shared/data/content_manifest.json` from existing built PCKs

### Bundles shipped
- `hud-core` — eager. Activity log + minimap widgets.
- `hud-battle` — lazy, depends on `hud-core`. Battle overlay widget.

## Critical Patterns to Follow

### 1. Loading anything at runtime on web → mirror LocationManager.\_fetch\_pck\_web
This is the unblock that took most of a day to find:
- Fresh `HTTPRequest` per call (don't reuse a long-lived field)
- `add_child(http)`, `http.request(url)`, `await http.request_completed`, `http.queue_free()`
- Absolute URL via `JavaScriptBridge.eval("window.location.origin")` + `window.location.pathname`'s base dir
- Write bytes to `user://...`, then `ProjectSettings.load_resource_pack(user://...)`

`ContentManager._load_pck_web` is the canonical example. `LocationManager._fetch_pck_web` is the original.

### 2. Authoring a new content bundle
1. `mkdir project/shared/content/{kind}/{bundle-id}/`
2. Write `bundle.json` with `id`, `kind`, `policy` (eager/lazy), `deps`, `include` patterns, `provides` map.
3. Author the actual content (`.tres`, `.tscn`, `.gd`).
4. **`HudWidgetDefinition.tres` filenames must equal the widget id used by `ContentManager.get_hud_widget(id)`** — the lookup builds the path from the requested ID, not the script name. The mini-map widget is `minimap.tres`, NOT `mini_map_panel.tres`.
5. For script-only Control widgets, create a thin wrapper `.tscn` that attaches the script — `HudWidgetDefinition.scene` requires a PackedScene.
6. Include glob patterns in `bundle.json` need both nested AND flat variants — `["**/*.gd", "*.gd"]`. GDScript's `String.match("**/*.gd")` does not match files at the bundle root.
7. `task content:build -- {bundle-id}` — produces the PCK and updates the manifest.

### 3. Boot flow
`scenes/boot.tscn` (the main scene) → `boot.gd._ready()`:
1. Show "Booting…" splash
2. Load `res://data/content_manifest.json` — fall through to "fallback mode" status if missing
3. For each manifest entry with `policy: "eager"`: `await ContentManager.load_bundle(id)`
4. `change_scene_to_file("res://scenes/main.tscn")` — gameplay scene takes over
5. main.gd then instantiates HUD widgets via `ContentManager.get_hud_widget(id)`

If you add new eager bundles, just declare them in `bundle.json` with `policy: "eager"` — boot will pick them up automatically.

### 4. Lazy bundle loading
Currently nothing actually loads `hud-battle` lazily — gameplay code needs to `await ContentManager.load_bundle("hud-battle")` when entering combat. The bundle is built and registered in the manifest; the consumer wiring is missing. See "Worth doing next" below.

## Worth Doing Next

In rough priority order:

### High value
- **Wire `hud-battle` lazy load into combat entry.** `BattleManager.start_battle()` (or whatever triggers combat) should `await ContentManager.load_bundle("hud-battle")` before instantiating the battle overlay. Add a `bundle_unloaded` cleanup on combat exit. This is the proof that lazy-loading actually saves memory in the web build.
- **Fix the `whispering-woods` location PCK palette texture errors** visible in the browser console. Pre-existing issue with the LocationManager pipeline (palette PNGs reference paths that don't resolve after the location PCK loads). Not introduced by this migration but blocks visual polish.
- **HTTPRequest first-call latency on multi-threaded web**. The first `request_completed` signal takes ~12 seconds to fire on initial page load (subsequent calls are fast). Investigate Godot's HTTP client thread scheduling. May be fixable by warming a connection at boot, or it may be a Godot bug worth filing upstream.

### Medium value
- **Migrate `enemies-forest` bundle** with at least 1-2 enemy `.tres` definitions so the lookup pattern (`ContentManager.get_enemy_definition("goblin")`) gets exercised end-to-end.
- **Migrate location PCK pipeline to use ContentManager.** Currently `LocationManager` is its own thing with its own loader. Both could share `ContentManager`'s manifest + load flow. The plan deferred this; doing it would consolidate the patterns.
- **Per-asset CDN versioning.** PCK filenames are already hash-suffixed (`hud-core@a3f1b2.pck`); the manifest entry carries the hash. A cache-controlled HTTP layer or service worker could exploit this for proper offline caching.

### Lower value
- **Hot-reload watcher.** `ContentManager` exposes `bundle_will_reload` signal but nothing fires it. A filesystem watcher in dev mode (or HTTP polling on web) could detect new builds of a loaded bundle and re-`load_resource_pack` it. Useful for rapid iteration.
- **CI check** comparing autoload lists across `complete-app/project.godot` and `content-app/project.godot` to catch kernel-set drift.
- **Setup script pre-validation**. `setup_shared_links.py` should validate every entry's prerequisites in a pre-pass before creating any links so partial state can never result if something goes wrong mid-way.

## Known Pitfalls

- **Don't reuse HTTPRequest across calls on multi-threaded web.** Spent significant time chasing this. `request_completed` won't fire reliably. Always create a fresh one + `queue_free` after.
- **Don't add autoload mutation to addon `_enable_plugin` / `_disable_plugin`.** Headless mode never enables plugins, so the autoload registration never happens via that path. Declare statically in `project.godot [autoload]`. The vendored GUIDE addon has this fix; if you update GUIDE, re-apply (commit `f94129c`).
- **Don't edit through host-project link paths.** Pre-commit hook will reject. Edit `project/shared/...` directly.
- **`HudWidgetDefinition.tres` filename must match widget id** (mini-map is `minimap.tres`, not `mini_map_panel.tres`).
- **Browser cache after rebuild**. Hashed PCK filenames bust cache automatically, but the wasm/JS files don't have hashes. Hard reload (Cmd+Shift+R) or clear site data via `chrome://settings/cookies/detail?site=localhost` if you see stale behavior.

## Reference Files

| Topic | File |
|---|---|
| Original spec | `vault/specs/2026-04-15-content-runtime-split-design.md` |
| Implementation plan | `vault/plans/2026-04-15-content-runtime-split.md` |
| Progress + findings (F1–F10) | `vault/dev-log/2026-04-15-content-runtime-split-progress.md` |
| ContentManager source | `project/hosts/complete-app/scripts/content_manager.gd` |
| ContentManager API contract | `project/shared/lib/contracts/content_manager_api.gd` |
| Web PCK loader pattern (canonical) | `project/hosts/complete-app/scripts/location_manager.gd` (`_fetch_pck_web`) |
| Bundle packager | `project/hosts/content-app/scripts/bundle_packager.gd` |
| Manifest generator | `scripts/content_manifest.py` |
| Cross-platform link helper | `scripts/setup_shared_links.py` |
| Pre-commit guard | `scripts/precommit_shared_guard.py` |
| Updated AGENTS.md sections | Project Structure, Cross-Platform Sharing, Content Pipeline |
