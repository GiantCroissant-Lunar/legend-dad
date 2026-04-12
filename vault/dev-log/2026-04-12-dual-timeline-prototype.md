---
date: 2026-04-12
agent: claude-code
branch: feature/dual-timeline-prototype
version: 0.1.0-dual-timeline-prototype.1
tags: [prototype, gameplay, battle, dual-timeline]
---

# Session Dev-Log — Dual-Timeline Prototype

## Summary

Brainstormed, designed, and built the first playable prototype of the
dual-timeline RPG concept. Two gameplay views (father era and son era)
float as windows over a world map. Added Dragon Quest-style turn-based
combat system. 18 commits on `feature/dual-timeline-prototype`.

## What Was Built

### Gameplay Design (brainstorming)

- Established core concept: top-down JRPG with two simultaneous views
  (father in the present, son 20 years later)
- Confirmed genre: classic JRPG with timeline twist (Dragon Quest style)
- Designed screen layout: floating windows (~50% active, ~40% inactive)
  over a functional world map with toggle (M key)
- Designed four same-spot overlap mechanics: temporal resonance, echo
  battle, timeline convergence, temporal dungeon
- Designed combat system: DQ first-person turn-based, same engine for
  both eras, father solo with advisor, son with party of 3-4
- Cross-timeline combat approach 1 confirmed (inherited scars)
- Interactive browser mockups created for layout and mechanics discussion

### Overworld Prototype (19 GDScript files)

ECS architecture using GECS addon:

**Components (6):**
- `C_TimelineEra` — FATHER/SON enum
- `C_GridPosition` — col, row, facing, visual_x/visual_y for smooth lerp
- `C_PlayerControlled` — active flag for input routing
- `C_Interactable` — type (BOULDER/SWITCH), state (DEFAULT/ACTIVATED)
- `C_TimelineLinked` — links paired objects across eras
- `C_Enemy` — enemy_type string indexing into BattleData

**Entities (3):**
- `E_Player` — player with era, grid position, control
- `E_Interactable` — boulder/switch with cross-era linking
- `E_Enemy` — overworld enemy with era, position, type

**Systems (3):**
- `S_PlayerInput` — directional movement with cooldown, walkability check,
  occupation check
- `S_GridMovement` — lerps visual_x/visual_y toward grid target
- `S_Interaction` — face interactable + press E, activates + propagates
  to linked entity in other era

**Visual layer:**
- `EntityVisual` (Node2D) — draws entities via `_draw()`, synced from
  component data by main.gd each frame
- Separate from ECS entities (Entity extends Node, not Node2D)
- Types: PLAYER_FATHER, PLAYER_SON, BOULDER, BLOCKED, ENEMY

**Scene assembly:**
- `main.gd` — builds everything programmatically: two SubViewportContainers
  with TileMapLayers, world map CanvasLayer, ECS world, entities, visuals
- `TilesetFactory` — creates colored-tile tilesets from code (no art needed)
- Tab = switch era, M = toggle map, E = interact, arrows = move

### Battle System

**Data layer:**
- `BattleData` — static stat tables (father, son, ally1, ally2), enemy
  definitions (slime, bandit, wolf), damage formula, flee chance
- `Combatant` — runtime state class with from_dict() factory

**State machine:**
- `BattleManager` — 7 states: INTRO → COMMAND → TARGET_SELECT → RESOLVE
  → VICTORY/DEFEAT/FLEE
- Speed-sorted turn resolution, retargeting on dead combatants
- Father fights solo (1 command/turn), son fights with party of 3

**Rendering:**
- `BattleUI` — draws entire battle screen via `_draw()`: enemies as
  colored ellipses, message log, command menu with cursor, party status
  with HP bars

**Integration:**
- Overworld enemies spawn as diamond-shaped visuals on the tilemap
- Walking next to an enemy and pressing E triggers battle
- ECS pauses during combat, BattleManager takes over
- On victory: enemy removed from map, EXP/gold awarded
- On defeat: scene reloads

### Design Documents

- `vault/design/dual-timeline-gameplay-brainstorm.md` — full gameplay
  brainstorm with confirmed directions and open questions
- `vault/design/combat-system-design.md` — DQ-style combat spec with
  prototype scope and future plans

### Implementation Plans

- `vault/plans/2026-04-12-dual-timeline-prototype.md` — 11-task plan
  for overworld prototype
- `vault/plans/2026-04-12-battle-system-prototype.md` — 9-task plan
  for battle system

## Known Issues

