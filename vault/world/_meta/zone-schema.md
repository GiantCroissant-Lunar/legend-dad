---
type: meta
---

# Zone Page Mechanical Frontmatter

## encounter_table

Weighted monster pool for this zone. The battle system rolls once per
encounter trigger using `weight` for probability, filtered by `era`.

```yaml
encounter_table:
  - bestiary: "[[Crystal Crawler]]"   # vault wikilink to a bestiary entry
    weight: 3                         # integer >= 1, relative weight
    era: "son"                        # "father" | "son" | "both"
  - bestiary: "[[Slime]]"
    weight: 5
    era: "both"

encounter_rate: 0.15   # 0.0-1.0; probability per player-step of triggering an encounter
difficulty_tier: 2     # 1-10; feeds monster level scaling in Phase 2B
```

## Era gating

`era: "father"` -- only rolls during the Father timeline.
`era: "son"` -- only rolls during the Son timeline.
`era: "both"` -- rolls in both eras (but individual stats may differ
via monster-scaling in Phase 2B).

## Encounter-free zones

Omit `encounter_table` entirely for towns / safe zones.
Set `encounter_rate: 0` to explicitly mark as safe.

## Layout Spec

Optional structured tile-layout authoring lives in a fenced YAML block
under a `## Layout Spec` section. When present, it becomes the source of
truth for Collision, Terrain, Terrain_Father, Terrain_Son, and Entities
layers in the LDtk level. Rendered through `scripts/zone_layout_render.py`
during `task ldtk:sync`.

**Authoring contract** (per user decision 2026-04-16): the vault spec is
canonical. Every `task ldtk:sync` re-renders and OVERWRITES the LDtk
level's layer data. Hand-painting in the LDtk editor is a preview tool,
not durable authoring. To change tiles, edit the spec.

### Grammar

```yaml
# All fields are optional. Missing fields fall through to defaults.

base:
  collision: empty        # one of: empty, solid, water, pit
  terrain: ground         # any symbol from the zone's biome vocabulary

raw:                      # escape hatch for pasting pre-computed CSVs
  Collision: [...]        # flat int array, length = grid_width * grid_height
  Terrain: [...]          # same
  Terrain_Father: [...]   # optional; defaults to copy of Terrain
  Terrain_Son: [...]      # optional; defaults to copy of Terrain

regions:                  # rect / circle stamps applied on top of base
  - id: cottage
    shape: rect           # or 'circle'
    at: [col, row]        # top-left for rect, (ignored for circle)
    size: [w, h]          # rect only
    center: [col, row]    # circle only
    radius: 2             # circle only
    collision: solid      # optional: omit to leave base collision
    terrain: building_wall
    openings:             # optional: punch cells through a region
      - at: [1, 2]
        collision: empty
        terrain: door

paths:                    # polyline strokes, Bresenham between waypoints
  - id: main_road
    points: [[c0, r0], [c1, r1], [c2, r2]]
    terrain: path_stone
    collision: empty      # optional; omit to leave base collision

era_overlays:             # era-specific diffs stamped on top of base Terrain
  father:
    - at: [col, row]      # point (no shape key = single cell)
      terrain: tall_grass
    - shape: rect         # or 'circle'
      at: [col, row]
      size: [w, h]
      terrain: wildflower_patch
  son:
    - shape: rect
      at: [col, row]
      size: [w, h]
      terrain: crystal     # biome must allow 'crystal' (dungeon)

entities:
  - type: Character       # matches LDtk entity-def identifier
    vault_ref: torbin     # slug (basename without .md) of a vault entity
    at: [col, row]
    era: Both             # 'Father', 'Son', 'Both'
```

### Operation order

1. `base` fills the whole grid with a uniform collision + terrain.
2. `raw` (if present) overwrites whole layers with pre-computed arrays.
3. `regions` stamp on top of base in declaration order.
4. `paths` stamp on top of regions in declaration order.
5. `Terrain_Father` starts as a copy of Terrain, then `era_overlays.father`
   stamps its diffs. Same for `Terrain_Son` with `era_overlays.son`.
6. `entities` emit LDtk entity instances into the Entities layer.

### Terrain symbol vocabulary

Defined in [scripts/ldtk_vocabulary.py](../../../scripts/ldtk_vocabulary.py).
Universal symbols (0-9) are valid in every biome. Biome-specific symbols
(10-19 field, 20-29 dungeon, 30-39 town) are rejected with a clear error
when used in the wrong zone biome.

**Universal** (always valid): `void`, `ground`, `wall`, `water_shallow`,
`water_deep`, `pit`, `door`, `stairs_up`, `stairs_down`, `bridge`

**Field** (`biome: field`): `tall_grass`, `bush`, `tree_trunk`,
`fallen_log`, `cliff_edge`, `path_dirt`, `path_stone`, `stream_crossing`,
`undergrowth`, `hollow`

**Dungeon** (`biome: dungeon`): `cave_floor`, `cave_wall`, `lava`,
`mine_track`, `cracked_floor`, `ore_vein`, `rubble`, `crystal`,
`ice_floor`, `dark_zone`

**Town** (`biome: town`): `cobblestone`, `fence`, `garden`,
`market_stall`, `well_fountain`, `building_wall`, `interior_floor`,
`counter`, `furniture`, `signpost_lamp`

### Collision symbols

- `empty` (0): walkable
- `solid` (1): blocks movement
- `water` (2): blocks movement (may become swimmable in future)
- `pit` (3): blocks movement (hazard)

### Reference implementation

[vault/world/zones/whispering-woods-edge.md](../zones/whispering-woods-edge.md)
has the first real Layout Spec — currently using the `raw:` escape hatch
to preserve the original hand-authored tile pattern byte-for-byte.
Future zones should prefer the higher-level `regions` / `paths` / `era_overlays`
primitives for reviewability.
