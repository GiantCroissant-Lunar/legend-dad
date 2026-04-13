---
type: meta
status: draft
last-agent-pass: "2026-04-13"
---

# Biome Conventions

## LDtk Architecture

- **World overview**: `project/ldtk/world-overview.ldtk` — locations as levels on the world map
- **One .ldtk per location**: e.g. `thornwall.ldtk`, `whispering-woods.ldtk`, `iron-peaks.ldtk`
- **Zones = levels** within a location's .ldtk file
- **Buildings are open-top / cutaway** — interiors visible on the same zone level, no screen transitions. Walls define rooms, doors are gaps in walls.

## Universal IntGrid Values (0-9)

Shared across all biomes. Every .ldtk file uses these.

| Value | Name | Walkable | Notes |
|---|---|---|---|
| 0 | void | no | Empty / out of bounds |
| 1 | ground | yes | Default walkable surface |
| 2 | wall | no | Generic solid impassable |
| 3 | water_shallow | yes | Slow movement, splash effect |
| 4 | water_deep | no | Impassable water |
| 5 | pit | no | Fall hazard / chasm |
| 6 | door | yes | Zone or map transition trigger |
| 7 | stairs_up | yes | Elevation change up |
| 8 | stairs_down | yes | Elevation change down |
| 9 | bridge | yes | Walkable over water or pit |

## Biome-Specific Ranges

| Range | Biome | File |
|---|---|---|
| 10-19 | Field | `field.md` |
| 20-29 | Dungeon | `dungeon.md` |
| 30-39 | Town | `town.md` (includes building interiors — open-top style) |
| 40-49 | *Reserved* | Future biomes |
| 50-59 | *Reserved* | Future biomes |

Town biome covers both outdoor areas and building interiors on the same map. Buildings are open-top (no roof) — the player sees rooms directly. Walls (35) define building boundaries, interior_floor (36) marks indoor space.

## Tile Specifications

- **Size**: 16x16 pixels
- **Style**: 16-bit JRPG, top-down 3/4 perspective
- **Target per biome**: 64-128 tiles (minimal viable tileset)
- **Palette source**: https://lospec.com/ — one palette per location, recorded in location frontmatter
- **Era variants**: Father's era (vibrant) and Son's era (muted) achieved via palette swap where possible, dedicated tile variants where needed (e.g. boarded-up stalls)

## Pipeline

1. Biome defs in vault define IntGrid values and tile categories
2. Location frontmatter references a lospec palette
3. LDtk sync script reads biome defs to configure IntGrid values per .ldtk file
4. ComfyUI reads biome tile categories + palette to generate tileset PNGs
5. Generated tilesets are imported into LDtk as auto-tile sources
6. Auto-rules map IntGrid values to themed tiles
