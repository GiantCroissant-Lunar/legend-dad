---
type: biome
status: draft
tags: [cave, mine, underground]
intgrid-range: [20, 29]
tile-count-target: 64-128
palette: "damage-dice-10-6"
palette-url: "https://lospec.com/palette-list/damage-dice-10-6"
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

**Damage Dice 10 & 6** by Richmond Riddle — https://lospec.com/palette-list/damage-dice-10-6

10-color cool ramp from near-black (#00000d) through slate blues/teals (#3e4e59, #468c8b) to cool highlights — stone walls, iron veins, crystal glints. 6-color warm complement (#5e3d17 through #eddf48) for torch/lantern orange, rust/iron brown, gold ore deposits.

Depth progression: upper mines favor the warm 6-color set (torchlit); deep caverns use the cool 10-color set (crystal light, darkness).

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
