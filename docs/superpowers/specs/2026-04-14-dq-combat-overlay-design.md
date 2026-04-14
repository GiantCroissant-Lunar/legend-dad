# Dragon Quest Combat Overlay + HUD Panels

## Summary

Add a DQ first-person style battle overlay window, always-visible activity log (bottom-left), and mini-map placeholder (top-right) using a CanvasLayer-based floating window architecture.

## Layout

- **Top-left:** Active era view (50% viewport) — existing SubViewport
- **Top-right:** Mini-map panel (~15% viewport) — new, windowed style
- **Bottom-left:** Activity log panel (~35%w x ~35%h) — new, windowed style
- **Bottom-right:** Inactive era view (40% viewport) — existing SubViewport
- **Battle overlay:** Same size as active view (50%), same position (top-left 20,20), on CanvasLayer z=50

## Battle Overlay (DQ First-Person)

Three zones top-to-bottom:
1. **Monster viewport (~55%):** Gradient sky-to-ground background, dark silhouette shapes for enemies, name labels, target arrow
2. **Command menu (~20%):** Active combatant name + Attack/Defend/Flee, cursor highlight
3. **Party status (~25%):** HP bars, names, DEF indicators

Colors: navy bg, white/blue border, gold highlights, white text.

## Activity Log

- Always visible, windowed panel matching era view aesthetic
- Records exploration events (era switch, interactions, zone enter) and all battle events
- Battle sections wrapped with separator lines
- Max 50 lines, oldest pruned
- Singleton autoload `ActivityLog` — any system calls `ActivityLog.log(msg)`

## Mini-map

- Small dot-grid showing collision grid for active era
- Player = bright dot, enemies = red dots, blocked = filled squares
- Updates on era switch

## Architecture

- **CanvasLayer z=50** hosts: activity log panel, mini-map panel, battle overlay (when active)
- `ActivityLog` autoload singleton (data store + signal)
- `ActivityLogPanel` Control node (visual renderer)
- `MiniMapPanel` Control node (reads collision grid + entity positions)
- `BattleOverlay` Control node (replaces old BattleUI, DQ-style _draw())
- `BattleManager` pushes messages to ActivityLog instead of internal message_lines
- `main.gd` creates CanvasLayer + panels in _ready(), manages battle overlay lifecycle

## Scope

**In:** Battle overlay, activity log, mini-map placeholder, exploration event wiring
**Out:** Random encounters, spells/items, real monster art, rich mini-map features
