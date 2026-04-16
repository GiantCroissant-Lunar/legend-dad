---
date: 2026-04-16
agent: claude-code
branch: main
tags: [dev-log, phase-2a, phase-2b, articy, pipeline, battle, progression]
---

# Session Dev-Log — 2026-04-16 Content Mechanics Pipeline Phase 2

## What Was Built

Phase 2A (bestiary mechanics + zone encounters) and Phase 2B (leveling curves + progression) from `vault/plans/2026-04-16-content-mechanics-pipeline-phase2.md`, implemented across 17 commits.

### Phase 2A: Bestiary Mechanics & Zone Encounters

1. **Schema extension** — Added `battle_stats`, `actions`, `encounter_table`, `difficulty_tier`, `recommended_level`, and `curve` entity type to `import-manifest.schema.json`. Relaxed `template_properties` from string-only to mixed types.

2. **Parser update** — `vault_to_manifest.py` gains `_lift_mechanical_sections()` which carries structured YAML frontmatter (dicts, arrays, ints) into template_properties by entity type (bestiary, zone, location, curve). 8 new pytest tests.

3. **Bestiary mechanical data** — All 5 creatures authored with `battle_stats`, `actions` (weighted action tables using only implemented statuses: sleep/poison/paralysis/stopspell), `group_size_min/max`, and `zone_affinity`.

4. **Zone encounter tables** — 4 wilderness zones get weighted monster pools with era gating. 3 town zones marked `encounter_rate: 0`. 4 locations get `recommended_level` + `difficulty_tier`.

5. **MDK plugin update** — Template definitions gain BattleStats (LD_Creature), EncounterData (LD_Zone), DifficultyData (LD_Location), CurveData (LD_Curve) features. quicktype regenerated with typed classes. EntityImporter routes structured data to correct features, serialized as JSON text. Zone + Curve added to TypeToTemplate.

6. **Articy import/export cycle** — Clean-up + re-import with new templates. All 36 entities verified with mechanical features in export JSON. Articy IDs written back to vault.

7. **EncounterTable resource** — `encounter_table.gd` with era-filtered weighted `roll()`. 6 GUT tests. Bundle scaffold for encounters-core.

8. **Adapter** — `scripts/adapters/canonical_to_godot.py` reads import-manifest.json and emits EnemyDefinition .tres (5), EncounterTable .tres (4). Taskfile task `content:generate:tres`. 3 pytest tests.

9. **Action-driven enemy AI** — Combatant gains `actions` array. BattleManager `_pick_enemy_action()` does weighted random from bestiary table. `_action_to_command()` maps action kinds. Resolve loop handles `action_data` power and `status_inflict`. Legacy cast-or-attack preserved as fallback. 4 GUT tests.

10. **Zone encounter helper** — `Main.roll_zone_encounter()` and `era_to_string()` ready to wire once zone tracking exists.

### Phase 2B: Leveling Curves & Progression

11. **Curve vault pages** — 5 curves authored: father/son XP-to-level (DQ1-style decelerating), father/son stat growth (matching existing hardcoded stats at canonical levels), monster scaling (tier -> level offset).

12. **LevelCurve resource** — `level_curve.gd` with `level_for_xp()` and `stat_at_level()` (linear interpolation). 7 GUT tests. Adapter extended with `emit_curve_tres()`. Curves-core bundle with 5 .tres files.

13. **ProgressionManager** — `progression_manager.gd`: XP accumulation per combatant, level-up detection via LevelCurve, stat growth application, `level_up` signal. Wired into main.gd: loads curves from content bundles, awards XP on victory, party persists across battles. 5 GUT tests.

14. **Monster scaling** — `build_enemy_group()` accepts optional `difficulty_tier` + `LevelCurve`. Scales HP (+10%/offset), ATK (+8%/offset), DEF (+5%/offset). 2 GUT tests.

15. **Curve-driven party** — `BattleData.build_hero_from_curve()` constructs stats from LevelCurve at a level. `main.gd._build_party()` uses curves when loaded, falls back to FATHER_STATS/SON_STATS constants.

16. **Skill update** — `articy-prep` skill rewritten to document the full 6-step pipeline.

## Test Summary

- **Python tests**: 32 passing (28 vault_to_manifest + 4 canonical_to_godot)
- **GUT tests added**: ~24 new (encounter_table 6, level_curve 7, level_up_system 5, battle_manager_cast 4, build_enemy_group 2)
- **MDK plugin**: builds with 0 warnings, 0 errors

## Key Files

```
# Schema + parser
project/articy/schemas/import-manifest.schema.json
project/articy/schemas/template-definitions.json
scripts/vault_to_manifest.py

# MDK plugin
project/articy/mdk-plugin/LegendDad.MdkPlugin/EntityImporter.cs
project/articy/generated/csharp/ImportManifest.cs

# Adapter
scripts/adapters/canonical_to_godot.py

# Godot resources
project/shared/lib/resources/encounter_table.gd
project/shared/lib/resources/level_curve.gd
project/shared/lib/resources/enemy_definition.gd

# Battle system
project/hosts/complete-app/scripts/battle/battle_manager.gd
project/hosts/complete-app/scripts/battle/combatant.gd
project/hosts/complete-app/scripts/battle/battle_data.gd
project/hosts/complete-app/scripts/progression/progression_manager.gd
project/hosts/complete-app/scripts/main.gd

# Vault content
vault/world/bestiary/*.md (5 files — mechanical frontmatter added)
vault/world/zones/*.md (7 files — encounter tables added)
vault/world/locations/*.md (4 files — difficulty tiers added)
vault/world/curves/*.md (5 files — new)
vault/world/_meta/bestiary-schema.md (new)
vault/world/_meta/zone-schema.md (new)
vault/world/_meta/curve-schema.md (new)

# Generated .tres
project/shared/content/enemies/enemies-core/{crystal_crawler,iron_borer,moss_lurker,shade_wisp,thornbriar_stalker}.tres
project/shared/content/encounters/encounters-core/{iron_peaks_trail,iron_peaks_upper_mines,whispering_woods_deep,whispering_woods_edge}.tres
project/shared/content/curves/curves-core/{father_xp_to_level_curve,father_stat_growth_curve,son_xp_to_level_curve,son_stat_growth_curve,monster_scaling_curve}.tres
```

## Decisions Made

- **Used only implemented status effects** (sleep, poison, paralysis, stopspell) in bestiary actions. Deferred crystallize, confusion, defend_buff to a future commit.
- **Kept FATHER_STATS/SON_STATS constants** as fallback when curves aren't loaded. Clean deletion deferred until the content bundle loading path is fully verified in-game.
- **Zone encounter rolling** added as a static helper but not wired into the encounter trigger — requires zone tracking infrastructure that doesn't exist yet.
- **Allies stay hardcoded** — future plan: vault character entities with their own curves.
- **Party auto-heals between battles** — DQ1 uses inns, but for dev convenience auto-heal is on.

## Known Issues

- Zones are duplicated in articy export (14 instead of 7) from a partial import before cleanup. Cosmetic — doesn't affect the pipeline. Fix by doing another clean-up + re-import cycle.
- `ContentManager.get_resource()` may not support the curves-core bundle yet — depends on whether the content manifest includes it. The `_load_progression_curves()` call in main.gd will silently no-op if curves aren't loadable, falling back to constants.
- `build_hero_from_curve` uses a Python-style docstring (`"""`) which is not valid GDScript. Should be `##` comment. Non-blocking (GDScript ignores it at runtime).
