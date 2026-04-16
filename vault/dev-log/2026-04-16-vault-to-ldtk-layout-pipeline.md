---
date: 2026-04-16
agent: claude-code
branch: main
tags: [dev-log, vault, articy, ldtk, encounters, pipeline]
---

# Dev Log — vault→articy→LDtk content + layout pipeline

## What landed

Seven commits on `main`, all pushed together at end of session. The
through-line: make the vault the authoritative source for every kind of
zone data — prose, dimensions, encounter tables, and now tile layouts
plus entity placements — with deterministic renders into downstream
artifacts (articy templates, `.tres` resources, LDtk levels).

| # | Commit | What it shipped |
|---|---|---|
| 1 | `49feeb1` | 4 new locations + 12 NPCs + 8 quests filling the DQ1-style tier ladder: Saltmere Port (T3), Ashenford (T4), Hollow's Rest (T6), Lastwatch (T7). Mixed named + archetype NPCs per the research note recommendation. |
| 2 | `79d887a` | 10 zone pages (per-location sub-regions) with full encounter tables, grid dimensions, era gating. Parent-location backlinks + creative prompts match the existing zone pattern. |
| 3 | `e9accc1` | Articy import roundtrip: user ran MDK import + export in Articy, `task articy:writeback` patched articy-ids into 39 vault frontmatters (34 new + 5 curves that had been pending from Phase 2B), `task content:generate:tres` emitted 4 new encounter `.tres` resources. |
| 4 | `eb53e7f` | First-time content-bundle build on this Windows checkout: ran `task share:link`, seeded Godot caches, built all 6 bundles (curves-core, encounters-core, enemies-core, hud-battle, hud-core, spells-core), regenerated `content_manifest.json`. Fixes "curves-core not indexed" gotcha. |
| 5 | `142c26c` | Zone encounter rolling wired end-to-end: `LocationManager.get_current_zone()/set_current_zone()`, `locations.json.default_zone`, `Main._start_battle` now rolls from the zone's `EncounterTable` first (with monster-scaling applied per `difficulty_tier`) and falls back to the overworld entity's enemy_type. Plus fixes to two pre-existing Mac-authored parse errors that were cascading through GUT suite on this Windows checkout. |
| 6 | `1319b35` | LDtk level-stub generation: `ldtk_sync` now reads zone dimensions from vault frontmatter and appends new levels for zones that weren't in the previous sync. 7 → 17 levels, each sized from the zone page's `grid-width × grid-height`. |
| 7 | `53ad4fd` | **Vault-authored zone layouts.** Each zone can carry a `## Layout Spec` fenced YAML block describing Collision/Terrain/Terrain_Father/Terrain_Son/Entities via high-level primitives (base, regions, paths, era_overlays, entities) or a `raw:` escape hatch. `task ldtk:sync` renders the spec into LDtk layers and OVERWRITES (vault wins, editor is preview). Shared `ldtk_vocabulary.py` defines collision + biome-scoped terrain symbol tables consumed by both the renderer and `ldtk_sync`. |

## Why this session mattered

Going in, the vault-to-runtime pipeline was proven for **entities**
(characters, bestiary, spells, zones-as-data) but not for **level
geometry**. The only painted LDtk level — `Whispering_Woods_Edge` — had
its tile CSV hardcoded as a Python constant in `scripts/ldtk_sync.py`,
with no way to extend that pattern to other zones without writing more
Python constants. New zones added during the vault expansion (10 of
them this session) had nowhere to land their tile data.

The solution splits authoring across a clean seam:

```
Describe (vault .md prose + frontmatter + Layout Spec YAML)
    │
    │  task articy:prep      (parse + lift into manifest)
    ▼
Structure (manifest JSON)
    │
    │  task ldtk:sync        (render layout spec into layer CSVs)
    ▼
Preview (LDtk editor reads .ldtk)
    │
    │  pck build → game launch
    ▼
Runtime (Godot reads the same .ldtk)
```

The seam is clear: **vault is the source, everything else is derived**.
Re-running the pipeline is idempotent and overwrites — if you
hand-painted tiles in LDtk, next sync clobbers them, so there's
exactly one place to author zone content (the vault page).

## What's now possible that wasn't

1. **An agent can paint tile layouts from prose.** Given a zone's "Layout & Terrain" section, the agent emits a Layout Spec block under the same page. `task articy:prep && task ldtk:sync` renders it. Reviewable in the vault (YAML diff, not JSON soup). Testable via the pure-function renderer.

2. **Per-zone dimensions honored.** Previously every level was 20×16. Now each level is sized from its vault `grid-width × grid-height`. Hollow's Rest Hearth Circle is 18×16, Saltmere Chalk Estuary is 28×20, etc.

