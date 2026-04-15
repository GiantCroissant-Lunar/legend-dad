---
date: 2026-04-15
agent: claude-code
branch: main
version: 0.1.0-258
tags: [dev-log, hot-reload, f9, content-runtime-split, serve-web, bugfix]
---

# Session Dev-Log — F9 Widget-Vanish Root Cause

The visual-qa decision gate
(`vault/dev-log/2026-04-15-visual-qa-decision-gate.md`) caught a real bug:
after F9, both `hud-core` widgets vanish. This session root-caused and
fixed it.

## Root cause

The static server (`scripts/serve_web.js`, :7601) serves `/pck/*` from
`build/_artifacts/latest/web/pck/` — a symlink to the frozen
`0.1.0-257` engine-export snapshot. Contains only the three PCKs present
at export time: `hud-core@6747a4`, `hud-battle@b9d664`, `whispering-woods`.

`task content:build -- hud-core` writes fresh PCKs to
`build/_artifacts/pck/` — a **different directory that nothing copies into
the served tree**. The manifest on :7600 correctly points at the new hash,
but the game-side `_load_pck_web` hits the static server and gets a 404.

The 404 cascades:

1. `_load_pck_web(..., replace_files=true)` → `load_resource_pack` false
2. `load_bundle` → `bundle_load_failed` (not `bundle_loaded`)
3. `reload_bundle` returns false
4. `_on_bundle_reloaded` **never fires**
5. But `_on_bundle_will_reload` **already fired** at step 0 and tore down
   both widgets. They stay gone.

Proved by curl:

```
$ curl -sI http://localhost:7601/pck/hud-core@6747a4.pck       # snapshot
HTTP/1.1 200 OK
$ curl -sI http://localhost:7601/pck/hud-core@0e8db3.pck       # content:build output
HTTP/1.1 404 Not Found
```

## Why `hot-reload.spec.js` was green under this bug

The existing assertion only counted that distinct PCK URLs crossed the
wire — a 404 on the rebuild hash still shows up as a distinct URL, so
`uniqueHashes.length >= 2` passes. The test never validated (a) the
response status, (b) that `_on_bundle_reloaded` actually ran, or (c) that
widgets re-appeared. The visual-qa experiment was the first thing to
actually look at the rendered result.

## Fix

`scripts/serve_web.js` gets a `/pck/*.pck` fallback: if the default root
doesn't have the file, retry under `build/_artifacts/pck/` (anchored via
`import.meta.url` so it works regardless of invocation cwd — Playwright's
webServer spawns this from `project/server/packages/e2e`). Versioned
snapshot stays immutable; `content:build` output is served live.

`tests/hot-reload.spec.js` now asserts:

- every `/pck/hud-core@*.pck` response returned 200
- no `ContentManager: HTTP fetch failed` in console

Under the old (buggy) code, the strengthened test fails with:

```
Error: PCK http://localhost:7601/pck/hud-core@c29174.pck must return 200
Expected: 200
Received: 404
```

Under the fix, both pre- and post-F9 PCK responses are 200, and the
diagnostic screenshots show both widgets present after F9 (with "Hot
reload: hud-core (442ms)" line in the activity log confirming
`_on_bundle_reloaded` ran).

## Residual issue (follow-up)

The BG_COLOR tweak (red channel `0.05 → 0.45`) is still **not visually
apparent** after F9 — the activity log panel renders with the original
dark-blue background even though the re-instantiation completes. Likely
`const`-caching in GDScript: `CACHE_MODE_REPLACE_DEEP` on the
`HudWidgetDefinition.tres` doesn't force re-compile of the `.gd` script it
transitively references, so the `const BG_COLOR` at the top of the script
stays at its first-load value.

Related code smell in `_load_resource_by_kind` at
`project/hosts/complete-app/scripts/content_manager.gd:277`: the
`_just_reloaded` flag is erased after the FIRST lookup inside a bundle,
so the second widget of a multi-widget bundle (minimap, in this case)
loads through the default cache and never benefits from
`CACHE_MODE_REPLACE_DEEP`. That hides the color tweak on minimap too.

Filed for a separate session. The core hot-reload chain is now healthy —
widgets come back, and the test would catch a silent 404 regression.

## Files changed

```
scripts/serve_web.js                                       +27 -3
project/server/packages/e2e/tests/hot-reload.spec.js       +28 -2
vault/dev-log/2026-04-15-f9-pck-404-root-cause.md          (new)
```
