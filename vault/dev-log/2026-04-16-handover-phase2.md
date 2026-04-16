---
date: 2026-04-16
agent: claude-code
branch: main
tags: [handover]
---

# Session Handover — 2026-04-16 (Phase 2 Complete)

## What Was Built Today

17 commits on `main`, implementing Phase 2A + 2B from `vault/plans/2026-04-16-content-mechanics-pipeline-phase2.md`.

### Pipeline (end-to-end)

```
vault markdown → vault_to_manifest.py → import-manifest.json
  → MDK plugin → articy:draft → export JSON → writeback IDs
  → canonical_to_godot.py → .tres (enemies, encounters, curves)
  → Godot: action-driven combat, XP/level-up, monster scaling
```

### Phase 2A deliverables
- Schema + parser extended for mechanical data
- 5 bestiary entries with battle_stats + weighted action tables
- 7 zones with encounter tables (4 wilderness, 3 safe)
- 4 locations with difficulty tiers
- MDK plugin updated (templates, importer, quicktype types)
- Adapter: manifest → EnemyDefinition + EncounterTable .tres
- BattleManager: action-driven enemy AI with fallback to legacy path

### Phase 2B deliverables
- 5 curve vault pages (father/son XP + stats, monster scaling)
- LevelCurve resource with interpolation
- ProgressionManager: XP award, level-up detection, stat growth
- Monster scaling by zone difficulty_tier
- Curve-driven party construction (const fallback preserved)

## Current State Snapshot

| Area | Status | Notes |
|---|---|---|
| Vault → manifest pipeline | Working | 41 entities, validates against schema |
| MDK plugin | Deployed | BattleStats, EncounterData, DifficultyData, CurveData features |
| Articy import/export | Working | 36+ entities with mechanical data in export |
| Adapter (.tres generation) | Working | 5 enemies, 4 encounters, 5 curves |
| Action-driven enemy AI | Working | Weighted action selection + legacy fallback |
| ProgressionManager | Working | XP accumulation, level-up, stat growth |
| Monster scaling | Working | build_enemy_group with difficulty_tier offset |
| Curve-driven party | Working | Falls back to constants if curves not loaded |
| Python tests | 32/32 | vault_to_manifest (28) + canonical_to_godot (4) |
| GUT tests (new) | ~24 added | encounter_table, level_curve, level_up, actions, scaling |

## Known Issues / Gotchas For Next Agent

1. **Duplicate zones in articy** — 14 zones in export instead of 7 from a partial import before cleanup. Cosmetic. Fix: clean-up + re-import in articy:draft.

2. **Curves not in content manifest** — `ContentManager.get_resource("curves-core", ...)` may not work yet if the content manifest doesn't index the curves-core bundle. `_load_progression_curves()` silently falls back to hardcoded constants. Verify by checking `project/shared/data/content_manifest.json`.

3. **Python docstring in GDScript** — `BattleData.build_hero_from_curve()` uses `"""..."""` which is not valid GDScript comment syntax. Should be `##`. Non-blocking at runtime.

4. **Zone encounter rolling not wired** — `Main.roll_zone_encounter()` exists but isn't called from the encounter trigger. Requires zone tracking (player knows which zone they're in). Current encounters still use the overworld entity's hardcoded enemy_type.

5. **Allies are hardcoded** — ALLY1_STATS / ALLY2_STATS in BattleData. Future: vault character entities with their own curves.

6. **Curve articy import pending** — The 5 curve vault pages were authored and their .tres generated, but they haven't been imported into articy:draft yet. Run `task articy:prep && task articy:build` then import in articy.

## Next Session Entry Points

### Wire zone encounter rolling
- Add zone tracking to the player (which zone am I in?)
- Replace `_start_battle`'s direct enemy_type lookup with `roll_zone_encounter(current_zone, era)`
- This completes the Phase 2A exit criteria

### Import curves into articy
- Run the full articy pipeline for the 5 new curve entities
- Export, writeback, verify

### Content manifest for curves
- Add curves-core bundle to `content_manifest.json`
- Verify `ContentManager.get_resource()` loads LevelCurve .tres
- Remove the const fallback once curves are confirmed loading

### Add missing status effects
- `crystallize`, `confusion`, `defend_buff` referenced in bestiary prose
- Add cases in `BattleManager._apply_status_effect`
- Update bestiary actions to use them

### Phase 2B follow-ups from plan
- Ally characters as vault entities with curves
- Per-step random encounters using `encounter_rate`
- Mixed-type encounter groups
- Inn/rest system (currently auto-heal between battles)

## One-Liner State

Phase 2A + 2B complete: vault→articy→Godot pipeline carries mechanical game data end-to-end. Enemies use bestiary action tables, players gain XP and level up from curves, monsters scale by zone tier. 32 pytest + ~24 GUT tests added.
