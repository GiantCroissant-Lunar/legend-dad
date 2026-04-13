---
type: zone
status: draft
articy-id: ""
tags: [dungeon, mine, underground]
connections:
  - "[[Iron Peaks]]"
  - "[[Iron Peaks Trail]]"
  - "[[Iron Peaks Sealed Cavern]]"
parent-location: "[[Iron Peaks]]"
zone-type: dungeon
biome: dungeon
floor: 1
grid-width: 24
grid-height: 20
era: "Both"
last-agent-pass: "2026-04-13"
---

# Iron Peaks Upper Mines

## Overview

The first dungeon floor — abandoned mine tunnels carved into the Iron Peaks generations ago. Narrow passages, support timbers, rusted rail tracks, and collapsed sections create a maze-like environment. The player navigates through to reach the deeper levels and eventually the Sealed Cavern. In the father's era, the mines are abandoned but structurally sound. In the son's era, crystal growth has invaded the tunnels, creatures have nested, and some passages have collapsed while new ones have opened.

## Layout & Terrain

Medium-large zone (24x20 tiles). Network of interconnected tunnels radiating from a central hub (the old mineshaft elevator room, 4x4 tiles, non-functional). Four main tunnel branches: north (to Sealed Cavern entrance — blocked in father's era), east (dead end with loot), south (entrance from the Trail), west (collapsed in father's era, opened by crystal growth in son's era — alternate path). Tunnels are 2-3 tiles wide. Rail tracks run along the main passages. Support timbers at regular intervals. The hub has a higher ceiling (visually lighter). Dead-end alcoves contain old mining equipment and potential loot. Walkable: tunnel floors, rail tracks. Impassable: rock walls, collapsed rubble, intact support pillars.

## Entities & Encounters

**Father's era:**
- Bats (passive, ambient — scatter when approached)
- 1-2 cave spider encounters (basic dungeon enemies)
- Mining equipment interactions (pickaxe — key item, lantern — light source)
- Lore note on wall (miner's warning about the deep tunnels)

**Son's era:**
- Crystal-mutated creatures (cave spiders evolved, more aggressive)
- Crystal growth nodes (interactable — can be broken for resources or examined with Starweaver Lens)
- 1 mini-boss encounter in the west branch (new area opened by crystal growth)
- Environmental hazard: unstable floor sections (shake visual, damage if lingered)

## Era Variants

**Father → Son changes:**
- Tunnel walls: rough stone → stone with crystal veins (violet lines in rock tiles)
- Rail tracks: rusted but intact → some sections buckled by crystal growth pushing from below
- Support timbers: weathered wood → some cracked/broken, crystal growing through gaps
- Hub room: empty, dusty → crystal growth cluster at center (large, ambient light source)
- North passage (to Sealed Cavern): solid brick wall → bricks cracked, violet light leaking through
- West passage: fully collapsed rubble → rubble cleared by crystal growth, new passage opened
- Air: dusty, stale → faint crystal haze, particles visible in light
- Temperature: cool → warm (the crystal generates heat)

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: mine tunnel floor (dark gray stone with gravel texture), mine wall tiles (rough-hewn rock, darker than floor), support timber tiles (brown vertical beams at tunnel edges), rail track tiles (two parallel rust-brown lines on floor), collapsed rubble tiles (mixed rock and timber, impassable), hub room floor (smoother stone, lighter — the worked center of the mine), mining equipment tiles (pickaxe against wall, lantern on hook, barrel, crate), minecart tile (on rails, can be pushed?), elevator shaft tile (dark square with wooden frame, non-functional). Son's era additions: crystal vein wall tiles (stone with glowing violet lines — the crystal is growing through the rock), crystal cluster tiles (larger formations, 1x1 and 2x2, emit pale violet light), crystal-cracked timber tiles (wood split by crystal growth), buckled rail tiles (bent upward by force from below), unstable floor tiles (subtle crack pattern, slightly different color — visual warning), crystal haze overlay (semi-transparent violet tint on affected areas). Lighting: father's era uses warm orange (torch/lantern), son's era mixes orange torchlight with violet crystal glow — the two light sources competing.

### ambience

Father's era: underground echo chamber acoustics. Dripping water (irregular, echoing), footsteps on stone (sharp reverb), bat wing flutters (sudden, startling), wind draft through tunnels (low moan), timber creaking under rock pressure, distant rock settling, minecart wheels on rails (if pushed), lantern flame hiss. The mine should sound hollow and abandoned — every sound echoes. Son's era: same base acoustics but warmer (crystal heat changes the air). Crystal resonance hum (constant, varies by location — louder near clusters), creature skittering (fast, in walls), unstable floor rumble (warning sound before damage), crystal breaking (sharp, glass-like when nodes are destroyed), a deep pulse from below (the Sealed Cavern, rhythmic, like a heartbeat). The crystal hum should become the new normal — silence is when it stops, and that's scarier.

### music

Father's era: minimal — mostly ambient with occasional musical stings. A low, sustained cello note as base drone. Sparse pizzicato strings when exploring (plucked notes, irregular rhythm, suggesting careful steps in the dark). Combat encounters: the drone intensifies, percussion enters. The music should feel like the mine is breathing — slow, patient, not hostile but not safe. Loop: 180 seconds with long quiet sections. Son's era: the cello drone is replaced by a synthesized crystal tone (same pitch, different timbre — organic replaced by mineral). Pizzicato strings are joined by crystal percussion (tuned chimes struck with mallets). The rhythm is slightly faster — the mine is more active, more alive. Near the Sealed Cavern entrance: all other music fades, replaced by a deep, throbbing bass note and the crystal hum at its loudest. Loop: 180 seconds.
