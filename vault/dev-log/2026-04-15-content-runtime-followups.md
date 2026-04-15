---
date: 2026-04-15
agent: claude-code
branch: main
version: 0.1.0-250
tags: [dev-log, content-runtime-split, godot, pck, web, lazy-load, e2e]
---

# Session Dev-Log — Content/Runtime Split Followups

Picked up the three "worth doing next" items from the post-merge handover (`vault/dev-log/2026-04-15-content-runtime-split-handover.md`). All three landed and are end-to-end verified by a new Playwright headed test.

## Summary

| Item | Status | Verification |
|---|---|---|
| #1 hud-battle lazy load on combat entry | ✅ Done | Playwright e2e + headless GUT |
| #2 whispering-woods palette texture errors | ✅ Done | Visual confirmation in browser + headless resource load test |
| #3 HTTPRequest first-call latency | ✅ Done | 53s → 158ms measured end-to-end |

## Item #1 — Lazy bundle load on combat entry

`BattleManager.start_battle()` already exists, but main.gd's `_start_battle` was instantiating the battle overlay widget without first ensuring the `hud-battle` PCK was loaded. Wired the lazy load in:

- `_start_battle` now `await ContentManager.load_bundle("hud-battle")` before `_instantiate_widget("battle_overlay")`. Fails closed: if load returns false, `in_battle` is reset and entity refs cleared so the player isn't stuck in a half-entered combat state.
- `_on_battle_ended` calls `ContentManager.unload_bundle("hud-battle")` to mirror the entry. (Godot 4 has no public PCK unload API; this just clears bookkeeping so future loads re-fetch.)

The Playwright test confirms `pck/hud-battle@b9d664.pck` is **NOT** requested at boot but **IS** requested after `interact` triggers combat, with the actual fetch taking ~232ms.

## Item #2 — Palette texture errors (visual regression)

**Root cause:** `pck_builder.gd` was copying raw `palette_father.png` + its `.import` companion into the location PCK. The `.import` file references a `res://.godot/imported/palette_father.png-{hash}.ctex` binary which lives **outside** the PCK — never gets packed — so `load("...palette_father.png")` failed at runtime, leaving the tilemap unrendered (gray screen with only the brown UI border visible).

**Fix:** Bake palettes as self-contained `ImageTexture` `.tres` resources at PCK build time. `ResourceSaver.save()` embeds the pixel data directly into the resource — no `.import`/`.ctex` dependency. The atlas was already done this way inside `tileset.tres`; palettes now follow the same pattern.

- `pck_builder.gd`: new `_bake_palette_texture(src, dst)` helper; replaces `_copy_file` calls for palettes.
- `location_manager.gd`: `_load_from_pck` now loads `palette_father.tres` / `palette_son.tres` instead of the raw PNGs.
- Also deleted obsolete `palette_*.png` + `.import` from the staging dir (`project/hosts/complete-app/locations/whispering-woods/`) so they don't sneak back into the PCK on subsequent builds.

Headless verification:
```
PCK loaded OK
palette_father.tres loaded: 16x1
palette_son.tres loaded: 16x1
tileset.tres loaded: 1 sources, tile_size=(32, 32)
atlas texture: 512x512
ALL PALETTE/TILESET LOADS OK
```

Visual confirmation in the headed Playwright test screenshot: the whispering-woods tilemap renders correctly, "Entered Whispering Woods" appears in the activity log, mini-map populates.

## Item #3 — HTTPRequest first-call latency on multi-threaded web

**Root cause:** With `variant/thread_support=true` in `export_presets.cfg`, Godot's `HTTPRequest` defaults to using a per-request worker thread (pthread). On Emscripten, spawning the first pthread worker has a one-time setup cost of ~10s+ (worker pool warm-up). Each fresh `HTTPRequest.new()` was eating that cost — not just the first one — because each call hit a cold worker.

Initially I suspected the handover's "~12s" estimate was conservative and only the first call paid it. Diagnostics showed otherwise: a 7KB PCK that curls in 1ms was taking 53.4s to deliver `request_completed` in the browser. **Worse**, when the tab is hidden, Chrome throttles RAF and the engine pump barely runs, multiplying the wait.

