---
type: zone
status: draft
articy-id: "72057594037930354"
tags: [interior, keep, hub, joint-militia]
connections:
  - "[[Lastwatch]]"
  - "[[Lastwatch Broken Bailey]]"
  - "[[Jessa Vale]]"
  - "[[Keep Armorer Holt]]"
  - "[[Crystal-Shunted Watchman]]"
  - "[[The Watch Holds]]"
  - "[[The Crystal Shadow]]"
parent-location: "[[Lastwatch]]"
zone-type: interior
biome: dungeon
floor: 1
grid-width: 14
grid-height: 20
era: "Both"
encounter_rate: 0
last-agent-pass: "2026-04-16"
---

# Lastwatch Tower Interior

## Overview

The central three-story tower of Lastwatch keep plus its signal platform rooftop — the only part of the keep that remains free of crystal growth in the son's era and the functional core of the keep in both eras. This zone covers the ground-floor Great Hall, the second-floor armory access and landing, Jessa Vale's warden's tower room on the third floor, and the open signal platform above. Vertically stacked via LDtk floor layers (floor 1 here represents the tower; the adjacent Broken Bailey is floor 0).

## Layout & Terrain

Narrow vertical zone (14x20 tiles) oriented around the central tower's interior. The zone uses a stacked vertical layout — four sub-regions represent the tower's four levels, connected by spiral staircase tiles at the tower's north wall. Ground floor (bottom 5 rows): the Great Hall — a long rectangular stone-vaulted chamber with a long timber table (father's era) or crystal-growth-claimed table (son's era) at center, iron-banded chairs, a wall map at the west, a cold hearth at the east wall, spiral stair entry at the north. Second floor (next 4 rows): the armory access and landing — a small square landing with the armory door on the west wall (open in father's era with Holt at work visible through the doorway; sealed behind a crystal-wall in the son's era, the door blocked). Third floor (next 4 rows): Jessa's warden's tower room — a narrow bed on the east, a writing desk at the west under a single east-facing window, a cold hearth (Jessa has not lit a fire here in years per her character page — the state applies in both eras), three stacks of logs on the desk. Top (top 5 rows): the signal platform — an open stone deck with a mounted iron brazier prop on a rotating frame, rope-and-pulley rigging visible at the north. Sky overhead. Exits: a south door at the ground floor's Great Hall leads to Lastwatch Broken Bailey.

## Entities & Encounters

**Father's era:**
- Jessa Vale in the warden's tower room at the writing desk (quest-giver for "The Watch Holds"; offers tea from the small iron kettle)
- Keep Armorer Holt in the armory through the second-floor landing door (sharpening, hammering, interactable for gear repair and blade-offering scene in "The Watch Holds")
- 1-2 ambient soldier sprites in the Great Hall (off-duty, eating at the table)
- Standard wall map and log-book as interactable lore props

**Son's era:**
- Jessa Vale alone, same writing desk, thirty years later (quest-giver for "The Crystal Shadow")
- Holt absent (armory sealed behind crystal)
- The Crystal-Shunted Watchman appears on the signal platform at dusk (scripted per "The Crystal Shadow" Act 3)
- The sealed iron box with Kaelen's residue sample on a desk shelf (interactable per "The Crystal Shadow")
- Jessa's thirty years of logs stacked on the desk (interactable lore — reading them surfaces sightings entries and weather records)
- No ambient soldiers

## Era Variants

**Father → Son changes:**
- Great Hall timber table: intact, iron-banded chairs, map on the wall → one leg of the table claimed by crystal growth coming up through the flagstone floor; map fossilized in pale violet crystal film, still readable; two of the four iron-banded chairs gone under crystal
- Great Hall hearth: cold in both eras (stated detail: Jessa does not light fires in the keep's lower rooms in either era; the cold hearth is a character note in the father's era too, because of her grandmother's burden)
- Armory door (second floor): oiled timber, open during Holt's work hours → sealed behind a crystal-wall of growth, the door blocked and impassable
- Warden's tower room: bed, desk, cold hearth, logs — unchanged across both eras; the room is the same room, same bed, same kettle, one of the few continuities in the whole keep
- Signal platform brazier: crisp iron, full of pitch-soaked wood, rope-pulleys maintained → iron tarnished, pitch replaced weekly by Jessa with whatever she can salvage, rope-pulleys Jessa has rebuilt by hand three times (she is the only person who has ever serviced them in the son's era)
- Crystal-growth presence: none → visible at the Great Hall only; the second floor's armory corridor is fully crystal-claimed; the third-floor warden's room is clear; the signal platform is clear

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective with vertical floor layering, 16x16 tile grid. Core tiles: dark gray granite interior wall tiles (stone-vaulted Great Hall), stone flagstone floor tiles (lighter gray, worn smooth near the table), long timber table tile (4x1, dark-stained wood in father's era, one end overtaken by crystal in son's era), iron-banded chair sprites, wall-map sprite (parchment with painted-ink contour lines, 2x1), cold hearth tile (empty stone fireplace with ash-residue, cold in both eras), spiral staircase tile (stone steps rising, visual shorthand for vertical transition between floors), armory door tile (open variant with glimpse of forge-glow in father's era, crystal-sealed variant in son's era), bed sprite (narrow wooden frame with wool blanket), writing desk tile (1x2 wooden desk with candle, goose-quill, ink well, small iron kettle on a brass trivet), log-book stack tile, signal-platform stone deck tile (open to sky, cold gray light), mounted iron brazier sprite (rotating-frame structure, unlit daytime variant and lit-with-warm-orange-glow dusk variant). Son's era additions: crystal-growth tiles climbing up through flagstones at the Great Hall's northwest corner, crystal-sealed armory door variant, fossilized-in-crystal wall map overlay, sealed iron box sprite on the desk's bottom shelf (glowing very faintly through its casing). The warden's tower room and signal platform are intentionally visually identical between eras — the keep has been taken everywhere else, but these two spaces have held.

### ambience

High-altitude wind as a dominant layer through the signal platform, varying in pitch with wall geometry — moaning through arrow slits, whistling past the brazier-frame. Father's era interior: four pairs of boots on stone floors in the Great Hall, Holt's hammer from the armory above (consistent three-strike rhythm), Jessa's voice occasionally giving instructions to a soldier, wood crackling in the Great Hall's hearth if it happens to be lit during a meal, a cook stirring a pot in a small kitchen-alcove off the Great Hall (implied off-map). Son's era interior: silence as the default. Jessa's footsteps (slow) on stone stairs. Her writing quill on parchment at the desk. A new constant throughout the whole tower: the crystal growths at the keep's core emit a faint continuous high-frequency hum that is at the edge of perception and intensifies in the Great Hall near the taken table-leg. The warden's tower room and signal platform have almost no hum — those two spaces remain acoustically clean in both eras.

### music

Shares the Lastwatch location theme. Father's era: solo French horn in C minor playing the long rising-and-falling melody of a watchman's horizon-scan, with a low-string drone. A second violin enters in the second half playing in thirds with the horn — the cooperative counterpoint of the joint-militia era. Son's era: the horn plays alone, same melody, same tone; the second violin is gone; the drone has thinned to a single sustained note. Jessa's own violin voice enters quietly in the third-floor warden's room if the player lingers — a wordless alto counter-melody that is the music remembering her. On the signal platform at dusk in the son's era, all normal music drops out and the Crystal-Shunted Watchman's theme takes over if he is present (two pitched crystal tones plus a third quarter-tone off, plus the faint reversed fragment of a joint-militia march in the deep background).
