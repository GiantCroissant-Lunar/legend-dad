---
type: zone
status: draft
articy-id: "72057594037930395"
tags: [town, coastal, residential, shops]
connections:
  - "[[Saltmere Port]]"
  - "[[Saltmere Harbor Docks]]"
  - "[[Cael Vire]]"
parent-location: "[[Saltmere Port]]"
zone-type: town
biome: town
floor: 0
grid-width: 20
grid-height: 16
era: "Both"
encounter_rate: 0
last-agent-pass: "2026-04-16"
---

# Saltmere Merchant Quarter

## Overview

The uphill residential and trade quarter of Saltmere Port, behind the waterfront warehouses. Three-story stone townhouses with iron balconies line narrow flagstone lanes climbing from the harbor to a small market plaza at the hill's crest. In Kaelen's era, the quarter holds the port's wealthier traders and the guild council house. In Aric's era, half the townhouses are shuttered and the guild council no longer meets.

## Layout & Terrain

Medium zone (20x16 tiles) sloping west-to-east, with the harbor implied downslope to the east. Main feature: a rising switchback lane of flagstone that zigzags from the east edge up to the Market Plaza near the west edge. Stone townhouse blocks line both sides of the lane (2x3 each, impassable except at doors). The Market Plaza at the west edge is a small open space (5x5 tiles) with a central stone water-fountain (1x1 impassable) and two permanent trade stalls at its north and south sides. The Guild Council House is a larger 4x4 structure on the south side of the plaza with a carved wooden double-door facing north. Exits: east (to Saltmere Harbor Docks).

## Entities & Encounters

**Father's era:**
- 2 wealthier-trader NPCs (ambient on the plaza)
- 1 guild clerk at the Council House door (dialogue: guild postings, legitimate trade routes)
- 2 market stall vendors in the plaza (one cloth, one salt — shop interactions)
- 1 child NPC near the fountain (ambient)
- Ambient lantern-lighter NPC at dusk (ambient walk cycle)

**Son's era:**
- 1 trader NPC (pessimistic, mostly retired)
- Guild Council House door is sealed — a weathered notice nailed to it
- 1 remaining stall on the plaza (limited stock)
- No children
- Fountain basin cracked but still holds water

## Era Variants

**Father → Son changes:**
- Townhouse shutters: most open in father's era → two-thirds closed and latched in son's
- Balcony plantings: potted herbs and flowers → empty clay pots, some broken
- Flagstone lanes: swept clean → weeds between stones, salt-rime at the edges
- Guild Council House double-door: oiled timber with polished brass → weathered, brass tarnished black, chains through the handles
- Market Plaza stalls: four active → one active, three dismantled (blank wooden plinths)
- Water fountain: clean stream from a carved fish-spout → cracked spout, water trickles rather than arcs
- Lantern-lighter walks at dusk → lanterns unlit, poles remain

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: pale limestone townhouse walls (3-tile implied height), iron balcony props at upper-story windows, flagstone lane tiles (gray, slight slope shading), Market Plaza flagstone variant (lighter, worn smoother by foot traffic), stone fountain tile (circular basin, carved fish-spout centerpiece), trade stall tiles (wooden frame with colored awning — blue and ochre in father's era), Guild Council House facade (carved lintel, brass fittings, double-door sprite). Son's era additions: shuttered-townhouse variant (gray-brown weathered wood across windows), empty clay pots on balcony tiles, weed-gapped flagstone variants, chained Council House door sprite with a faded paper notice, dismantled stall plinth tiles, cracked fountain-spout variant. The quarter should feel like a neighborhood of faded comfort — never squalid, always a step below its original dignity in the son's era.

### ambience

Father's era: quieter than the Harbor Docks by design — flagstone footsteps at low traffic, a vendor calling from the plaza, a child's laugh near the fountain, fountain water arc-splash, distant harbor sounds filtered over the warehouse roofs. A cat meowing from a balcony. Occasional conversation between townhouse windows. Wind is lighter here, sheltered by the buildings. Son's era: flagstone footsteps alone for long stretches, the fountain's reduced trickle, wind now audible as it channels between the shuttered townhouses. One distant voice from the remaining stall. A single cat, still on one of the balconies. The harbor sounds reach through less because there are fewer of them to begin with.

### music

Shares the Saltmere Port theme but at reduced presence. Father's era: the concertina melody from the Harbor Docks fades as the player ascends the lane, replaced by a solo pennywhistle playing the same melody at half volume — a quieter variation on the shared port song, suggesting a neighborhood that hums the tune rather than sings it. Son's era: the pennywhistle is gone. A single sustained low note on a bowed bass holds for the duration of the zone's music, punctuated every eight bars by a very quiet solo concertina phrase from the Harbor theme — the theme briefly remembered, then dropped again.
