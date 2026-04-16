---
type: zone
status: draft
articy-id: ""
tags: [town, refugee, son-era, quest-hub]
connections:
  - "[[Ashenford]]"
  - "[[Ashenford Garrison Square]]"
  - "[[Rhen Halloway]]"
  - "[[The Missing Patrol]]"
  - "[[Vanguard Checkpoint]]"
parent-location: "[[Ashenford]]"
zone-type: town
biome: town
floor: 0
grid-width: 20
grid-height: 14
era: "Son"
encounter_rate: 0
last-agent-pass: "2026-04-16"
---

# Ashenford Refugee Camp

## Overview

A son-era-only zone at the southern edge of Ashenford, outside the old town gate, where displaced miners and their families have settled into a makeshift encampment while they wait for the Vanguard Checkpoint to reopen the road to the Iron Peaks. The camp has been here three years. It is not leaving. This zone hosts the opening of "The Missing Patrol," the encounter with Alva the midwife, and the discovery of retired Captain Rhen Halloway at his small stone house at the camp's eastern edge.

## Layout & Terrain

Medium zone (20x14 tiles). The Ashenford south town gate is the northern exit (centered, 2-tile-wide archway). South of the gate, the camp sprawls in an irregular pattern: a central communal cook-fire in a ring of river stones (2x2, impassable center, walkable around), patched canvas tents in clusters of three or four, guy-ropes staked into the ground (decorative overlays — tile is walkable but ropes are a visual boundary), stacked wagons on the west edge serving as wind-break. Rhen Halloway's small stone house sits on the eastern edge, two rooms and a small porch, recognizable as a pre-camp building. Alva's shelter is a larger canvas lean-to on the south edge, built against a low dry-stone wall that predates the camp. Exits: north (to Ashenford Garrison Square via the south town gate), off-map south (to coast road).

## Entities & Encounters

**Son's era only:**
- Alva the midwife at her lean-to (quest-giver for "The Missing Patrol")
- Rhen Halloway at his small stone house porch (reflective dialogue; will acknowledge Aric if he recognizes Kaelen's line first)
- 3-4 refugee NPCs at the cook-fire (ambient, dialogue about lost homes, the Vanguard, the sound of the checkpoint gate)
- 1 child sprite near Rhen's house (ambient, Rhen tolerates the child's presence)
- 2 refugee NPCs stacking firewood on the west side (ambient)
- 1 camp dog sprite (roams, non-interactive)

## Era Variants

This zone does not exist in the father's era. A small note in the Ashenford location page covers the space that the refugee camp occupies in the son's era: in the father's era, this ground is an open field south of the town gate used for militia practice and occasional market days, without permanent structures. No era-variant toggle in LDtk is required — the zone simply does not render in the father's timeline.

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: trampled-earth ground (packed brown with patches of weeds where the grass has been worn through), river-stone ring with central cook-fire (warm orange glow, thin smoke wisp sprite rising and dispersing), patched canvas tent tiles (2x2, tan canvas with visible stitched repairs, different colors per tent to suggest individual households — faded red, faded blue, faded green), guy-rope overlay tiles (thin brown lines staked at corners, decorative), stacked wagon tile on the west (collapsed to one wheel and a box, serves as wind-break — 2x1), Rhen's small stone house facade (gray stone, small wooden porch, a single window and a door, recognizably a pre-camp building), Alva's lean-to (tall canvas against low dry-stone wall, brown and gray palette, a small clay oven smoking on the wall side), camp dog sprite (animated idle and roam cycles), firewood stack tile on the west. A south town gate archway tile at the north exit — old cooperative stonework with a Vanguard sentry sprite optionally at the arch in son's era (the sentry will pass the player through without comment, but his presence is visual). Palette: muted browns, canvas-tans, stone-grays, with the cook-fire and Alva's oven as the only warm light sources.

### ambience

Low voices, a child being hushed, a wooden ladle in a clay pot, canvas flapping in the canyon wind (intermittent), a small fire popping at irregular intervals, a dog's quiet panting, occasional firewood-splitting thwack, the distant clang of the Vanguard Checkpoint gate from the north-northwest (audible through the Ashenford Garrison Square and into this zone at reduced volume, unpredictable cadence that the refugees flinch at). Rhen's porch has its own quieter acoustic pocket — the camp sounds reach him at half volume, as if the small stone house has its own sound-shelter built in.

### music

A solo acoustic guitar plays a tired, circular folk pattern in C minor — the same three chords repeating without resolution. A fiddle enters in the second pass with a counter-melody that is distinctly non-military in key and phrasing, and does not sync with the Ashenford Garrison march if the player can hear both musics at the zone boundary. Near Rhen Halloway's porch, the guitar thins to a solo and the fiddle drops out; the instrumentation there is just the guitar and, very faintly, the muted trumpet of Rhen's character theme held as a single sustained note. The piece does not build or resolve; it is the music of people who have been waiting for three years and have decided they will keep waiting.
