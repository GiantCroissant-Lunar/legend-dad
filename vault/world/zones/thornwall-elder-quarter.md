---
type: zone
status: draft
articy-id: ""
tags: [town, residential, story]
connections:
  - "[[Thornwall]]"
  - "[[Thornwall Market]]"
  - "[[Elder Aldric]]"
  - "[[Aric]]"
parent-location: "[[Thornwall]]"
zone-type: town
biome: town
floor: 0
grid-width: 16
grid-height: 14
era: "Both"
encounter_rate: 0
last-agent-pass: "2026-04-16"
---

# Thornwall Elder Quarter

## Overview

The quieter eastern district of Thornwall, home to the village elder's cottage, a small chapel, and a handful of residential houses. This is where Aric grew up. The Elder Quarter is where key story conversations happen — the elder's cottage contains maps, records, and Kaelen's hidden journal. In the father's era, it's a peaceful residential area. In the son's era, several houses are abandoned, but the elder's cottage remains the beating heart of the community.

## Layout & Terrain

Medium zone (16x14 tiles). Flagstone paths connect the buildings. The elder's cottage is the largest structure (4x3 tiles) at the north end, with a small garden patch beside it. A chapel (3x2 tiles) sits at the south end. Four residential cottages (2x2 each) line the east and west sides. A large oak tree (2x2, impassable) grows in the center courtyard. The south exit leads to the Market. No other exits — this is a dead-end district, reflecting its quiet nature.

## Entities & Encounters

**Father's era:**
- Village elder (in cottage — dialogue: local history, advice for Kaelen)
- 2 residents (ambient, short dialogue)
- Chapel keeper (dialogue: lore about the region's founding)

**Son's era:**
- Village elder (aged, in cottage — dialogue: stories about Kaelen, concern for Aric)
- Aric (found here at certain story points)
- 1 remaining resident
- Kaelen's Journal discovery event (triggered at militia barracks in Market, but the journal content references this area)

## Era Variants

**Father → Son changes:**
- Elder's cottage: well-maintained, garden flourishing → maintained but aged, garden smaller
- Residential cottages: 4 occupied → 2 occupied, 2 boarded up
- Chapel: active, candles lit → still open but dusty, fewer candles
- Oak tree: full green canopy → still alive but leaves are thinning, some bare branches
- Flagstone: clean → moss-covered, some cracked
- Overall: warm, lived-in → quiet, holding on

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: flagstone path (gray-blue, more formal than cobblestone), elder's cottage tiles (larger stone building, thatched roof visible from top-down as brown texture, warm window glow), residential cottage tiles (smaller wood-and-stone, varied roof colors), chapel tiles (pale stone with small steeple shadow), garden tiles (brown earth with green plant rows), oak tree tiles (large trunk center with canopy overlay spreading 2x2), boarded cottage variant (dark windows, boards across door). Flagstone should feel quieter and more dignified than the Market's cobblestone. The elder's cottage should clearly be the most important building — slightly larger, warmer lighting, more detail in the roof tiles.

### ambience

Father's era: flagstone footsteps (softer than cobblestone), wind through the oak tree's leaves, a garden tool clinking, chapel bell (single tone, once per loop), distant laughter from the Market, a door opening and closing, fire crackling from the elder's cottage chimney. Gentle, residential, safe. Son's era: flagstone footsteps, wind through the oak (thinner sound, fewer leaves), elder's chimney fire (still there — the one constant), creaking from abandoned cottages, chapel bell (same tone but sounds lonelier in the quiet), no Market sounds. The elder's chimney fire sound is the emotional anchor — the one thing that hasn't changed.

### music

Father's era: gentle harp arpeggios in C major with a solo oboe melody — warm, domestic, unhurried. The oboe suggests wisdom and age (the elder's theme hint). Volume is low — this is background music for conversation scenes. Son's era: same harp pattern but slower, in C minor. The oboe is replaced by a solo clarinet playing the melody an octave lower — the same wisdom made heavier by twenty years. A faint music-box quality on the last phrase suggests childhood memories (Aric's connection to this place).
