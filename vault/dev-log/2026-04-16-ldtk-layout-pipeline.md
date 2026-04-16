---
date: 2026-04-16
agent: claude-code
branch: main
tags: [pipeline, ldtk, zones, layout]
---

# LDtk Tile Layout Pipeline — End-to-End

## The question this answers

> How do we actually lay out tiles in LDtk for each location to reflect
> what's being designed in the vault and/or articy?

The answer is a three-stage pipeline: **vault describes → pipeline
generates stubs → human paints in LDtk editor**. This doc explains each
stage, what's automated, what's human-authored, and where the seams are.

## Pipeline overview

```
vault/world/zones/*.md          ← you describe the zone in prose + frontmatter
       │
       │  task articy:prep       (scripts/vault_to_manifest.py)
       ▼
project/articy/import-manifest.json
       │
       │  task ldtk:sync         (scripts/ldtk_sync.py)
       ▼
project/ldtk/legend-dad.ldtk    ← empty level stub at correct grid size
       │
       │  ── Open LDtk editor, paint tiles, place entities ──
       ▼
project/ldtk/legend-dad.ldtk    (same file, now with painted data)
       │
       │  Runtime load
       ▼
LocationManager → tilemap + collision grid + entity spawns
```

The pipeline is **idempotent and non-destructive**: re-running
`task articy:prep && task ldtk:sync` after editor work **preserves every
painted tile** and every placed entity instance. Only new zones (zones that
appeared in the manifest since last sync) get fresh empty level stubs.

## Stage 1: describe the zone in vault

Every zone page under `vault/world/zones/*.md` declares its topology and
size in frontmatter:

```yaml
---
type: zone
parent-location: "[[Saltmere Port]]"
zone-type: town        # overworld | town | dungeon | cave | interior | boss-arena
biome: town            # town | field | dungeon (drives tileset/palette)
floor: 0               # multi-floor dungeons, 0-indexed
grid-width: 24         # zone width in tiles (16px each)
grid-height: 18        # zone height in tiles
era: "Both"
encounter_table: [...] # zone-schema.md
encounter_rate: 0.10
difficulty_tier: 3
---
```

The prose sections that follow (Overview, Layout & Terrain, Entities &
Encounters, Era Variants, Creative Prompts) are the **design brief** you
hand to yourself when you sit down to paint. They don't automatically
translate into tiles — they're the source of truth for the human
painting decisions in LDtk.

See [vault/world/_meta/zone-schema.md](../world/_meta/zone-schema.md) for
required fields.

## Stage 2: generate the LDtk level stub

```bash
task articy:prep        # vault → import-manifest.json
PYTHON_BIN=python3 task ldtk:sync   # manifest → legend-dad.ldtk
```

What this does:

1. `vault_to_manifest.py` lifts zone frontmatter (including `grid-width`,
   `grid-height`, `zone-type`, `parent-location`, `floor`, `biome`) into
   `template_properties` on each zone entity.
2. `ldtk_sync.py` walks zone entities in the manifest. For each zone whose
   `identifier` (derived from display_name) is **not already a level in
   legend-dad.ldtk**, it appends a fresh empty level sized from
   `grid_width × grid_height × 16px`.
3. Existing levels with painted tiles are left untouched.
4. All layer/entity/enum definitions are refreshed from the manifest so
   the editor picks up new bestiary types, new NPCs, new event categories.

