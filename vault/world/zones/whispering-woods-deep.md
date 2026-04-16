---
type: zone
status: draft
articy-id: "72057594037929799"
tags: [forest, wilderness, danger]
connections:
  - "[[Whispering Woods]]"
  - "[[Whispering Woods Edge]]"
  - "[[Iron Peaks Trail]]"
parent-location: "[[Whispering Woods]]"
zone-type: overworld
biome: field
floor: 0
grid-width: 24
grid-height: 24
era: "Both"
encounter_table:
  - bestiary: "[[Moss Lurker]]"
    weight: 3
    era: "son"
  - bestiary: "[[Thornbriar Stalker]]"
    weight: 4
    era: "son"
  - bestiary: "[[Shade Wisp]]"
    weight: 2
    era: "son"
encounter_rate: 0.18
difficulty_tier: 3
last-agent-pass: "2026-04-16"
---

# Whispering Woods Deep

## Overview

The deep interior of the Whispering Woods, where ancient trees block most sunlight and the canopy trail provides the only safe path above the tangled undergrowth. The Moss Clearing — a natural depression where foresters camp — sits at the center. The path north exits toward the Iron Peaks Trail. This zone has denser encounters and more exploration than the Edge. The Ancient Stones (carved markers from a forgotten civilization) are found here, hinting at the buried structures beneath the forest.

## Layout & Terrain

Large zone (24x24 tiles). Dense tree coverage — only 40% of the ground is walkable. The canopy trail (elevated wooden walkway tiles) provides a safe route through the treetops in the northern half. The Moss Clearing is a 6x6 open area at the center with soft green moss tiles and a campfire ring. The Deep Root (the oldest tree, 3x3 tiles) is in the northwest corner. Ancient Stones are scattered as 1x1 interactable tiles at 4-5 locations among the roots. Paths are narrow and winding — no straight lines. A stream from the Edge zone continues through the southeast corner. Exit south: back to Edge. Exit north: to Iron Peaks Trail.

## Entities & Encounters

**Father's era:**
- 2-3 passive creatures (foxes, owls)
- 1-2 hostile creatures (wolves, territorial)
- Forester camp at Moss Clearing (rest point, campfire save)
- Ancient Stone interactions (examine → lore text, Starweaver Lens reveals hidden inscriptions)

**Son's era:**
- 3-4 hostile corrupted creatures (stronger than Edge encounters)
- Sinkhole at Moss Clearing center (where the campfire was)
- Canopy trail sections collapsed (requires alternate ground routes)
- Ancient Stones now glow faintly (the buried structures are activating)
- The Deep Root is stressed — sap weeping, bark cracked

## Era Variants

**Father → Son changes:**
- Moss Clearing: green moss, campfire ring → sinkhole at center, moss blackened at edges
- Canopy trail: intact wooden walkways → 2-3 sections collapsed (fallen plank tiles)
- Ancient Stones: inert, covered in moss → faint violet glow, moss burned away
- Deep Root: massive healthy trunk → cracked bark, sap pools, still alive but visibly damaged
- Tree density: unchanged, but many trees show stress (bark peeling, canopy thinning)
- Stream: clear → cloudy with a faint violet tint near sinkhole
- Ground: thick moss → patches of black fungal growth, crystal shards near sinkhole

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: dense forest floor (dark green moss, minimal light), massive tree trunks (3-4 tile wide ancient trees — these should feel enormous), canopy overlay (very dark green, heavy coverage, only path tiles are visible beneath), canopy trail tiles (wooden planks suspended between trees, lighter than ground level), Moss Clearing tiles (bright green moss, lighter than surrounding forest, clearly a break in the canopy), campfire ring tiles (stone circle with ash/embers), Deep Root tiles (enormous trunk with visible root system spreading 3x3, bark texture detailed at pixel level), Ancient Stone tiles (gray carved stone half-buried in roots, small — 1x1 with inscribed line details). Son's era additions: collapsed walkway tiles (broken planks hanging at angles), sinkhole tiles (dark void with crystal-violet edge glow), glowing Ancient Stone variant (same stone but with violet light pixels emanating), cracked Deep Root (sap drip pixels, bark gap patterns), black fungal moss (replacing green moss near corruption sources), crystal shard ground tiles (small violet geometric shapes on dark ground). The zone should feel claustrophobic — limited visibility, heavy canopy, narrow paths between massive trunks.

### ambience

Father's era: deep forest layered soundscape. The whispering canopy at full volume — a constant, almost conversational murmur. Owl hoots (night cycle), fox barks (distant), wolf howl (rare, far away), thick undergrowth rustling, heavy branch creaking from ancient trees, stream (muffled by distance and canopy), footsteps on moss (soft, damp), footsteps on wooden walkway (hollow clonk). At Moss Clearing: campfire crackle, the canopy rustle is quieter (opening in trees). Son's era: the whisper is louder and higher-pitched — urgent, warning. Crystal resonance hum near the sinkhole and glowing stones (a sustained, slightly pulsing tone). Corrupted creature sounds (guttural, wrong-sounding versions of normal animals). Collapsed walkway: wood groaning when walked near. Deep Root: a slow, deep creak like a ship hull under pressure. Sinkhole: a low draft sound, as if air is being pulled downward.

### music

Father's era: the Whispering Woods theme fully developed — dual recorders, lute, with added low drone from a bowed psaltery. Darker and more mysterious than the Edge variant. The melody moves in a minor key with modal inflections suggesting ancient, pre-human music. The forest sounds are heavily blended into the arrangement — the boundary between music and place dissolves. Loop: 150 seconds. Son's era: the recorder is gone. The psaltery drone dominates, with crystal-chime percussion (representing the corruption) replacing the rhythmic lute. A solo low flute plays fragments of the melody — not the full tune, just broken phrases, as if the forest itself is forgetting its song. Near the sinkhole: all melodic content drops out, leaving only the drone and crystal chimes. Loop: 150 seconds.
