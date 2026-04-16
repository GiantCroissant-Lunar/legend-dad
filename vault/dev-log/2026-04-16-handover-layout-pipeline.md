---
date: 2026-04-16
agent: claude-code
branch: main
tags: [handover]
---

# Session Handover — 2026-04-16 (vault→LDtk layout pipeline)

## One-liner state

Vault zone pages are now the authoritative source for LDtk tile
layouts. The infrastructure works end-to-end; the follow-up work is
writing Layout Specs for the 16 empty zones.

## Current state snapshot

| Area | Status | Notes |
|---|---|---|
| Vault entities | 75 | 4 new locations, 12 NPCs, 8 quests, 10 zones added this session |
| Articy roundtrip | Clean | MDK plugin deployed, 34 new entities imported, writeback populated articy-ids in 39 frontmatters |
| LDtk levels | 17 | All zones represented; dimensions per vault frontmatter. Only `Whispering_Woods_Edge` has painted tiles. |
| Content bundles | 6 | All in content_manifest.json (was 0 registered on this checkout pre-session) |
| Zone encounter rolling | Working | `_start_battle` → `roll_zone_encounter` → scaled by `difficulty_tier` → falls back to entity lookup |
| Layout Spec renderer | Working | Pure function; 38 unit tests; WWE byte-identity fence passes |
| Python tests | 157/157 | +55 new tests this session |
| GUT tests | 85/86 | 1 pre-existing flake (`test_pause_when_already_paused`) |

## Key files touched this session

```
# New infrastructure
scripts/ldtk_vocabulary.py                 Collision + terrain symbol tables, biome validation
scripts/zone_layout_render.py              Pure renderer: spec → CSV arrays + entity instances
tests/test_ldtk_vocabulary.py              12 tests
tests/test_zone_layout_render.py           38 tests including WWE byte-identity fence

# Modified
scripts/ldtk_sync.py                       Wire renderer + entity instance emission; delete _WWE_* constants
scripts/vault_to_manifest.py               extract_layout_spec() + lift into template_properties.layout
project/hosts/complete-app/scripts/main.gd          _start_battle routes through roll_zone_encounter
project/hosts/complete-app/scripts/location_manager.gd   get/set_current_zone + default_zone seeding
project/hosts/complete-app/scripts/battle/battle_manager.gd   _apply_status_effect signature fix
project/shared/data/locations.json          default_zone per location

# Vault
vault/world/locations/{saltmere-port,ashenford,hollows-rest,lastwatch}.md
vault/world/zones/{saltmere-*,ashenford-*,hollows-rest-*,lastwatch-*}.md  (10 new)
vault/world/characters/{cael-vire,rhen-halloway,torbin,jessa-vale,...}.md  (12 new)
vault/world/quests/{iron-in-the-tide,smugglers-cove,the-vanguards-debt,...}.md (8 new)
vault/world/_meta/zone-schema.md            Layout Spec grammar + biome vocabulary
vault/world/zones/whispering-woods-edge.md  First real Layout Spec (raw:)

# Generated / derived (committed together with authoring)
project/articy/import-manifest.json         75 entities
project/articy/export/*.json                Full articy re-export
project/ldtk/legend-dad.ldtk                17 levels, WWE painted
project/shared/content/encounters/encounters-core/*.tres   4 new encounter tables
project/shared/data/content_manifest.json   All 6 bundles registered
```

## Known issues / gotchas for next agent

1. **Taskfile `PYTHON_BIN` is Mac-hardcoded.** Every Python-shell task needs `PYTHON_BIN=python3` prefix on Windows. Workarounds:
   - `PYTHON_BIN=python3 task articy:prep`
   - `PYTHON_BIN=python3 task ldtk:sync`
   - `PYTHON_BIN=python3 task content:build -- <bundle>`

   Fix candidate: add platform detection to Taskfile or ship a wrapper script. Deferred this session.

2. **GODOT_PATH is Mac-hardcoded too.** Same pattern — override with `GODOT_PATH="/c/lunar-horse/tools/Godot_v4.6.1-stable_mono_win64/Godot_v4.6.1-stable_mono_win64_console.exe"` when running bundle builds or GUT tests.

3. **Runtime ignores Entity instances in LDtk.** `ldtk_importer.gd:190-215` parses entity metadata correctly but `main.gd:612` frees the tree without spawning anything. Layout Spec `entities:` blocks emit LDtk entity instances in the correct forward-compatible format, but they do nothing in-game until someone writes `ldtk_entity_placer.gd`.

4. **Pre-existing flake still present:** `test_pause_when_already_paused` in `test_time_service.gd` fails intermittently. Unchanged from prior handovers. Counted as 1/86 every GUT run this session.