3. **Zone encounters actually work at runtime.** Walking into battle from the overworld rolls the zone's `EncounterTable`, applies the zone's `difficulty_tier` through the monster-scaling curve, and produces a scaled enemy group. Falls back to the old overworld-entity path when the zone has no table (towns).

4. **Content bundles are reproducible on new machines.** The full build pipeline runs cleanly from a fresh checkout (`task share:link` + `task setup:godot` + `task content:build:all` documented in dev-log).

## Gotchas and discoveries

1. **Taskfile has Mac-hardcoded `PYTHON_BIN`.** Every Python-shell task (articy:prep, ldtk:sync, content:manifest, test:python) needs `PYTHON_BIN=python3` override on Windows. Candidate for follow-up: auto-detect via `env:` in Taskfile or a wrapper script.

2. **Three pre-existing Mac-authored parse errors were blocking GUT.** `battle_manager._apply_status_effect` took `SpellDefinition` but action-system callers passed `String`; `main._load_progression_curves` had untyped for-loop variables. All three fail-fast on Windows GDScript's stricter type checking. Fixed in `142c26c` — GUT now runs 85/86 (up from 35/78 cascade failures). Only remaining failure is the known flake `test_pause_when_already_paused`.

3. **`test_preserves_levels` regressed from commit 1319b35.** The test expected `merge_ldtk_project` to NOT append levels from `new_defs`. The new "append missing zones" feature made it fail. Test updated to assert both preservation (existing levels untouched) and appending (new-in-manifest levels added) in separate tests.

4. **LDtk runtime reads tile layers but ignores Entity instances today.** `ldtk_importer.gd:190-215` parses entity metadata into `Node2D.set_meta(...)` but `main.gd:612` frees the level tree without spawning anything from the entities layer. Layout Spec `entities:` blocks emit LDtk entity instances in forward-compatible format — they inform the editor preview and are ready for when `ldtk_entity_placer.gd` spawn logic is written.

5. **`Whispering_Woods_Edge` grid-width was lying.** Vault declared 24×20 (480 cells) but the baked CSV was 20×16 (320 cells). Corrected frontmatter to match what actually ran in-game. The hardcoded CSV is now preserved byte-for-byte via `raw:` in the Layout Spec.

6. **Articy export/import manifest and `.adpd` partition files churn a lot.** Every articy re-import rewrites the full JSON export and the two `.adpd` files, producing large diffs (+3000/-3800 in `e9accc1`). These stay tracked because the handover pattern is to commit them together with writeback + tres regen — otherwise a fresh clone can't rebuild state without running Articy locally.

## Test posture at session end

| Layer | Status |
|---|---|
| Python (`pytest tests/`) | 157/157 — adds 12 `ldtk_vocabulary` + 38 `zone_layout_render` + 5 `vault_to_manifest` layout tests |
| GUT (`task test:godot`) | 85/86 — pre-existing flake `test_pause_when_already_paused` unchanged |
| Manifest schema | Validates — 75 entities |
| LDtk byte-identity fence | WWE renders byte-identical Collision to pre-refactor hardcoded array (73 nonzero cells, same positions) |

## Files that are now the interesting ones to read

**For understanding the pipeline:**

- [vault/world/_meta/zone-schema.md](../world/_meta/zone-schema.md) — Layout Spec grammar + biome vocabulary
- [vault/dev-log/2026-04-16-ldtk-layout-pipeline.md](./2026-04-16-ldtk-layout-pipeline.md) — end-to-end pipeline walkthrough (authored earlier this session)
- [scripts/zone_layout_render.py](../../scripts/zone_layout_render.py) — the renderer (pure-function; no I/O)
- [scripts/ldtk_vocabulary.py](../../scripts/ldtk_vocabulary.py) — collision + terrain symbol tables

**For understanding what's on disk now:**

- [vault/world/zones/whispering-woods-edge.md](../world/zones/whispering-woods-edge.md) — the first real Layout Spec (uses `raw:` to preserve the legacy tile pattern)
- [project/ldtk/legend-dad.ldtk](../../project/ldtk/legend-dad.ldtk) — 17 levels, WWE painted, others empty canvases awaiting specs

**For wiring understanding:**

- [project/hosts/complete-app/scripts/main.gd:270-340](../../project/hosts/complete-app/scripts/main.gd) — `_start_battle` now calls `roll_zone_encounter` first, falls back to entity lookup
- [project/hosts/complete-app/scripts/location_manager.gd:25-34](../../project/hosts/complete-app/scripts/location_manager.gd) — `_current_zone_id` tracking