### P0 — Must Fix

1. **Battle screen rendering incorrect** — User reported the battle
   screen "looks incorrect" but specific issues not yet identified.
   Could be: BattleUI not filling the SubViewport correctly, z-index
   issues with the tilemap showing through, text positioning wrong,
   or the Control node anchoring not working inside SubViewport.
   Needs manual testing in a browser to diagnose.

2. **Keyboard input in web export** — Arrow keys, Enter, and Space
   may not work reliably in the browser. Tab and M keys work (handled
   via `_input()` with direct keycode checks). The ECS systems use
   `Input.is_action_pressed()` which may behave differently in web
   export. E key was added as alternative interact key.

### P1 — Should Fix

3. **Entity registration pattern** — Using `ECS.world.add_entity()`
   with default `add_to_tree=true` means entities live as children
   of the World node, not the SubViewport. This works for data but
   means the visual sync pattern (EntityVisual in SubViewport, entity
   in World) is the only viable approach. Confirmed working for the
   overworld; battle integration may have issues.

4. **BattleUI inside SubViewport** — The battle UI is added as a
   Control child of the SubViewport with `z_index = 100`. The
   `set_anchors_and_offsets_preset(PRESET_FULL_RECT)` call may not
   work correctly inside a SubViewport because the SubViewport's
   coordinate system differs from a regular viewport. May need to
   set size explicitly.

### P2 — Nice to Have

5. **No transition animation** for entering/exiting battle.
6. **Debug HUD overlaps** with game views on small screens.
7. **World map location labels** use hardcoded positions (1024x600).

## Architecture Decisions

1. **ECS entities as pure data** — Entity extends Node, not Node2D.
   All visual representation is handled by separate EntityVisual
   (Node2D) nodes in SubViewports. main.gd syncs positions each frame.

2. **Battle outside ECS** — BattleManager is a plain Node, not an
   ECS system. ECS pauses during combat. This keeps the battle state
   machine simple and avoids complexity of running two game loops.

3. **Programmatic scene construction** — Everything built in code
   via main.gd `_ready()`. No .tscn scene files beyond the minimal
   root. This makes iteration fast but harder to edit in the Godot
   editor.

4. **Placeholder art via `_draw()`** — All visuals are colored shapes
   drawn procedurally. No image assets needed for the prototype.

## Next Session Direction

- **Utilize WebSocket server** — The echo server at `:3000` is ready
  for a real protocol. Next session should define the WS message
  format and use it for gameplay features (e.g., remote play, event
  streaming, save/load via server).
- **Fix battle rendering** — diagnose and fix the battle UI issues.
- **Fix keyboard input** — investigate why arrow keys may not work
  reliably in web export and find a robust solution.

## Commit Log

```
e37e552 feat: integrate battle system with overworld
23b7c43 feat: add ENEMY visual type to EntityVisual
2cb4e91 feat: add BattleManager state machine
05eaf5d feat: add BattleUI with DQ-style battle screen
700b174 feat: add Combatant runtime state class
cb490e7 feat: add BattleData with stats and formulas
0e5372b feat: add C_Enemy component and E_Enemy entity
8a79d8c docs: add battle system prototype plan
4c7ee6e docs: add combat system design document
8beb836 fix: add debug HUD and E key for interact
a1787be fix: decouple visual rendering from ECS entities
596f0a4 feat: add visual sprites and input action
7c12f6a feat: assemble main scene with ECS wiring
4978db9 feat: add TilesetFactory for prototype tileset
77f90f7 feat: add player input, movement, interaction systems
19264e6 feat: add E_Player and E_Interactable entities
2a6df9d feat: add ECS components for dual-timeline prototype
fe8997b docs: add gameplay brainstorm and prototype plan
```

## File Inventory

```
ecs/components/     6 files (C_TimelineEra, C_GridPosition, C_PlayerControlled,
                            C_Interactable, C_TimelineLinked, C_Enemy)
ecs/entities/       3 files (E_Player, E_Interactable, E_Enemy)
ecs/systems/        3 files (S_PlayerInput, S_GridMovement, S_Interaction)
scripts/            3 files (main.gd, entity_visual.gd, tileset_factory.gd)
scripts/battle/     4 files (battle_data.gd, combatant.gd, battle_ui.gd,
                            battle_manager.gd)
vault/design/       2 files (gameplay brainstorm, combat system design)
vault/plans/        2 files (overworld plan, battle plan)
```

Total: 19 GDScript files, 4 design/plan docs, 18 commits.