5. **WWE is the only painted level.** The other 16 LDtk levels are empty canvases waiting for Layout Specs. Walking into them in-game produces fallback/zero collision (entire zone walkable) + all-void terrain (invisible walls / empty visuals). This is fine for overworld exploration flow since the runtime only uses `LocationManager.load_location("whispering-woods")` at boot.

6. **Articy artifact churn is large.** Every articy re-import rewrites `project/articy/export/*.json` (~3000-4000 line diffs) and the two `.adpd` partition files. These are committed alongside vault changes so fresh clones stay reproducible. Don't be alarmed by large diffs on those files.

7. **LDtk `defs.tilesets` is empty.** Zero pixel art linked yet. The LDtk editor renders IntGrid values as colored blocks per `INTGRID_COLLISION`/`INTGRID_TERRAIN` color hints. Real tilesets come from the ComfyUI pipeline (`task comfyui:tileset`) — linking them into `defs.tilesets` and auto-mapping values to atlas cells is a separate follow-up.

## Next session entry points

### If you want to paint zones (highest-value next step)

The renderer works. The infrastructure tests pass. What's missing is
actual tile content for the 16 empty levels.

**Workflow for one zone:**

1. Pick a zone from the vault, e.g. [vault/world/zones/hollows-rest-hearth-circle.md](../world/zones/hollows-rest-hearth-circle.md).
2. Read its "Layout & Terrain" prose section — it describes the spatial shape the Layout Spec should reproduce.
3. Write a `## Layout Spec` block using high-level primitives (`base`, `regions`, `paths`, `era_overlays`, `entities`) — see [zone-schema.md](../world/_meta/zone-schema.md) for grammar.
4. Run `task articy:prep && PYTHON_BIN=python3 task ldtk:sync`.
5. Open `project/ldtk/legend-dad.ldtk` in LDtk editor; flip to the level; verify the shape matches the prose.
6. If Biome is wrong, check `biome:` in frontmatter — `field`/`dungeon`/`town` constrains which terrain symbols resolve.
7. Commit the vault page change plus the regenerated manifest + .ldtk.

Hollow's Rest Hearth Circle is a good first target: small (18×16), single era (son only), distinctive shape (tree-fall hollow with circle of cottages around a central hearth), biome is `field`.

### If you want to wire entity runtime spawn

Layout Spec `entities:` blocks are forward-compatible but runtime-inert.
Writing `ldtk_entity_placer.gd` (or extending `ldtk_level_placer.gd`)
to read `entityInstances` from loaded levels and spawn Godot nodes is
the missing piece.

Starting points:
- `ldtk_importer.gd:190-215` — where entity instances are parsed into metadata today
- `main.gd:211-247` — how the game currently spawns entities (hand-coded, not from LDtk)
- NPC types to wire: `Character` (dialogue NPC), `Creature` (fixed encounter), `Quest` (scripted event trigger)

### If you want to link tilesets

`defs.tilesets = []` in legend-dad.ldtk. ComfyUI tileset generation
exists via `task comfyui:tileset`. Missing: import the generated atlas
into the .ldtk tileset defs + configure auto-layer rules per biome.

This unblocks the LDtk editor showing real pixel art instead of colored
IntGrid blocks.

### If you want to fix the Windows/Mac Taskfile drift

`PYTHON_BIN` and `GODOT_PATH` are hardcoded for Mac. Everything on
Windows needs env overrides. Taskfile supports conditional `vars:`
blocks or platform detection. Would cut setup friction for the next
agent starting fresh on either OS.

## Commits on main this session

```
53ad4fd feat(ldtk): vault-authored zone layouts render through task ldtk:sync
1319b35 feat(ldtk): generate zone level stubs from vault; preserve painted data on merge
142c26c feat(encounters): wire zone encounter rolling through LocationManager
eb53e7f build(content): register all 6 bundles in content_manifest; add project autoloads + script UIDs
e9accc1 chore(articy): import 34 new entities + writeback IDs + regen .tres
79d887a feat(vault): 10 zone pages for Saltmere, Ashenford, Hollow's Rest, Lastwatch
49feeb1 feat(vault): 4 new locations, 12 NPCs, 8 quests filling DQ1-style ladder
```

Plus docs in this commit.

## Vault pages still in `draft` status

All 34 new entities authored this session are `status: draft`. Human
promotion to `reviewed` is the gate before treating them as canon. Also
worth a human read-through before next agent session:

- Location pages for Saltmere / Ashenford / Hollow's Rest / Lastwatch
- Character pages for Cael Vire, Rhen Halloway, Torbin, Jessa Vale (named) + 8 archetypes
- Quest pages for the 8 new main + side beats
- Zone pages (10) — the prose + encounter tables get promoted together
