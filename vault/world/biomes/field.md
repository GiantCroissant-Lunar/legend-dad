---
type: biome
status: draft
tags: [overworld, forest, wilderness]
intgrid-range: [10, 19]
tile-count-target: 64-128
palette: ""
palette-source: "https://lospec.com/"
locations:
  - "[[Whispering Woods]]"
last-agent-pass: "2026-04-13"
---

# Field

Covers outdoor wilderness zones: forests, paths, clearings, riverbanks. Used by Whispering Woods (edge and deep) and any future overworld travel zones.

## IntGrid Values

Universal values 0-9 apply (see `vault/world/biomes/_conventions.md`).

| Value | Name | Walkable | Notes |
|---|---|---|---|
| 10 | tall_grass | yes | Random encounters, rustling visual |
| 11 | bush | no | Cuttable/clearable obstacle |
| 12 | tree_trunk | no | Large tree base (2x2 or 1x1) |
| 13 | fallen_log | no | Clearable after event |
| 14 | cliff_edge | no | Visual drop-off, impassable |
| 15 | path_dirt | yes | Distinct from grass ground |
| 16 | path_stone | yes | Maintained road / paved |
| 17 | stream_crossing | yes | Shallow ford, splash effect |
| 18 | undergrowth | yes | Slow movement, hides items |
| 19 | hollow | yes | Concave terrain, hide spot |

## Tile Categories

Target: 64-128 tiles at 16x16, 16-bit JRPG style, top-down 3/4 view.

- **Ground**: grass (3-4 variants), dirt path (straight, corner, T, cross), stone path (same set), mud
- **Water**: stream tiles (horizontal, vertical, corners), shallow ford, bank edges
- **Vegetation**: tree trunk, tree canopy (above-player layer), bush, tall grass, flowers, mushrooms
- **Terrain**: cliff face, cliff top edge, rock outcrop, fallen log
- **Transitions**: grass-to-dirt, grass-to-stone, forest-density edges

## Palette

> **TODO**: Select a palette from https://lospec.com/ that fits old-growth forest with seasonal variation.
> Candidates should support: rich greens, earth browns, cool shadow blues, warm highlight yellows.
> Consider era difference: father's era = vibrant greens; son's era = desaturated, dying tones (palette swap).

## ComfyUI Prompt Template

```
16-bit pixel art tileset, top-down 3/4 perspective, 16x16 tile grid.
Old-growth forest biome. {palette_name} color palette from lospec.
Tiles needed: {tile_category}.
Style reference: Chrono Trigger, Secret of Mana overworld.
Clean tile edges for seamless tiling. No anti-aliasing. Transparent background where applicable.
```

## Era Variants

- **Father's era**: Healthy forest — full canopy, green undergrowth, clear streams, wildflowers
- **Son's era**: Dying forest — bare branches, brown/gray undergrowth, murky water, sinkholes (palette swap + tile variants)
