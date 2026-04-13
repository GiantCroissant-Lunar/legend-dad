---
type: biome
status: draft
tags: [town, village, settlement, interior]
intgrid-range: [30, 39]
tile-count-target: 96-128
palette: ""
palette-source: "https://lospec.com/"
locations:
  - "[[Thornwall]]"
last-agent-pass: "2026-04-13"
---

# Town

Covers settlement zones including building interiors. Buildings are shown open-top / cutaway — the player sees interior rooms directly on the same map without screen transitions. Walls define room boundaries, doors are gaps in walls.

Style reference: Eastward, CrossCode, top-down Zelda — buildings are part of the world map, interiors visible at all times.

Used by Thornwall (market, north gate, elder quarter) and any future settlements.

## IntGrid Values

Universal values 0-9 apply (see `vault/world/biomes/_conventions.md`).

### Outdoor (30-34)

| Value | Name | Walkable | Notes |
|---|---|---|---|
| 30 | cobblestone | yes | Town ground — roads, plazas |
| 31 | fence | no | Low barrier (wood, stone), see-through |
| 32 | garden | no | Decorative vegetation plot |
| 33 | market_stall | no | Commerce structure, interactive |
| 34 | well_fountain | no | Town landmark / centerpiece |

### Building structure (35-37)

| Value | Name | Walkable | Notes |
|---|---|---|---|
| 35 | building_wall | no | Exterior and interior walls (auto-tiled) |
| 36 | interior_floor | yes | Wood/stone floor inside buildings |
| 37 | counter | no | Shop counter, bar top — interactive from one side |

### Furniture & fixtures (38-39)

| Value | Name | Walkable | Notes |
|---|---|---|---|
| 38 | furniture | no | Tables, chairs, shelves, beds, chests, hearths |
| 39 | signpost_lamp | no | Readable signpost or light source |

### How buildings work

A building is a cluster of `building_wall` (35) tiles forming an enclosed room with `interior_floor` (36) inside. Doorways are simply gaps in the wall — the player walks through without any transition. The camera shows the interior at all times (no roof to hide).

```
Example: 6x4 herb shop in Thornwall Market

  35 35 35 35 35 35
  35 36 36 36 38 35     38 = furniture (shelf)
  35 36 37 37 36 35     37 = counter
  35 35    35 35 35     gap = door (walkable ground/cobblestone)
```

Larger buildings may have internal walls dividing rooms. Multi-story is represented by stairs (universal value 7/8) leading to a visually offset upper area on the same level.

## Tile Categories

Target: 96-128 tiles at 16x16, 16-bit JRPG style, top-down 3/4 view.

### Outdoor tiles
- **Ground**: cobblestone (3-4 variants), dirt road, grass patches, puddles
- **Structures**: fence (wood, stone), gate (open, closed), well, fountain, market stall frame
- **Decoration**: lamp post, signpost, barrel, crate, flower pot, bench, cart
- **Vegetation**: small tree, hedge, garden flowers

### Building tiles
- **Walls**: stone wall, wood wall (auto-tile set — edges, corners, T-junctions)
- **Floor**: wood planks (2-3 variants), stone floor, rug/carpet patterns
- **Furniture**: table (1x1, 2x1), chair (4 directions), bed, shelf, barrel, crate
- **Shop**: counter (horizontal, vertical, corner), display shelf
- **Fixtures**: fireplace, candle, window (in wall), weapon rack, bookshelf, chest

### Transitions
- Cobblestone-to-dirt, cobblestone-to-grass, road edges
- Outdoor ground to interior floor at doorways

## Palette

> **TODO**: Select a palette from https://lospec.com/ for medieval village.
> Candidates should support: warm stone/wood browns, cool slate wall tones, green vegetation accents, warm lantern/fireplace light for interiors.
> Consider era difference: father's era = warm, busy, colorful; son's era = muted, boarded-up, dim.

## ComfyUI Prompt Template

```
16-bit pixel art tileset, top-down 3/4 perspective, 16x16 tile grid.
Medieval village biome with open-top buildings (interiors visible, no roofs).
{palette_name} color palette from lospec.
Tiles needed: {tile_category}.
Style reference: Eastward towns, CrossCode villages, top-down Zelda interiors.
Clean tile edges for seamless tiling. No anti-aliasing. Transparent background where applicable.
Warm ambient lighting. Building interiors lit by fireplace/candle glow.
```

## Era Variants

- **Father's era**: Thriving village — colorful awnings, goods on display, lit lanterns, full shelves, maintained gardens
- **Son's era**: Declining village — boarded stalls, cracked cobblestone, overgrown gardens, empty shelves, dim/broken lamps
