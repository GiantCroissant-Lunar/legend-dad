---
type: zone
status: draft
articy-id: "72057594037930270"
tags: [overworld, canyon, checkpoint, dungeon-pass]
connections:
  - "[[Ashenford]]"
  - "[[Ashenford Garrison Square]]"
  - "[[Iron Peaks]]"
  - "[[Iron Peaks Trail]]"
  - "[[The Vanguard's Debt]]"
  - "[[Vanguard Checkpoint]]"
  - "[[The Missing Patrol]]"
parent-location: "[[Ashenford]]"
zone-type: overworld
biome: dungeon
floor: 0
grid-width: 26
grid-height: 18
era: "Both"
encounter_table:
  - bestiary: "[[Crystal Crawler]]"
    weight: 2
    era: "son"
  - bestiary: "[[Shade Wisp]]"
    weight: 1
    era: "son"
encounter_rate: 0.08
difficulty_tier: 4
last-agent-pass: "2026-04-16"
---

# Ashenford Canyon Mouth

## Overview

The narrow canyon pass at the northern edge of Ashenford, where the road climbs from the lowland plain toward the Iron Peaks. In Kaelen's era this is a simple approach with two sentry posts flanking a small wooden gatehouse; traffic passes freely, the Vanguard logs names into a civilian passage book, and travelers continue. In Aric's era, the same canyon holds the full Vanguard Checkpoint — a timber-and-stone gatehouse with flanking watchtowers, iron-reinforced gates, a refugee encampment pressed up against the south entry, and patrols on the walls. The zone is the staging ground for most of the "Vanguard Checkpoint" quest and part of "The Missing Patrol."

## Layout & Terrain

Long narrow zone (26x18 tiles), oriented south-to-north, reflecting the canyon pass geometry. Southern half: the approach — the main road paved with worn flagstones running up the canyon floor (3 tiles wide), steep red-brown cliff walls on both east and west sides (impassable, implied height), scattered rocks and mineral-vein boulders as visual flavor. Middle: the gatehouse area — in father's era, two small 2x2 sentry posts flanking a 4x3 wooden gatehouse with a simple wooden bar across the road; in son's era, a full 8x5 timber-and-stone gatehouse with flanking 3x3 watchtowers and a heavy iron-reinforced gate across the road. A goat trail climbs from the southwest cliff base along a narrow ledge — this is the stealth-path option for "Vanguard Checkpoint" and is only walkable with Maren in the party. Northern half: beyond the gatehouse, the canyon widens slightly before exiting off-map north to Iron Peaks Trail. Exits: south (to Ashenford Garrison Square in father's era, directly into Ashenford Refugee Camp in son's era), north off-map (to Iron Peaks Trail).

## Entities & Encounters

**Father's era:**
- 2 sentry NPCs at the flanking posts (dialogue: passage log, directions)
- 1 junior officer in the gatehouse (dialogue: Rhen's passage instructions if Kaelen carries Rhen's written recommendation from "The Vanguard's Debt")
- Passage book on a small lectern outside the gatehouse (interactable, lore about who has traveled here recently)
- Minimal ambient patrol walking the flagstones
- No combat encounters in this zone in father's era (encounter_rate bypass)

**Son's era:**
- 4-6 Vanguard soldier NPCs on the walls and at the gate (non-interactable as individuals; interaction goes through Captain Voss at the gatehouse for "Vanguard Checkpoint" diplomacy path)
- Captain Voss at the gatehouse interior (scripted quest NPC, branching dialogue per "Vanguard Checkpoint" quest's three paths)
- Wounded Sentry on the south side of the gatehouse exterior (per "The Missing Patrol" — the same sentry visible in the Refugee Camp zone may appear here depending on quest state)
- Goat trail NPCs: none, but Maren will guide Aric along it as a scripted sequence if the stealth path is chosen
- Combat encounters per table for players who leave the road and enter the canyon's eastern slopes beyond the gatehouse (Crystal Crawler, Shade Wisp); rate low (0.08) — most traffic stays on the flagstone road

## Era Variants

**Father → Son changes:**
- Gatehouse: small 4x3 wooden structure with a simple bar-gate → full 8x5 timber-and-stone fortification with iron-reinforced double doors
- Sentry posts: two small 2x2 wooden posts → two full 3x3 stone watchtowers, each with a Vanguard banner and a visible sentry at the top
- Wooden bar across the road: ordinary, opens via lever → iron-reinforced gates, opens via chain-windlass from inside the gatehouse (audible as the clang the refugees flinch at)
- Passage book lectern: present, interactable → gone (replaced by a Vanguard decree posted on the gatehouse wall)
- Goat trail: present as environmental detail only → visible and walkable if Maren is in the party
- Cliff-wall mineral veins: rust-and-gold streaks, natural → streaks interrupted in places by faint violet crystal threads that have started to climb out of the rock (very subtle — the corruption is reaching the surface here)
- Refugees outside the gate: none → camp visible through the south exit into Ashenford Refugee Camp
- Road flagstones: clean, swept → trampled-mud patches at the gatehouse approach where refugee traffic and Vanguard inspection lines have worn the stone

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: red-brown cliff wall tiles (implied vertical height, impassable, with visible rust-orange mineral streaks), flagstone road tiles (gray, worn, 3 tiles wide in a strip down the canyon), canyon-floor rock tiles (reddish-brown gravel texture, walkable, slightly uneven), scattered boulder sprites, goat trail tile (narrow ledge, 1 tile wide, cliff-hugging), gatehouse structure tiles (timber-and-stone building faces in both scales — the father's-era smaller variant and the son's-era larger variant), watchtower stone tiles (rough ashlar, 3-tile implied height), iron-reinforced gate tile (2x3, closed state dominant in son's era), Vanguard banner sprite (red-and-steel cooperative in father's era, gray-on-gray in son's), sentry sprites (soldier figures at posts and on walls). Son's era additions: faint violet crystal-thread tiles overlaying the rust mineral streaks on the cliff walls (subtle, not the full corruption glow), wanted-poster sprites on the gatehouse wall (lore flavor), refugees-visible-through-gate overlay if looking south from the gatehouse area.

### ambience

Canyon acoustics with natural reverb — sounds bounce between the cliff walls with a half-second delay, making distant voices present but unintelligible. Father's era: occasional sentry's boot on flagstone, junior officer writing at the passage book, mule team passing through with cart-wheels on stone and teamster's quiet commands, a distant bird of prey's cry echoing between the cliffs. Son's era: the gatehouse gate's chain-windlass clang at unpredictable intervals (the sound that echoes down into the Refugee Camp), Vanguard soldiers on the walls calling tight-procedural orders to each other across the pass, the flapping of the new gray banners in the canyon wind, the scrape of boots on stone platforms overhead. The canyon wind itself is unchanged between eras — sharp, channeled, the most constant sound in the zone.

### music

Shares the Ashenford march theme but more distant and more enclosed (the canyon geometry compresses the music). Father's era: the snare cadence and tenor-horn melody from the Garrison Square play at reduced volume, with the canyon's reverb adding a half-second echo that deepens the march's sense of scale. Son's era: the same march but with the snare playing behind the beat more noticeably here, and a new element — a single long trumpet note sustained above the march, representing the closed gate — that does not resolve. On the goat trail, all melodic instruments drop out and only ambient wind plus a quiet sustained bass note carry the music. If combat triggers in the eastern slopes, a sharp plucked-string tension theme from the shared combat track layers over everything.
