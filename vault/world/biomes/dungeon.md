---
type: biome
status: draft
tags: [cave, mine, underground]
intgrid-range: [20, 29]
tile-count-target: 64-128
palette: ""
palette-source: "https://lospec.com/"
locations:
  - "[[Iron Peaks]]"
last-agent-pass: "2026-04-13"
---

# Dungeon

Covers underground and cave zones: mine tunnels, natural caverns, sealed chambers. Used by Iron Peaks (trail and upper mines) and any future dungeon interiors.

## IntGrid Values

Universal values 0-9 apply (see `vault/world/biomes/_conventions.md`).

| Value | Name | Walkable | Notes |
|---|---|---|---|
| 20 | cave_floor | yes | Natural stone ground |
| 21 | cave_wall | no | Natural rock wall |
| 22 | lava | no | Damage hazard, glow effect |
| 23 | mine_track | yes | Rail track, cart movement possible |
| 24 | cracked_floor | yes | Breakable, may collapse on event |
| 25 | ore_vein | no | Mineable resource node |
| 26 | rubble | no | Clearable after event/ability |
| 27 | crystal | no | Light-emitting obstacle |
| 28 | ice_floor | yes | Sliding movement mechanic |
| 29 | dark_zone | yes | Requires light source, fog of war |

## Tile Categories

Target: 64-128 tiles at 16x16, 16-bit JRPG style, top-down 3/4 view.

- **Ground**: cave floor (3-4 variants), mine floor (planks, gravel), ice, cracked stone
- **Walls**: cave wall (natural edges, auto-tile 47-piece or blob), reinforced mine wall, crystal wall
- **Features**: ore veins (iron, crystal, dark), mine track (straight, curve, switch), mine cart
- **Hazards**: lava pool, lava flow edges, pit edges, cracked ground, rubble pile
- **Lighting**: crystal clusters (glow source), torch bracket, dark overlay tiles
- **Transitions**: cave-to-mine, stone-to-ice, lit-to-dark

## Palette

> **TODO**: Select a palette from https://lospec.com/ for underground/cave.
> Candidates should support: dark stone grays, warm torch/lava oranges, cool crystal blues, iron metallics.
> Consider depth progression: upper mines = warmer (torch light); deep caverns = cooler (crystal light, darkness).

## ComfyUI Prompt Template

```
16-bit pixel art tileset, top-down 3/4 perspective, 16x16 tile grid.
Underground cave/mine biome. {palette_name} color palette from lospec.
Tiles needed: {tile_category}.
Style reference: Final Fantasy VI mines, Chrono Trigger underground.
Clean tile edges for seamless tiling. No anti-aliasing. Transparent background where applicable.
Dark ambient lighting with localized light sources (torches, crystals, lava glow).
```

## Era Variants

- **Father's era**: Abandoned but stable mines — old equipment, dusty tracks, sealed passages
- **Son's era**: Fractured and active — new crevasses, dark energy leaking from sealed caverns, creatures emerging
