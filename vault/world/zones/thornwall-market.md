---
type: zone
status: draft
articy-id: "72057594037929773"
tags: [town, starting-area, commerce]
connections:
  - "[[Thornwall]]"
  - "[[Thornwall North Gate]]"
  - "[[Thornwall Elder Quarter]]"
parent-location: "[[Thornwall]]"
zone-type: town
biome: town
floor: 0
grid-width: 20
grid-height: 16
era: "Both"
encounter_rate: 0
last-agent-pass: "2026-04-16"
---

# Thornwall Market

## Overview

The central square of Thornwall — a cobblestone plaza surrounded by shops, the village well, and the militia notice board. This is the player's hub zone in both eras. In the father's era it bustles with traders, children, and militia guards. In the son's era the same square feels half-empty: stalls are boarded up, the well bucket is rusty, and the notice board is covered in warnings about creature sightings.

## Layout & Terrain

A roughly rectangular plaza (20x16 tiles). The well sits at the center (2x2 impassable). Cobblestone paths radiate from the well to four exits: north (to Thornwall North Gate), south (to the southern road), east (to the Elder Quarter), west (to the farmlands). Market stalls line the north and east edges — in father's era they have awnings and goods; in son's era half are boarded up. The militia barracks is a large building (4x3 tiles) on the west side. A small herb shop sits on the east side near the Elder Quarter exit. The ground is mostly walkable cobblestone with building tiles as impassable walls.

## Entities & Encounters

**Father's era:**
- 2-3 trader NPCs at market stalls (dialogue: local rumors, item shop)
- 1 militia guard at the north exit (dialogue: warns about mountain paths)
- 2 children playing near the well (ambient, non-interactive)
- Kaelen's starting position: near the militia barracks

**Son's era:**
- 1 remaining trader (limited inventory, pessimistic dialogue)
- 1 elderly militia guard (dialogue: stories about Kaelen, warnings about tremors)
- Maren (companion, found near the herb shop)
- Aric's starting position: near the well

## Era Variants

**Father → Son changes:**
- Market stalls: 6 active → 2 active, 4 boarded (tile swap)
- Well: clean stone rim → rusty bucket, cracked rim (tile swap)
- Militia barracks: full bunks, lit windows → half-empty, dim windows
- NPC count: ~6 → ~3
- Ground: clean cobblestone → some cracked tiles, weeds growing through gaps
- Notice board: trade postings → creature warning posters
- Ambient: lively crowd sounds → wind, occasional footstep

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles needed: cobblestone ground (2-3 variants for visual variety), cobblestone-cracked variant (son's era), building walls (brown wood with stone base), building interiors visible through doorways (dark with warm light), market stall tiles (wooden frame with colored awning — red, blue, green), boarded-up stall variant (gray wood, no awning), well tiles (circular stone rim, dark water center), militia barracks facade (larger stone building, iron-banded door), herb shop facade (wooden with hanging dried plants), notice board (wooden frame with paper rectangles). Era-specific palette: father's era warm (golden cobblestone, warm brown wood, colored awnings), son's era cool (gray-tinted cobblestone, weathered wood, muted colors). Transition tiles needed for exits: cobblestone-to-dirt (south, west), cobblestone-to-flagstone (east to Elder Quarter), cobblestone-to-gate (north).

### ambience

Father's era: cobblestone footsteps, crowd murmur (3-5 voices at medium distance), merchant calling prices, children laughing near well, metal clinking from militia training, cart wheels on stone, birdsong. A warm, populated soundscape at moderate volume. Son's era: cobblestone footsteps (slower), wind through empty stalls, a single merchant's half-hearted call, creaking wood from boarded stalls, well bucket chain rattling, distant crow caw, occasional low rumble from the mountains. Same spatial layout as father's era but with 60% of the sound layers removed — the silence is the atmosphere.

### music

Father's era: folk melody in G major — acoustic guitar and pennywhistle at moderate tempo. Bright, communal, the sound of a village at peace. Melodic hook is simple and memorable — players will hear this often. Loop length: 90 seconds. Son's era: same melody in G minor, solo acoustic guitar, half tempo. The pennywhistle is absent. A faint low drone on the last 4 bars suggests the distant tremors. Loop length: 90 seconds. The recognition of the same tune made sad is the emotional point.