As of this session: **17 levels** in legend-dad.ldtk (7 original + 10 new
from the Saltmere / Ashenford / Hollow's Rest / Lastwatch zones), each at
the exact dimensions declared in the vault page.

## Stage 3: paint tiles in the LDtk editor

Open `project/ldtk/legend-dad.ldtk` in LDtk Deepnight (the editor at
https://ldtk.io). The editor will show every level in the world view at
the correct size. Pick a level, flip layers, paint.

### Layers per level

| Layer | Type | Purpose |
|---|---|---|
| Entities | Entities | NPC spawn points, interactables, encounter triggers, quest anchors |
| Terrain_Son | IntGrid | Son-era overlay tiles (corruption, decay, era-specific props) |
| Terrain_Father | IntGrid | Father-era overlay tiles (lived-in, pre-corruption) |
| Terrain | IntGrid | Shared ground layer (paths, base terrain) |
| Collision | IntGrid | Walkable (0) / solid (1) / water (2) / pit (3) |

The IntGrid values that drive each layer are defined in `ldtk_sync.py`
(`INTGRID_COLLISION` and `INTGRID_TERRAIN`). Universal values 0-9 are
shared across biomes; 10-19 are field-specific, 20-29 dungeon-specific,
30-39 town-specific. Changing these in the script and re-running
`ldtk:sync` updates the editor's value palette without touching painted
data (since painted data is raw int values per cell, not named
references).

### Entity placement

The editor's Entity defs include `Character`, `Zone`, `Faction`, `Quest`,
`Item`, `Event`, `Lore`, `Creature`. When you drop one on the Entities
layer, you pick which vault entity it refers to from the list (which is
populated from the manifest during sync). Placing a `Character` means
"an NPC spawns here that renders / dialogues from this vault character
page." Placing a `Creature` on the overworld is how the player triggers a
combat encounter.

### The Entity-placement shortcut for encounter spawns

Zones with `encounter_table` declared don't need a `Creature` entity
placed per encounter — the runtime rolls from the table automatically
when the player enters battle. You only need to place a `Creature` if
you want a **fixed** encounter at a specific tile (boss fight, scripted
ambush).

## Stage 4: iterate

Typical loop:

```bash
# 1. Edit vault page (e.g. adjust grid-height from 18 → 20 for more room)
vim vault/world/zones/lastwatch-broken-bailey.md

# 2. Run the pipeline
task articy:prep
PYTHON_BIN=python3 task ldtk:sync

# 3. Open the editor (LDtk will see the resized level and adapt)
#    — Painted tiles inside the old bounds are preserved; the extra rows
#      come in empty.

# 4. Paint more. Save. Commit .ldtk.
```

## What the pipeline does NOT do (on purpose)

- **It does not generate tile layouts from prose.** Nothing reads
  "Cobblestone paths radiate from the well to four exits" and places
  those tiles for you. That's the human's job; the prose is the brief.
- **It does not place NPC instances.** The vault prose names NPCs but
  doesn't say "at tile (12, 4)". That's editor-authoring.
- **It does not rebuild painted levels from scratch when zone frontmatter
  changes.** If you rename `grid-width: 18 → 20`, the painted tiles inside
  the original 18 columns stay put; column 19 comes in empty.

## What to do next

1. **Open `project/ldtk/legend-dad.ldtk`** in the LDtk editor and walk
   through the 17 levels. Each empty one is a canvas; the prose in the
   corresponding `vault/world/zones/*.md` is the brief.
2. **Paint Collision + Terrain first.** Get the walkable shape right
   before worrying about decoration.
3. **Then place Entities** — Characters at the NPC locations the prose
   calls out, Quest anchors where scripted events happen, Creatures for
   any fixed encounters outside the random-roll table.
4. **Tilesets are a separate issue.** `defs.tilesets` is currently empty
   in the .ldtk — the editor will paint IntGrid values without a tileset
   preview behind them, showing coloured blocks from `INTGRID_TERRAIN`.
   Actual pixel art tilesets come from the ComfyUI generation pipeline
   (`task comfyui:tileset`) and get linked in the editor per-biome.

## Files touched this session

| File | What changed |
|---|---|
| `scripts/vault_to_manifest.py` | `_MECHANICAL_KEYS_ZONE` now includes `zone-type`, `parent-location`, `floor`, `biome`, `grid-width`, `grid-height`. Dashed keys are normalized to underscores in `template_properties`. |
| `scripts/ldtk_sync.py` | `_make_levels_from_zones` reads zone dimensions from `template_properties.grid_width/grid_height`. `merge_ldtk_project` now appends new levels for zones that weren't in the previous sync, offsetting their `worldX` so they don't overlap existing levels in the world view. |
| `project/articy/import-manifest.json` | Regenerated: 75 entities, zone entities now carry dimensional fields. |
| `project/ldtk/legend-dad.ldtk` | 7 → 17 levels. New levels are empty stubs at the correct per-zone dimensions. |

## Known gaps / future work

- `ldtk:sync` uses the Mac `PYTHON_BIN` path in Taskfile.yml. On Windows
  you must run `PYTHON_BIN=python3 task ldtk:sync`. (Same issue exists
  for every Task that shells Python — could be fixed with an `env:`
  block or a platform detector in the Taskfile.)
- `defs.tilesets` is empty — no pixel art linked yet. Field/dungeon/town
  tilesets get generated via ComfyUI but aren't imported into the .ldtk
  yet. Once they are, the terrain IntGrid values can auto-map to tiles
  via LDtk's auto-layer rules.
- `Whispering_Woods_Edge` has hand-authored CSV baked into
  `ldtk_sync.py` (`_WWE_COLLISION`, `_WWE_TERRAIN`). That was a bootstrap
  convenience; future zones should be painted in the editor, not coded in
  the script. The bake-in mechanism remains in `LEVEL_LAYOUTS` for
  regression-testing but shouldn't be extended.
