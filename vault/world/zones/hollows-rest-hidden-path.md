---
type: zone
status: draft
articy-id: "72057594037930324"
tags: [overworld, forest, hidden-path, son-era, encounter]
connections:
  - "[[Hollow's Rest]]"
  - "[[Hollow's Rest Hearth Circle]]"
  - "[[Whispering Woods]]"
  - "[[Whispering Woods Deep]]"
  - "[[Maren]]"
  - "[[Roots of Exile]]"
  - "[[The Old Elder's Map]]"
parent-location: "[[Hollow's Rest]]"
zone-type: overworld
biome: field
floor: 0
grid-width: 24
grid-height: 22
era: "Son"
encounter_table:
  - bestiary: "[[Moss Lurker]]"
    weight: 3
    era: "son"
  - bestiary: "[[Thornbriar Stalker]]"
    weight: 2
    era: "son"
encounter_rate: 0.14
difficulty_tier: 6
last-agent-pass: "2026-04-16"
---

# Hollow's Rest Hidden Path

## Overview

The approach route to Hollow's Rest from the surrounding Whispering Woods — a path that is not quite a path, deliberately so. The zone covers a swampy low ground, a fallen-log bridge, a stream crossing at a place where footprints do not hold, and a final thicket before the tree-fall hollow. Only Maren can guide a first-time visitor through; subsequent traversals are possible but slower without her. This is the zone Aric and Maren walk in Act 1 of "Roots of Exile" and the route Scavenger Mott takes on his supply runs.

## Layout & Terrain

Medium-large zone (24x22 tiles). Topology from south to north: the southern third is swampy low ground with shallow standing water, reed hummocks, and clumps of dead-looking undergrowth that is in fact still-healthy forest holding its breath; the middle third is firmer ground with a fallen-log bridge (4 tiles long, 1 tile wide, walkable) crossing a wider stream; the northern third is a thicket of dense standing trees, with the final approach to the Hearth Circle gap visible at the north edge. The stream curves diagonally from the northeast to the southwest, cut through by the fallen-log bridge at the middle. A stone-hopping crossing exists at the zone's east side for Maren's shortcut route during Scavenger Mott's runs. Walkable: firm ground, the fallen log, stone-hops, the thicket's narrow gaps; impassable: standing water deeper than ankle height, reed hummocks, tree trunks, rooted undergrowth in the thicket. Exits: south (to a Whispering Woods boundary — leading off into the larger woods), north (through the thicket to Hollow's Rest Hearth Circle; gated by first-time-introduction flag).

## Entities & Encounters

**Son's era only:**
- No NPCs in the zone itself — this is the liminal approach route, not a living zone
- Combat encounters per table: Moss Lurker (swamp ambush in the southern third), Thornbriar Stalker (thicket-dwelling, in the northern third)
- Rare environmental event: a Hollow's Rest child-scout's bird-call whistle will signal the player's approach when they cross the stream — if the player does not have the woven signal-token tied to their wrist, the settlement hides and the northern gap becomes temporarily impassable (a narrative beat Maren explains in Act 1)
- Ambient wildlife: a healthy-forest owl-call (son's era, but from this uncorrupted pocket), a small deer sprite that flees when approached
- Optional: a hidden herb pickup on the east stone-hop route (deep-forest moss that Wren values; only spawns if the player has spoken with Wren in the Hearth Circle first)

## Era Variants

This zone does not exist in the father's era. In the father's era, the same geographic space is simply a part of the larger Whispering Woods Deep — walkable as normal forest, with different encounter tables per that zone's definition. No LDtk era-variant toggle is needed for this zone; the father's-era renderer falls through to Whispering Woods Deep tiles.

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: swampy ground tile (dark green-black with patches of standing water, occasional reed-hummock sprites, walkable only in specific patterns), shallow water tile (dark teal, semi-transparent, impassable deeper variants), reed hummock sprite (1x1 cluster, impassable), fallen-log bridge tile (4x1 strip of large mossy log with visible bark texture and a slight downward bow in the middle, walkable), stream water tile (clear-teal flowing water, animated), stone-hop stones in the stream (three small gray stones in a row, walkable with precise positioning), thicket tree tiles (dense standing trees, 1x1 with larger canopy overlay, impassable trunks but walkable between), underbrush tiles (shorter dark-green bushes, impassable), path-clue tiles (almost-invisible to the player: a small worn patch of moss where Maren's foot has rested before, a single trimmed twig, a bit of red fiber from Mott's cloak on a branch — easter-egg details that reward close inspection). The northern thicket should feel denser than anywhere else in the Whispering Woods, including the corruption zones — this is a healthy dense forest holding its own against the surrounding decay. Palette: rich greens, warm browns, the same inverse-of-Ashenford colors as the Hearth Circle but in the higher saturation of untouched woods.

### ambience

The Whispering Woods' canopy whisper is present at normal (pre-corruption) pitch — as at the Hearth Circle, this pocket has not been reached by the corruption, so the forest here sounds the way the woods sounded in the father's era. Shallow water lapping at the reed hummocks, the slow drip of condensed mist from leaves, a frog at irregular intervals in the southern third, a woodpecker far off, a healthy deer stepping through undergrowth, the particular dry-papery-creak of the fallen-log bridge under foot-weight, the small crystalline splash of the stream at the stone-hops. When Aric and Maren first walk this zone in "Roots of Exile," the soundscape is the same but foregrounded more carefully — the player's attention is meant to stay on the fact that this is a different kind of forest-sound than the corruption zones. Combat encounters layer the shared combat tension theme over this bed without removing the ambient layer entirely.

### music

Solo fiddle (Maren's theme) plays alone through the southern swamp — a cautious walking melody that matches the player's careful foot-placement across the uneven ground. At the fallen-log bridge, the fiddle pauses and a single wooden flute enters for the length of the crossing, its note held across four bars while the fiddle rests. At the stream stone-hop, both instruments drop out and only the stream's own sound carries the music. In the northern thicket, the mandolin of the Hollow's Rest location theme enters at very low volume from the north, suggesting the settlement is just ahead — the closer the player gets to the north exit, the clearer the mandolin becomes, until at the north edge the Hearth Circle's full theme takes over. This zone's music is the music of a journey ending — not arriving yet, but close.