**Fix:** Set `http.use_threads = false` on the per-request `HTTPRequest`. This switches to polling mode on the main thread — no worker spawn at all. Combined with running the test headed (so the tab isn't visibility-throttled), fetch latency drops to ~158ms end-to-end.

Both `ContentManager._load_pck_web` and `LocationManager._fetch_pck_web` got the same fix, plus a small `Time.get_ticks_msec()` timing print so future regressions are obvious in the console.

## E2E regression test

`project/server/packages/e2e/tests/lazy-bundle-load.spec.js` ties everything together. Asserts:

1. `hud-core` PCK fetched at boot (eager bundle).
2. `hud-battle` PCK **not** fetched at boot (lazy bundle).
3. After driving the player into combat via keyboard input, `hud-battle` PCK **is** fetched.
4. Zero `palette` / `CompressedTexture` / `ERROR` console messages during boot or location load.

Notable test gotchas worth keeping in mind for future Playwright work on this project:

- **Must run headed.** Hidden Chromium tabs throttle `requestAnimationFrame` to ~1Hz, which pauses Godot's main loop and inflates HTTPRequest wait times to minutes. The test is fast (~22s) headed, useless headless.
- **Direct keyboard input, not MCP.** When the user has another browser tab open with the game, *its* WS connection competes for the `connMgr.godotClient` slot on the game server (last-write-wins). MCP commands then land on the wrong Godot instance. `page.keyboard.down/up` with a held duration (~120ms) stays inside Playwright's browser context and bypasses the issue. A bare `page.keyboard.press` is too fast — `Input.is_action_pressed` polled per frame can miss it.

## Files changed

```
project/hosts/complete-app/scripts/content_manager.gd       use_threads=false + timing
project/hosts/complete-app/scripts/location_manager.gd      use_threads=false + .tres palettes
project/hosts/complete-app/scripts/main.gd                  hud-battle lazy load wiring
project/hosts/content-app/scripts/pck_builder.gd            bake palettes as embedded .tres
project/server/packages/e2e/tests/lazy-bundle-load.spec.js  new regression test
```

User WIP under `project/server/packages/game-server/` and other untracked dirs (`.archon/`, `build/tilesets/`, etc.) was intentionally left untouched.

## Worth Doing Next

The three high-priority items from the prior handover are done. From the medium/lower buckets:

- **Migrate `enemies-forest` bundle** (1-2 enemy `.tres`) to exercise the lookup pattern with non-HUD content.
- **Consolidate `LocationManager` onto `ContentManager`** — both have their own loaders + their own `_fetch_pck_web` copy. Now that `ContentManager` proves the pattern, dedup is straightforward.
- **Per-asset CDN cache headers** — PCK filenames are hash-suffixed; the static server could send long `max-age` for them.
- **Tab-visibility-throttling note in CI docs** — anyone running e2e in CI should be aware headless-with-throttling kills the test (CI normally runs headless but in a non-throttled "background" mode; should still verify on the chosen runner).

## Known Pitfalls (carried forward, plus new)

- Don't reuse `HTTPRequest` across calls on multi-threaded web. (From prior log — still true.)
- `HudWidgetDefinition.tres` filename must match the widget id used by `ContentManager.get_hud_widget(id)`. (From prior log.)
- **NEW: Always set `http.use_threads = false`** on per-request `HTTPRequest` instances when running on `variant/thread_support=true` web export. Default `true` triggers pthread spawn cost.
- **NEW: Palette PNGs in PCKs need to be baked as `ImageTexture` `.tres`**, not copied as raw `.png` + `.import`. Same pattern as the atlas embedding inside `tileset.tres`.
- **NEW: e2e Playwright tests against this game must run `--headed`.** Hidden-tab throttling makes the HTTPRequest pump slow to a crawl.
- **NEW: WS client-replacement free-for-all.** `connMgr.godotClient` is single-slot, replaced on every new WS handshake. If multiple browser tabs/windows have the game loaded (including service-worker zombies that survive tab closure), MCP commands land on whichever Godot most recently registered. For deterministic testing, use Playwright keyboard input rather than MCP, or close all other game tabs first.
