---
type: zone
status: draft
articy-id: "72057594037929733"
tags: [town, gate, transition]
connections:
  - "[[Thornwall]]"
  - "[[Thornwall Market]]"
  - "[[Whispering Woods Edge]]"
parent-location: "[[Thornwall]]"
zone-type: town
biome: town
floor: 0
grid-width: 16
grid-height: 12
era: "Both"
encounter_rate: 0
last-agent-pass: "2026-04-16"
---

# Thornwall North Gate

## Overview

The fortified northern entrance to Thornwall, where the thornbriar wall is thickest and a wooden gate controls passage to the Whispering Woods and the road toward the Iron Peaks. A militia guardhouse flanks the gate. This zone serves as a transition between the safe town and the dangerous wilderness. In the father's era, the gate is well-maintained and guarded. In the son's era, the thornbriar has gaps, the gate hangs crooked, and the guardhouse is understaffed.

## Layout & Terrain

Narrow zone (16x12 tiles) oriented north-south. The thornbriar wall runs east-west across the middle of the zone, with the gate opening at center (2 tiles wide). The guardhouse is a small building (3x2) on the west side of the gate. A dirt path runs north-south through the gate — south leads to the Market, north leads out to the Whispering Woods Edge. The thornbriar wall tiles are impassable except at the gate. East and west edges are dense thornbriar (impassable). A small weapons rack and training dummy sit outside the guardhouse (interactable in father's era).

## Entities & Encounters

**Father's era:**
- 2 militia guards (one at gate, one patrolling)
- Training dummy (interactable — tutorial combat hint)
- Weapons rack (interactable — basic equipment)

**Son's era:**
- 1 militia guard (tired, warns about forest creatures)
- Collapsed training dummy (non-interactive flavor)
- Empty weapons rack

## Era Variants

**Father → Son changes:**
- Thornbriar wall: dense, green, flowering → patchy, dead sections (gray tiles), gaps visible
- Gate: solid wood, oiled hinges → warped wood, hanging slightly open
- Guardhouse: lit windows, maintained → dim, peeling paint
- Training area: active dummy + full rack → fallen dummy + empty rack
- Ground: packed dirt path → same dirt but with weeds and cracks near the wall gaps

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: thornbriar wall tiles (dense green hedge, 1 tile high, with flower accents for father's era), dead thornbriar variant (gray-brown, gaps showing background through), wooden gate tiles (vertical planks, iron hinges — open and closed states), guardhouse tiles (stone base, wood upper, small window), dirt path tiles (packed brown earth), training dummy tile (wooden cross-frame with straw), weapons rack tile (wooden frame with sword/shield silhouettes). The thornbriar should look impenetrable — dark green with thorns visible at pixel level. Father's era: thornbriar has tiny white flower pixels scattered on top. Son's era: same structure but desaturated with brown-gray dead patches, some tiles have visible gaps (1-tile holes showing the ground behind).

### ambience

Father's era: thornbriar rustling in wind (constant, leafy), gate creaking on hinges when opened, militia guard footsteps on dirt, training dummy being struck (wooden thwack), distant market sounds from the south, birdsong from beyond the wall. Son's era: wind through thornbriar gaps (higher pitch, whistling), gate groaning (it never fully closes), a single guard's footsteps, creature sounds from beyond the wall (distant, indistinct — could be animal, could be worse), no market sounds from the south.

### music

Shares the Thornwall theme but at lower volume, transitioning. Father's era: the Market folk melody fading as you move north, replaced by a single sustained note on a low flute — the edge of safety. Son's era: near-silence with a quiet, repeating two-note motif on plucked strings (tension, watchfulness). When facing north toward the gate exit, a faint preview of the Whispering Woods theme bleeds in.
