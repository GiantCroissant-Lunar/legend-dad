---
type: zone
status: draft
articy-id: ""
tags: [forest, wilderness, transition]
connections:
  - "[[Whispering Woods]]"
  - "[[Thornwall North Gate]]"
  - "[[Whispering Woods Deep]]"
  - "[[Maren]]"
parent-location: "[[Whispering Woods]]"
zone-type: overworld
biome: field
floor: 0
grid-width: 24
grid-height: 20
era: "Both"
last-agent-pass: "2026-04-13"
---

# Whispering Woods Edge

## Overview

The first zone of the Whispering Woods, where the village farmlands give way to old-growth forest. A dirt path from Thornwall's north gate enters from the south and splits into a main trail heading north (to the Deep Woods) and a side path east (to the Forester's Cabin where Maren lives). The canopy is lighter here than deeper in — enough sunlight reaches the ground for wildflowers and undergrowth. This zone serves as the first wilderness area with light combat encounters.

## Layout & Terrain

Large zone (24x20 tiles). The southern third is transitional — scattered trees, tall grass, the edge of Thornwall's abandoned farmland (son's era: fallow fields with sinkholes). The middle is proper forest edge — medium-density trees with a clear path winding through. The northern third is denser canopy with the path narrowing. The dirt path splits at center: main path continues north, side path goes east to the Forester's Cabin (a small structure at the map's east edge). A stream crosses the zone east-west near the north end. Walkable tiles: dirt path, grass, shallow stream crossing. Impassable: tree trunks, dense undergrowth, deep stream sections.

## Entities & Encounters

**Father's era:**
- 1-2 passive forest creatures (deer, rabbit — ambient)
- 1 forester NPC on the path (dialogue: forest conditions, path advice)
- Medicinal herb pickups near the stream (3-4 spots)

**Son's era:**
- 1-2 hostile corrupted creatures (first combat encounters)
- Maren (near Forester's Cabin — companion recruitment)
- Fewer herb spots (some replaced by fungal growth — visual cue for corruption)
- 1 sinkhole near abandoned farmland (environmental hazard / story point)

## Era Variants

**Father → Son changes:**
- Southern farmland: golden wheat → cracked fallow earth with 1 sinkhole tile
- Tree canopy: full green → thinned, some bare branches letting harsh light through
- Stream: clear blue → slightly murky gray-blue
- Wildflowers: present → mostly gone, replaced by dark fungal patches
- Forester's Cabin: well-maintained → patched up, Maren's modifications visible
- Path condition: clear dirt → overgrown edges, some roots breaking through
- Creature type: passive animals → hostile corrupted creatures

## Creative Prompts

### tilemap-art

16-bit pixel art tileset, top-down perspective, 16x16 tile grid. Core tiles: dirt path (brown, worn, 2-3 variants), grass ground (varied greens with occasional wildflower pixel), tree trunk tiles (brown circles of varying size — small 1x1, medium 2x1), canopy overlay tiles (semi-transparent green dappled pattern, layered above ground), undergrowth tiles (dark green, impassable, shorter than trees), stream tiles (2-tile wide, animated blue with white highlight pixels for flow), stream crossing tile (shallow, walkable, slightly different color), tall grass tiles (lighter green, swaying animation frame). Forester's Cabin: small wooden structure (3x2), chimney smoke, pelts hanging outside. Son's era additions: dead tree trunk tiles (gray), thinned canopy overlay (more gaps), fungal growth tiles (dark purple-black patches on ground), sinkhole tile (dark circle with crumbled edge), cracked earth tiles (for abandoned farmland), murky stream variant. The visual transition from south (open, light) to north (dense, darker) should be gradual across the zone.

### ambience

Father's era: the signature Whispering Woods canopy rustle (constant, layered leaf sounds), birdsong (3-4 species at varying distances), stream babbling (louder near water, fading with distance), insect buzz (gentle, summer), footsteps switching from dirt to grass to shallow water. Occasional: deer movement in undergrowth, branch snap, woodpecker. A full, healthy forest soundscape. Son's era: canopy rustle still present but higher-pitched and thinner. Fewer bird species (1-2, with long silences between calls). Stream sound is present but duller. Add: wood creaking (stressed trees), a low subsonic pulse near the sinkhole, crystal-like chiming near fungal patches (faint, unsettling). Creature sounds: skittering in undergrowth, a low growl at medium distance. The forest edge should sound like a warning — enough nature sounds to be recognizably forest, enough wrong sounds to signal danger.

### music

Father's era: layered woodwinds in E minor — two recorders in thirds over finger-picked lute. Gentle, cyclical, walking pace. Natural sounds bleed into the arrangement. The melody is exploratory — ascending phrases suggesting discovery. Loop: 120 seconds. Son's era: solo recorder, same melody but with pauses where the second recorder should be. Lute replaced by bowed psaltery adding tension. Occasional dissonant note — a half-step clash that resolves quickly, suggesting the corruption is audible. Near the sinkhole: music drops to just the psaltery drone. Loop: 120 seconds.
