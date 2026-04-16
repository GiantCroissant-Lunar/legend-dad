---
type: zone
status: draft
articy-id: ""
tags: [town, vanguard, hub, military]
connections:
  - "[[Ashenford]]"
  - "[[Ashenford Refugee Camp]]"
  - "[[Ashenford Canyon Mouth]]"
  - "[[Rhen Halloway]]"
  - "[[Quartermaster Berin]]"
  - "[[The Vanguard's Debt]]"
  - "[[The Missing Patrol]]"
parent-location: "[[Ashenford]]"
zone-type: town
biome: town
floor: 0
grid-width: 22
grid-height: 16
era: "Both"
encounter_rate: 0
last-agent-pass: "2026-04-16"
---

# Ashenford Garrison Square

## Overview

The central parade ground of Ashenford, flanked by the barracks, the Command Hall, the armory, and the Depot warehouse. In Kaelen's era this is the functional heart of a cooperative Vanguard garrison; in Aric's era it has been expanded into a closed military staging yard with timber palisade walls added on three sides and civilians no longer permitted to linger. The zone serves as the hub for quest interactions with Captain Rhen Halloway (father's era) and Quartermaster Berin (both eras), and it is where the Traveler's Hearth inn faces for the father's era.

## Layout & Terrain

Rectangular zone (22x16 tiles). Open flagstone parade ground at center (roughly 10x8 tiles) with a raised dais at the west edge where officers address drills. Command Hall on the north side (5x4, impassable except at the central door); Depot warehouse on the east (6x4, impassable except at the sliding loading door); barracks block on the south (7x3 with two doors); armory on the west flanking the dais (4x3). The Traveler's Hearth inn facade sits outside the parade ground proper, on the south side of the barracks block, accessible via a narrow lane. In the son's era, the south lane to the Traveler's Hearth is closed by timber palisade with a heavy gate. Exits: south (to Ashenford Refugee Camp or to Traveler's Hearth in father's era), north (to Ashenford Canyon Mouth via the main road).

## Entities & Encounters

**Father's era:**
- Captain Rhen Halloway in the Command Hall (transition to interior)
- Quartermaster Berin at the Depot's loading door (exterior, dialogue + shop interface)
- 2 soldiers drilling on the parade ground (ambient, animated sword-form sprites)
- 1 sergeant at the dais (ambient calling cadence)
- 1 farrier at the armory's side forge (animated hammer-strike sprite)
- Notice board on the north side with militia postings (interactable, lore)

**Son's era:**
- Rhen Halloway not here (retired; he is at his small stone house at the camp's edge — see Ashenford Refugee Camp)
- Berin same position, same dialogue framework, grimmer
- 3-4 soldiers on the parade ground (now in newer gray kit rather than old cooperative red-and-steel)
- Dais empty
- Farrier absent; forge cold
- Notice board replaced with Vanguard posters (restricted zone warnings)
- Timber palisade walls visible on three edges of the zone (non-interactable, impassable)

## Era Variants

**Father → Son changes:**
- Parade ground flagstone: clean, swept → scuffed, trampled-mud patches at the palisade edges
- Banners at the Command Hall: red-and-steel cooperative sigil → colder gray-on-gray Vanguard sigil
- Notice board: open wooden frame with layered posting papers (trade, militia, community) → iron-banded frame with restricted-zone decrees printed in uniform type
- Command Hall door: carved timber, oiled, open during business hours → reinforced iron-banded, closed, a sentry at the step
- Depot loading door: open to civilian trade in posted hours → open by Vanguard schedule only; Berin's window shutter is the civilian-interface now
- Barracks windows: shuttered open, lamp-lit at dusk → shuttered closed, lamp-lit from behind gray-painted glass
- Traveler's Hearth access: open via south lane → closed, palisade gate across the lane
- Farrier's forge: lit, active, hammer sounds → cold, tools racked and locked

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: gray ashlar stone building walls with dark iron fittings (Command Hall, armory, barracks), timber-frame barracks variant for upper-story implied walls, stone-and-iron Depot warehouse with sliding loading door (the door is a 2-tile-wide sprite, closed and open variants), flagstone parade ground tiles (gray, subtly worn in wear-pattern from drill lines), dais tile (raised stone step, 2x1), wooden notice board prop tile, forge tile (open-sided wall with glowing coals in father's era, cold dark coals in son's), Vanguard banner sprite (hanging from iron brackets at regular intervals along building faces — old cooperative sigil in father's era, new gray sigil in son's). Son's era additions: timber palisade wall tiles (rough vertical logs, 2-tile implied height, impassable), palisade gate tile (heavy double-door, closed in most states), decree-poster wall tiles (replacing the open notice board), graffito-overlay tile for the old cooperative banners (a single tile where the old sigil was scrubbed off the stonework).

### ambience

Father's era: staggered marching boots on flagstone (a squad drilling distantly), rhythmic farrier hammer-ring, horses snorting from the stable block (implied east beyond the depot), sergeant calling cadence, cartwheels over cobblestone, wood being stacked near the depot, occasional greeting between soldiers and civilians. Canyon wind funneling in from the north. Son's era: drill cadence still present but fewer voices, civilian sounds absent from the central streets, the farrier's hammer absent (replaced by the distant clang of the checkpoint gate opening and closing at unpredictable intervals, which the refugees flinch at but which echoes into this zone from the north). Canyon wind unchanged — it was always loudest here.

### music

Shares the Ashenford location theme. Father's era: the snare-and-tenor-horn march in E minor plays at full presence in this zone — parade tempo, 120 bpm, the fife carries a hummable middle passage that brings the military scaffolding down to human scale. Son's era: same march cadence but stripped of the fife, brass line transposed a minor third down and played with a heavier attack, snare slightly behind the beat suggesting institutional fatigue. Beneath the march, the refugee-camp fiddle melody (from Ashenford Refugee Camp) bleeds in at very low volume if the player stands near the palisade south edge — the two musics never sync.
