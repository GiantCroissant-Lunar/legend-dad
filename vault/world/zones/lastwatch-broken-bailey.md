---
type: zone
status: draft
articy-id: ""
tags: [dungeon, crystal-corruption, exterior, son-era-hazard]
connections:
  - "[[Lastwatch]]"
  - "[[Lastwatch Tower Interior]]"
  - "[[Iron Peaks]]"
  - "[[Iron Peaks Trail]]"
  - "[[Jessa Vale]]"
  - "[[The Watch Holds]]"
  - "[[The Crystal Shadow]]"
parent-location: "[[Lastwatch]]"
zone-type: dungeon
biome: dungeon
floor: 0
grid-width: 22
grid-height: 18
era: "Both"
encounter_table:
  - bestiary: "[[Crystal Crawler]]"
    weight: 4
    era: "son"
  - bestiary: "[[Iron Borer]]"
    weight: 3
    era: "son"
encounter_rate: 0.18
difficulty_tier: 7
last-agent-pass: "2026-04-16"
---

# Lastwatch Broken Bailey

## Overview

The outer bailey of Lastwatch keep — the walled courtyard enclosing the central tower, stables, cistern, and Hesper's Stone. In Kaelen's era the bailey is intact and austere: gray granite walls, packed-earth ground, a small stone stable block, a cistern cap in the courtyard center, the carved slab of Hesper's Stone set against the east wall. In Aric's era the bailey is half-consumed: crystal growths have come up through the foundations and climbed the bailey walls, the north wall is cracked open in a jagged breach, the stables are a lattice of pale violet, and the cistern water has gone silver-gray. Only Hesper's Stone remains in a small clear ring at the east wall. This is Lastwatch's combat zone.

## Layout & Terrain

