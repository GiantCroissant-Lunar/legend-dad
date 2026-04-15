---
date: 2026-04-16
agent: claude-code
branch: main
version: 0.1.0-286
tags: [dev-log, planning, articy, pipeline, content-mechanics, progression]
---

# Session Dev-Log — Articy Phase 2 Plan Authored

## Summary

Goal: shape the next big design chunk — "what monsters live where, how
they act, how leveling works" — into an actionable plan that flows
through the existing vault → articy → Godot pipeline rather than being
hardcoded in GDScript.

Outcome: a 16-task, two-sub-phase plan committed at
`vault/plans/2026-04-16-content-mechanics-pipeline-phase2.md`. No
production code touched yet — planning artifact only.

## Changes

- `73927fa` plan: articy phase 2 — content mechanics + progression pipeline (this session)
- `3e16aa0` feat(encounters): multi-enemy groups rolled from EnemyDefinition data (earlier this session)
- `c4bd56f` feat(battle): status system polish, enemy AI, and level-gated spell learning (earlier this session)

## What The Plan Covers

### Phase 2A — Bestiary Mechanics & Zone Encounters (Tasks 1-8)

1. Schema: add `battle_stats`, `actions`, `encounter_table`,
   `difficulty_tier`, `recommended_level_*` to `import-manifest.schema.json`
2. Parser: teach `vault_to_manifest.py` to lift the new frontmatter
3. Content: author mechanical frontmatter into the 5 existing bestiary
   entries (Crystal Crawler, Iron Borer, Moss Lurker, Shade Wisp,
   Thornbriar Stalker) + 7 zones + 4 locations
4. Godot: new `EncounterTable` Resource + `encounters-core` bundle
5. Adapter: `scripts/adapters/canonical_to_godot.py` emits `.tres`
   for enemies + encounters from `canonical.json`
6. Battle integration: enemies pick actions via weighted `frequency`;
   `main.gd` rolls encounters from the zone's table instead of
   hardcoded overworld spawns

### Phase 2B — Leveling Curves & Progression (Tasks 9-16)

1. Schema: new `curve` entity type (`xp_to_level`, `stat_growth`,
   `monster_scaling` kinds)
2. Content: author 5 curves (father/son XP, father/son stat growth,
   monster-scaling by difficulty tier)
3. Godot: `LevelCurve` Resource + `ProgressionManager` autoload
4. Victory → XP award → level-up signal → stat growth applied
5. Monster scaling: zone `difficulty_tier` → level offset → HP/atk/def
   percentage bump
6. Delete hardcoded `FATHER_STATS` / `SON_STATS`; construct party
   from curves

## Design Decisions Locked

- **`frequency` is relative weight** (not probability). Normalized at
  roll time. Lets authors express "70/30 split" as `0.7 / 0.3` or
  `7 / 3` — math is identical.
- **Status ids match** `BattleManager._apply_status_effect` switch
  cases (current set: `sleep`, `poison`, `paralysis`, `stopspell`).
  Task 3/4 reference `crystallize`, `confusion`, `defend_buff` —
  flagged as follow-up to add those cases before the actions using
  them become usable.
- **Era gate** on encounter_table entries: `father` / `son` / `both`.
- **Level-up fully heals** the leveling combatant (DQ1 convention).
- **Monster scaling is multiplicative** (HP × growth%, atk × growth%)
  not a full stat-block replacement — keeps bestiary prose intact
  while scaling the numbers.
- **Era encoding** between Godot and vault: `C_TimelineEra.Era.FATHER`
  ↔ `"father"` string (helper `_era_to_string` in main.gd).

## What's Intentionally Out of Scope

- Mixed-type groups (Slime + Dracky in one encounter) — separate plan
- Elite / mini-boss variants (Prism Crawler) — post-2B
- Ally characters as first-class vault entities — currently left as
  constants; folded into a future "character-authoring" plan
- Per-step random encounter rolls (DQ1 style) — right now encounters
  fire on face-enemy-and-interact; random rolling is a separate
  overworld task
- Status UI polish beyond the existing Zz glyph — out of this plan
- Class-based Son-era party (Knight / Priest / Mage) — follow-up

## Plan Structure Notes

Each task has:
- Explicit **Files** section (new + modified with paths)
- Bite-sized **Steps** (~2-5 minutes each) with:
  - Test-first where code is involved (failing test → minimal impl → pass)
  - Exact code blocks (no placeholders like "add error handling")
  - Exact commands + expected output
  - Commit message + staged paths at the end of each task

Per the superpowers `writing-plans` skill convention, the plan doc
starts with the "REQUIRED SUB-SKILL: subagent-driven-development or
executing-plans" banner — next agent to execute just picks an approach.

## Verification

No code changes this commit, so no test runs. The plan itself passed
the skill's self-review gates:
- Spec coverage (all four user asks — monster placement, player
  leveling, monster leveling, actions — have mapped tasks)
- No placeholders (searched the doc for TBD/TODO/implement-later)
- Type consistency (`EncounterTable.entries` uses `bestiary_id`
  across Tasks 6+7; `LevelCurve.data_points` uses `level` + stat keys
  across Tasks 10+11)

## Follow-up Decisions For Next Agent

1. **Execution approach** — the user picked "commit plan first, review
   later" (option 3) so the plan stands on its own. Next
   implementation session picks between subagent-driven-development
   (recommended for 16 tasks) or executing-plans (inline).
2. **Status case additions** — before Task 3 or Task 8 runs,
   `BattleManager._apply_status_effect` needs `crystallize`,
   `confusion`, `defend_buff` cases OR those actions are dropped
   from bestiary authoring. Cleanest: add the cases first as a small
   prep commit.
3. **Task 12 party-persistence** — the current code reconstructs the
   party every encounter. Task 12 needs party combatants to persist
   across battles so XP accumulates. Plan has this as a drive-by
   change inside `_on_battle_ended` but it deserves a small standalone
   refactor first to avoid conflating two concerns.
4. **Adapter idempotency** — Task 16 asserts `task content:generate:tres`
   is a no-op on the second run. Adapter emits `.tres` with sorted
   keys + stable float formatting; if CI flags diffs, the key-order
   logic in `_update_bundle` may need a canonical sort.

## Files Changed

```
vault/plans/2026-04-16-content-mechanics-pipeline-phase2.md   new (1654 lines)
vault/dev-log/2026-04-16-phase2-planning.md                   new (this file)
vault/dev-log/2026-04-16-handover.md                          new
```
