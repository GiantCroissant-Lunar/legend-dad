---
date: 2026-04-15
agent: claude-code
branch: main
version: 0.1.0-278
tags: [dev-log, hot-reload, f9, hud, content-manager, refactor, follow-up]
---

# Session Dev-Log — HUD Live Visual Iteration via Style .tres

Closes the second residual filed by the earlier hot-reload-widget-vanish
work: **script `const` values can't hot-reload on the web build**
(compiled `.gdc` carries no source for `GDScript.reload` to re-parse).

A parallel session already landed Bug A's fix (`_just_reloaded` flag
persistence, commit `b74a08e`) and documented the const-caching limitation
(`cdcd409`). This session delivers the pragmatic fix the user asked for —
"F9 actually gives you a live visual iteration loop."

## Approach

Move every hot-tunable value out of `const` on the widget scripts and into
a `.tres` style resource referenced by the widget's `.tscn`. Data files
hot-reload cleanly via the existing `CACHE_MODE_REPLACE_DEEP` chain; script
bytecode doesn't need to change at all.

### Resource graph (new)

```
hud_widget_definition.tres  (HudWidgetDefinition — id, scene, anchor)
  └─ scene → activity_log_panel.tscn
       ├─ script → activity_log_panel.gd   (reads `style.*`)
       └─ style  → activity_log_panel_style.tres  (ActivityLogPanelStyle)
                     bg_color, border_color, header_color, text_color,
                     msg_font_size, header_font_size, line_height,
                     padding, border_width
```

Same shape for `mini_map_panel` + `mini_map_panel_style.tres`
(`MiniMapPanelStyle`).

Resource class `.gd` files live under `project/shared/lib/resources/`
(follows the existing `HudWidgetDefinition` pattern — baked into
`complete-app.pck` so the `ActivityLogPanelStyle` / `MiniMapPanelStyle`
class names are registered at startup).

Style `.tres` instances live inside the `hud-core` bundle so they ship
with the PCK and participate in the hot-reload path.

## Verification

`tests/style-hot-reload.spec.js` drives the full iteration loop and
asserts the widget's self-reported style value flips after F9:

```
[style-alp] bg_color=(0.05, 0.05, 0.15, 0.85)      ← boot
[style-alp] bg_color=(0.45, 0.05, 0.15, 0.85)      ← post-F9 (.tres tweaked)
```

Screenshot verification (`build/_artifacts/latest/screenshots/style-hot-reload-after.png`)
shows the activity log panel's background visibly changing from dark-blue
to dark-red under the hot-reload. Compare:

- Prior visual-qa-experiment `after-15s.png` (pre-refactor, const-based):
  panel color did NOT change despite BG_COLOR tweak landing in the new PCK
- This session's `style-hot-reload-after.png` (post-refactor, .tres-based):
  panel color DOES change

`tests/hot-reload.spec.js` retargeted to tweak the same `.tres` file; it
retains the 200-response + widgets-ok assertions (regression guards for the
earlier server-404 and widget-vanish fixes).

## Works / doesn't-work matrix (updated)

| Iteration change | Hot-reload via F9 |
|---|---|
| Edit `<widget>_style.tres` value | ✅ live update |
| Edit `.tscn` scene structure | ✅ live update |
| Edit `.gd` `const NAME = ...` | ❌ bytecode frozen on web |
| Edit `.gd` function body | ❌ bytecode frozen on web |

**Policy for HUD widget authors:** any tunable that you might want to
iterate on goes in a `<widget>_style.tres`. Script code stays structural.
This also lines up with the project rule in `AGENTS.md` ("no hardcoded
adjustable values — read from data").

## Scope notes

Only activity log + minimap were refactored (both in `hud-core`). The
`battle_overlay` in `hud-battle` still uses script consts if any — worth a
follow-up pass when battle visuals start needing iteration.

## Files changed

```
project/shared/lib/resources/
  activity_log_panel_style.gd  (new — Resource class, 9 exported fields)
  mini_map_panel_style.gd      (new — Resource class, 9 exported fields)

project/shared/content/hud/hud-core/
  activity_log_panel.gd         const → @export var style: ActivityLogPanelStyle
  activity_log_panel.tscn       adds style = ExtResource(...)
  activity_log_panel_style.tres (new — baseline values)
  mini_map_panel.gd             const → @export var style: MiniMapPanelStyle
  mini_map_panel.tscn           adds style = ExtResource(...)
  mini_map_panel_style.tres     (new — baseline values)

project/server/packages/e2e/tests/
  style-hot-reload.spec.js      (new — TDD for the iteration loop)
  hot-reload.spec.js            retargeted to tweak style.tres

project/shared/data/content_manifest.json   rebuild hash bump (09edde)
```