Medium zone (22x18 tiles) with a roughly square bailey interior. Granite outer walls form the zone boundary on east, south, and west (3-tile implied height, impassable); the north wall has a jagged breach (2-tile-wide gap, walkable, opening to a cliff path off-map north that links to Iron Peaks Trail). The central tower door sits against the south inner wall (transition to Lastwatch Tower Interior). The stable block is a 4x3 structure on the east-southeast (partially impassable — walkable interior in father's era with stalls and a tack room, impassable entirely in son's era due to crystal lattice). The cistern cap (1x1 iron grate, impassable) is at the bailey's center. Hesper's Stone is a 1x1 slab against the east wall with a small walkable clear-ring around it. Packed-earth ground covers the majority of walkable space in father's era; son's era overlays crystal-growth cluster tiles across perhaps 40% of the ground. Exits: south (to Lastwatch Tower Interior via the tower door), north (through the wall breach to Iron Peaks Trail off-map — son's era only).

## Entities & Encounters

**Father's era:**
- Patrol-rotation soldier sprites (2-3 at varying positions, ambient walking patterns)
- Stable boy sprite near the stable block (ambient)
- 1 hitching post with 2 horse sprites at the stable block
- Holt's forge glow visible through an open armory-adjacent exterior window on the south-southwest wall (audible hammer from inside; see Tower Interior zone)
- No combat encounters (encounter_rate bypass in father era)
- Hesper's Stone is interactable: reading the inscription surfaces lore about Jessa Vale's grandmother

**Son's era:**
- No NPCs (Jessa stays in the tower; no one else remains)
- Combat encounters per table: Crystal Crawler (primary, emerging from crystal-growth clusters), Iron Borer (from the wall breach)
- Hesper's Stone still interactable, with additional son's-era dialogue if Aric reads it after speaking with Jessa (she mentions that she visits the stone daily — the small clear ring around it is the only other place in Lastwatch that remains clear)
- Wall breach on the north is walkable (connects to Iron Peaks Trail)
- Crystal growth clusters are interactable: they can be broken for resources (small crystal fragments) at the cost of audible noise that triggers a faster encounter roll while the sound lasts

## Era Variants

**Father → Son changes:**
- Outer walls: granite blocks intact, crisp corners → the north wall is cracked open with a jagged 2-tile breach; the east and west walls have visible crystal threads climbing them
- Ground: packed earth, clean, with patrol-path wear patterns → packed earth with pale violet crystal-growth clusters occupying perhaps 40% of the walkable space
- Stable block: intact, 2 horses, straw on the floor, tack room in the rear → a lattice of pale violet crystal consuming the entire block; no horses, no straw; the block is walkable only as a perimeter around its impassable crystal interior
- Cistern cap: iron grate over clear rainwater → iron grate over silver-gray silted water; the water emits a faint crystal shimmer that is visible through the grate
- Hesper's Stone: intact slab, packed-earth ring around it → intact slab, small clear ring around it that the crystal growth has not crossed (a narrative detail — the only other clear ring in Lastwatch besides the tower and platform)
- Patrol soldiers: 2-3 ambient → none
- Light: daytime with strong mountain sun, or dusk with the signal brazier lighting the tower roof above → same daylight, but the crystal clusters emit a faint steady violet glow that competes with the sun; at dusk the crystal glow is the dominant light source in the bailey except near Hesper's Stone

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: dark gray granite outer wall tiles (3-tile implied height, impassable, with slight weathering variations), packed-earth ground tiles (brown with subtle patterns of worn patrol paths), stable block structure tiles (gray stone base with dark-stained timber upper walls, thatched roof overlay), cistern-cap iron grate sprite (1x1, circular, set into a square stone frame), Hesper's Stone slab sprite (1x1, dark gray, with fine carved lettering visible at pixel level), hitching post sprite, horse sprites (walking-idle and grazing variants), armory window glow sprite (warm orange leak from the south-southwest wall, father's era only). Son's era additions: north-wall breach tiles (jagged stone debris spilling inward, walkable through the gap), crystal-thread wall-overlay tiles (pale violet geometric threads climbing the east and west walls), crystal-growth cluster tiles on the ground (geometric pale violet shapes, 1-3 tiles per cluster, emit faint glow), crystal-consumed stable block overlay (the stable block's silhouette is still present but overlaid with a lattice of pale violet crystal, its interior now impassable), silver-gray silted cistern variant (the grate's water sheen changes to that pale gray-violet), Hesper's Stone clear-ring tile (a 1-tile-radius border of clean packed earth around the stone, contrasting against the surrounding crystal growth). The bailey should read visually as two different places that share a floor plan — the same space, one preserved and one consumed.

### ambience

Exterior: the same high-altitude wind as the rest of Lastwatch, channeled differently by the bailey walls — less moaning through arrow slits (fewer slits on the interior) and more direct flow across the courtyard. Father's era: patrol boots on packed earth at regular intervals, horses snorting in the stable, stable boy's boots on straw, Holt's hammer from inside the armory (three strikes, pause, three strikes, pause — the armorer's working rhythm), the clink of a bucket against the cistern grate when someone draws water. The keep's low background ambient of a small garrison going about its day. Son's era: wind dominates. The crystal clusters produce a faint continuous high-frequency hum that is louder in this zone than anywhere else in the keep (because the clusters are densest here); the hum has a rhythmic quality that is just below melodic, as if the keep is trying to sing. When Crystal Crawlers trigger, the skitter of their legs on stone is the first warning; Iron Borers emerging from the wall breach have a distinct grinding-through-rock sound that precedes their appearance by two to three seconds. Hesper's Stone's clear ring has a small specific acoustic property — standing inside it, the crystal hum drops by about 30%, as if the stone itself is holding the space.

### music

Father's era: shares the Lastwatch Tower Interior theme at reduced volume — the French horn melody of a watchman's scan plays overhead from the tower, drifting down into the bailey at a softer presence, giving the zone a sense of being watched over rather than hosting its own music. No distinct bailey theme. Son's era: the tower theme is not audible here — the crystal hum fills the acoustic space. A low bowed bass holds a single sustained note as the zone's base music layer, moving slowly between two pitches a tritone apart. When combat triggers, the shared combat tension theme layers over the bass; when combat ends, the bass resumes alone. At Hesper's Stone in the son's era, standing inside the clear ring briefly, a quiet fragment of the cooperative joint-militia march (from the Crystal-Shunted Watchman's music) surfaces, played forward rather than backward — the keep remembering what it was built for. The fragment lasts two bars. Then the bass returns.
