---
type: zone
status: draft
articy-id: ""
tags: [coastal, overworld, encounter, wilderness]
connections:
  - "[[Saltmere Port]]"
  - "[[Saltmere Harbor Docks]]"
  - "[[Iron in the Tide]]"
  - "[[Smuggler's Cove]]"
parent-location: "[[Saltmere Port]]"
zone-type: overworld
biome: field
floor: 0
grid-width: 28
grid-height: 20
era: "Both"
encounter_table:
  - bestiary: "[[Iron Borer]]"
    weight: 3
    era: "son"
  - bestiary: "[[Shade Wisp]]"
    weight: 2
    era: "son"
encounter_rate: 0.10
difficulty_tier: 3
last-agent-pass: "2026-04-16"
---

# Saltmere Chalk Estuary

## Overview

The broad reed-fringed estuary south of Saltmere Harbor, where the chalk river empties into the Moonlit Sea. Walkable shingle beach, reed beds, and a derelict tide mill define the zone. This is the outdoor encounter zone of Saltmere Port and the setting for the dive scene in "Iron in the Tide." In the father's era it is lightly populated with working salt-mill hands and fishing boats in the deeper channel; in the son's era, it is empty except for crystal-borne creatures that have started to come up out of the corrupted seabed.

## Layout & Terrain

Large coastal zone (28x20 tiles). The sea occupies the eastern third (walkable dock path along the north edge leading to where "Smuggler's Cove" starts off-map south; shallows tiles elsewhere, swimmable only in scripted dive scenes). The chalk river meanders across the zone's middle from the west edge to the sea, with reed beds on both banks (4-tile-wide strips, partially impassable in father's era and fully impassable in son's era where the reeds are dead and stiff). The Tide Mill is a 4x4 derelict structure on the north bank of the river, about two-thirds of the way east, with an interior entrance (not covered here). Shingle beach tiles ring the southeastern corner of the zone. A coast road runs along the north edge of the zone from the west (toward Saltmere Harbor Docks) to the east-southeast (toward the hidden cove off-map). Exits: north (to Saltmere Harbor Docks via the coast road), off-map south-east scripted exit to Smuggler's Cove scene.

## Entities & Encounters

**Father's era:**
- 2 salt-mill workers at the Tide Mill (ambient, dialogue about tide schedule)
- 1 fishing boat offshore (scripted appearance only; Kaelen boards it during "Iron in the Tide")
- Medicinal kelp pickups on the shingle beach (3-4 spots)
- 1 seagull flock (animated ambient)
- No combat encounters (encounter_rate bypass in father era)

**Son's era:**
- Tide Mill is abandoned (boarded door, no workers)
- Combat encounters per table: Iron Borer (small crystal-bored insectoid that has moved up out of the silted shallows), Shade Wisp (dusk-only ambient-hazard spawn)
- Pale mineral film overlay on the waterline tiles (visual, non-mechanical)
- One dead seabird on the shingle (environmental flavor — same encounter Aric and Maren pass in "Smuggler's Cove")
- 1 seagull (alone, wrong-pitched call)

## Era Variants

**Father → Son changes:**
- River water: clear turquoise → silver-gray silted outflow
- Reed beds: green and flowering, partial barrier → dead gray-stiff stubble, full barrier
- Tide Mill: operational with running wheel and smoke from the grinder roof → boarded, still wheel, no smoke
- Shingle beach tiles: pale clean pebble → pale pebble with mineral film crusting at the waterline
- Sea tile waterline: clean teal edge → pale violet tint near where the river outflow meets the sea
- Kelp pickups: 3-4 in father's era → 1-2, the rest replaced by "crystallized kelp" decorative tiles (non-usable)
- Seagull count: flock (6-8) → 1

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: shingle beach (pale gray-tan pebble texture, walkable), chalk-river water (clear turquoise in father's era, silver-gray in son's), reed bed tiles (green reeds in father's era with tiny white flowers, dead gray-brown stiff stubble in son's era), sea water tiles (teal-blue deep, lighter at shallows), coast road tile (packed earth with wheel-ruts), Tide Mill exterior (wooden 4x4 building with water-wheel on the river-facing side — animated spinning in father's era, stopped in son's), salt-drying rack tiles on the north bank (wooden frames with white salt granules in father's era, empty in son's). Son's era additions: mineral-film overlay at waterline (thin pale violet band along the edge where water meets shingle), crystallized-kelp tile (pale violet geometric overlay on the kelp-spot tile), dead-seabird prop tile (small sprite on the shingle), boarded-Tide-Mill door variant. Sky tiles overhead: low silver-gray with band of pink at the horizon for Smuggler's Cove dusk scene.

### ambience

Father's era: full coastal-estuary soundscape — small waves at the shingle (slow), reed rustle in the river-wind (the reeds have a specific dry-papery-green sound), distant gull flock calls, the Tide Mill's water-wheel splash-rhythm (steady, mechanical), salt-mill workers calling to each other, a small boat's rope creak. A low layered surf from the open sea beyond. Son's era: the reeds have a different sound — drier, sharper, more brittle. The waves slap differently against the mineral-filmed shingle. The Tide Mill is silent. A single gull, wrong-pitched. The surf beyond is the same. A new sound: a very faint subsonic pulse from the shallows where the river meets the sea, audible mostly as a feeling in the chest, that a player will come to recognize as the same pulse beneath Thornwall's well and beneath the Iron Peaks fissures.

### music

Father's era: the Saltmere Port concertina theme plays at reduced volume over a wash of sea-wind, with a solo tin whistle carrying the melodic line instead of the full ensemble — this is the port's song heard from outside the port. Son's era: the whistle is gone. A solo fiddle plays a variation on the concertina melody in the relative minor, with long silences between phrases. Underneath, the same subsonic pulse from the ambient layer briefly surfaces as a musical note — the corruption itself entering the scale. When combat triggers (encounter_table rolls), the fiddle drops out and a sharp plucked-string tension theme (from the shared combat track) rises.
