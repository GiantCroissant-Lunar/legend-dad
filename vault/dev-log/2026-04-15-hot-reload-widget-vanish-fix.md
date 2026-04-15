---
date: 2026-04-15
agent: claude-code
branch: main
version: 0.1.0-276
tags: [dev-log, hot-reload, f9, content-manager, bugfix, follow-up]
---

# Session Dev-Log — Hot-Reload Widget-Vanish Residual Fix

Follow-up to `2026-04-15-f9-pck-404-root-cause.md` — that session fixed the
server-side 404 that was silently failing `_on_bundle_reloaded`. The
**residual bug** filed in its "Residual issue (follow-up)" section is what
this session closes.

## The residual bug

From the prior dev-log:

> Related code smell in `_load_resource_by_kind` at
> `project/hosts/complete-app/scripts/content_manager.gd:277`: the
> `_just_reloaded` flag is erased after the FIRST lookup inside a bundle,
> so the second widget of a multi-widget bundle (minimap, in this case)
> loads through the default cache and never benefits from
> `CACHE_MODE_REPLACE_DEEP`.

hud-core contains two widgets — `activity_log_panel.tres` and
`minimap.tres`. `_install_hud_core_widgets()` calls `_instantiate_widget`
twice, which lands in `_load_resource_by_kind` twice. The original code
erased the flag after the first call:

```gdscript
if _just_reloaded.has(bundle_id):
    _just_reloaded.erase(bundle_id)  # ← bug: kills the flag for siblings
    return ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_REPLACE_DEEP)
return load(path)
```

Effect: one widget re-instantiates from the fresh PCK; the other returns
the cached `HudWidgetDefinition` pointing at a PackedScene from the old
PCK. The old scene no longer has a valid backing in the virtual filesystem
(replace_files=true wiped it), so `.instantiate()` either fails silently
or produces a node that never renders. The user sees one widget missing.

Prior visual-qa diagnosis saw **both** widgets missing because instantiation
for both often failed under the race — but the structural cause is the flag
erase.

## Fix

Drop the `erase`. The flag is naturally re-set on the next `reload_bundle`
call for the same bundle, so no state piles up. All widget lookups after a
reload use `CACHE_MODE_REPLACE_DEEP` — correct, with a tiny per-call I/O
cost which is fine outside hot paths.

```gdscript
if _just_reloaded.has(bundle_id):
    return ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_REPLACE_DEEP)
return load(path)
```

Also added a sanity print in `main.gd._on_bundle_reloaded`:

```gdscript
var ok := _activity_log_panel != null and _mini_map_panel != null
print("[main] hud-core widgets after reload: %s" % ("ok" if ok else "MISSING"))
```

...and a matching assertion in `tests/hot-reload.spec.js` so this regression
can't sneak back in silently. Prior visual-qa caught it with native vision;
this asserts it at the console level for fast CI feedback.

## Known residual: script constants don't hot-reload on web

Separate from the widget-vanish bug. If a `.gd` script contains a
`const BG_COLOR = Color(...)` at class level, changing that value and
pressing F9 **will not change the visible color** on the web export.

Root cause: Godot's web export ships compiled `.gdc` bytecode, not `.gd`
source. `GDScript.reload()` re-parses source code — with no source in the
PCK, there's nothing to re-parse. `CACHE_MODE_REPLACE_DEEP` on the `.tres`
re-loads the resource chain, but `PackedScene` instantiation uses the
already-registered GDScript class, and that class's constant table is
baked at first-compile.

I tried an explicit `_reload_bundle_scripts` pass that called
`GDScript.reload(true)` on every `.gd`/`.gdc` in the bundle. No effect —
reload is a no-op when source is absent.

### What works and what doesn't for iteration

| Change kind | Hot-reload works? |
|---|---|
| `.tres` data values (colors, numbers, strings in a Resource) | ✅ |
| `.tscn` scene structure (nodes, properties, layout) | ✅ |
| `const NAME = ...` in a `.gd` on web export | ❌ |
| `var NAME = ...` set in `_ready()` | ❌ (same cause — class stays frozen) |
| `.gd` function-body changes | ❌ (same) |

**Recommendation for content iteration:** put tunable values in `.tres`
data files, read them in `_ready()`. This also matches the project rule
in `AGENTS.md`:

> No hardcoded adjustable values — tile sizes, grid dimensions, speeds,
> cooldowns, zoom levels, and any gameplay-tunable constant must be read
> from data.

If you need actual script-level iteration during development, restart the
browser — or if running native (editor/desktop), hot reload works
differently because Godot can re-parse `.gd` source.

## Files changed

```
project/hosts/complete-app/scripts/content_manager.gd  _just_reloaded erase removed
project/hosts/complete-app/scripts/main.gd             [main] widgets-after-reload log
project/server/packages/e2e/tests/hot-reload.spec.js   widgets-present assertion
```
