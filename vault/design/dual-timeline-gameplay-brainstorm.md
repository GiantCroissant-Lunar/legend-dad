---
type: design
status: draft
tags: [gameplay, core-loop, timeline, brainstorm]
last-agent-pass: 2026-04-12
---

# Dual-Timeline Gameplay Brainstorm

Captured from brainstorming sessions on 2026-04-12. Ideas range from confirmed
directions to open questions that need further digestion.

---

## 1. Core Concept

A top-down JRPG (Dragon Quest style) played on web. The screen shows two
gameplay views simultaneously — one for the **father** (current time) and one
for the **son** (20 years later). The player toggles control between them, and
the two timelines are intertwined through cause-and-effect, shared geography,
and inherited consequences.

**Pitch line:** A top-down RPG where you play as a legendary hero in the
present and his son 20 years later, switching between eras to build, break, and
reinterpret the same world. The father shapes history; the son survives it.

---

## 2. Confirmed Directions

These were discussed and agreed upon during brainstorming.

### 2.1 Genre & Scope

- **Classic JRPG with timeline twist** — towns, NPCs, turn-based battles,
  quests, leveling. The dual timeline is the differentiator, not a replacement
  for traditional JRPG structure.
- Web target (Godot 4.6 WASM, itch.io distribution).

### 2.2 Timeline Switching

- **Split simultaneous with active toggle** — both eras are always visible.
  The player toggles which view is active (controlled). The active view is
  always rendered in front of the inactive view (higher z-index).
- This is the most ambitious option but the most unique.

### 2.3 Screen Layout — Floating Windows over World Map

The two gameplay views are **not** fullscreen. They float like application
windows over a fantasy world map background.

| Element       | Screen Area | Description                              |
|---------------|-------------|------------------------------------------|
| Active view   | ~50% WxH    | Larger, gold border, always in front      |
| Inactive view | ~40% WxH    | Smaller, dimmed, sits behind active view  |
| World map     | 100% (behind)| Parchment-style fantasy map, always there |

- Views have **mac-style window chrome** (title bar with dots, era label).
- When the player toggles active era, the windows swap size and z-order.

### 2.4 World Map — Functional Layer (not just decoration)

The world map is accessed via a **toggle button** (not hold-to-peek). When
toggled, the gameplay windows slide aside to reveal the full map.

**The map is dual-state:**

- When the **father's view** is active, the map shows the father's footprints
  and journey markers.
- When the **son's view** is active, the map shows the son's footprints.

**The map is interactive:**

- Regions on the map can be clicked to view **cutscene events** happening at
  that location.
- These events play in a temporary view window (read-only, no player control).
- Events follow the active era's timeline — father-focused map shows father-era
  events, son-focused map shows son-era events.

---

## 3. Ideas to Digest — Father's Footprints Visible to Son

**Question:** When the son's view is active and the map is open, should the
son also see the father's footprints?

**Proposed answer (needs confirmation):** Partially visible, narratively gated.

- The son does NOT see all of father's journey by default.
- The son sees father's footprints only at locations he has **heard stories
  about** — from NPCs, journals, or lore items.
- Locations where the stories are **wrong** become discovery moments — the son
  visits expecting one thing and finds the truth was different.
- This creates a "following in his footsteps" mechanic where the son gradually
  pieces together the father's true journey.
- It also gives the player a reason to talk to NPCs in the son's era — they
  are not just quest givers, they are sources of the father's map.

**Status:** Promising direction, not yet confirmed.

---

## 4. Ideas to Digest — In-Between Timeline Events (Gap Years)

**Question:** Should the world map show events from in-between the two main
timelines? For example, 5 years after the father's adventure, or 8 years before
the son's adventure begins.

**Proposed answer (needs confirmation):** Yes, but cutscene-only.

- Gap events are **not playable**. No new characters for the gap years.
- They appear as **map cutscene vignettes** that fill in the 20-year gap.
- Examples:
  - "3 years after the father left, the blacksmith's apprentice took over the
    forge."
  - "12 years later, the sealed cave began leaking dark energy."
  - "The son was 8 years old when the old knight visited and told him about his
    father's battle at Iron Peaks."
- Gap events are the connective tissue between eras. The player sees **how**
  the world got from state A to state B, not just the endpoints.

**Status:** Promising direction, not yet confirmed.

---

## 5. Ideas to Digest — Same-Spot Overlap Mechanics

When the father and son are at the **same geographic location**, the world map
shows overlapping markers. This is the moment of tightest coupling between
timelines and should unlock special gameplay.

Four concepts were explored (interactive demos built). These are **not mutually
exclusive** — they layer on top of each other.

### 5.1 Temporal Resonance (Real-Time Cause & Effect)

- **When:** Default mechanic at any shared location.
- **How:** Father's actions update son's view in real-time while both are at
  the same spot.
- **Example:** Father pushes a boulder to clear a path. Son's view instantly
  shows the path is now open (the boulder has been gone for 20 years).
- **Feel:** Immediate, satisfying, readable.

### 5.2 Echo Battle (Cross-Timeline Combat)

- **When:** Boss fights at shared locations.
- **How:** Father fights a powerful enemy. The same enemy (or its descendant)
  exists in the son's era carrying **scars from the father's battle**. Father's
  attacks create lasting weaknesses the son can exploit.
- **Example:** Father wounds a dragon's left wing. In son's era, the ancient
  dragon cannot fly and is vulnerable to attacks from the left.
- **Feel:** Strategic, rewarding for paying attention across eras.

### 5.3 Timeline Convergence (Views Merge)

- **When:** Reserved for 3-4 major story climax moments. Rare, high impact.
- **How:** The two gameplay windows **physically merge into one larger view**.
  Father and son occupy the same space across time. They cannot see each other,
  but their actions interleave.
- **Example:** Son steps on a floor plate that the father needs to unlock a
  door. Father lights a torch that illuminates the son's dark room.
- **Feel:** Epic, disorienting (in a good way), emotionally charged.

### 5.4 Temporal Dungeon (Two-Era Linked Dungeon)

- **When:** Shared-location dungeons.
- **How:** Same floor plan, different states. Father's dungeon is intact with
  traps and guards. Son's dungeon is ruined with collapsed paths and different
  hazards. The player switches between them to solve rooms.
- **Example:** Father activates a water gate switch to drain a chamber. Son
  walks across the now-dry floor 20 years later.
- **Feel:** Puzzle-box satisfaction, reuses geometry efficiently.

### 5.5 Proposed Layering

| Location Type     | Mechanics Used             |
|-------------------|----------------------------|
| Normal shared     | Resonance (5.1)            |
| Boss at shared    | Resonance + Echo Battle    |
| Story climax      | Convergence (5.3)          |
| Shared dungeon    | Resonance + Temporal Dungeon |

**Status:** All four concepts are promising. Layering approach needs
confirmation. Convergence (5.3) is the most ambitious — needs scoping.

---

## 6. Ideas from Initial Brainstorm (Unprocessed)

These ideas came from the first brainstorming session and have not been
discussed in detail yet. Captured here for future reference.

### 6.1 Legacy Inventory

- Father can intentionally leave items for the son: bury a key, hide a sword,
  write journal notes, plant herbs.
- Son discovers these through exploration or inherited clues.
- Pattern: Son finds a problem → discovers evidence of what father could do →
  player switches to father and sets it up → future updates.

### 6.2 Town Growth and Decline

- Villages evolve over 20 years based on father's choices.
- A village can become: thriving trade town, militarized fort, ghost town, cult
  center, flooded ruin, prosperous farming hub.
- Father's choices affect: shops, NPC lineages, side quests, available party
  members, town appearance, rumors about the father.
- Efficient for web: reuse same map locations with different state layers.

### 6.3 "History is Wrong" Quests

- The son grows up hearing stories about the father, but stories are
  incomplete, biased, or false.
- Everyone says the father abandoned a town, but the son learns he stayed
  behind to hold a monster.
- Father is remembered as hero, but son discovers one of his victories caused
  a later disaster.
- A villain in son's era turns out to be the child of someone father betrayed.

### 6.4 Asymmetric Protagonists

- Father and son should NOT feel like palette swaps.
- Father: physically stronger, socially respected, can alter unfinished
  structures, interacts with people who later become legends.
- Son: more agile or educated, reads father's journals, accesses collapsed
  ruins and old relics, uses inherited tools in upgraded form.

### 6.5 Family Inheritance System

- Father's choices influence son's build through story:
  - Which mentor trains the child
  - What values father teaches
  - What weapon style he leaves behind
  - What reputation the family carries
- Affects: dialogue, class specialization, stat bias, faction access, whether
  NPCs trust the son.

### 6.6 Parallel Quest Chains

- Design quests in pairs:
  - Father stops forest logging → son explores the surviving ancient forest.
  - Father saves apprentice healer → son meets her as elderly master.
  - Father spares a thief → thief's daughter runs the underground network.

### 6.7 Curated Causality (Scope Control)

- Do not simulate everything. Use a **curated causality system**:
  - Only important objects affect the future.
  - Each location has a handful of state flags.
  - Each major quest flips those flags.
  - Son's era reads flags to swap NPCs, tiles, paths, and quest availability.
- Instead of "every tree can grow," use: special sapling spots, specific
  buildings, named NPC families, dungeon state markers, town development
  choices.

---

## 7. Reference Games

| Game                              | Useful For                                       |
|-----------------------------------|--------------------------------------------------|
| Cris Tales                        | Showing multiple time states on one screen        |
| Radiant Historia                  | Timeline structure, player guidance across branches|
| Chrono Trigger                    | Past-to-future pacing, era contrast, world design |
| Zelda: Oracle of Ages             | Local cause-and-effect puzzles (plant seed, tree grows) |
| Day of the Tentacle               | Multi-era puzzle design, cross-era item logic     |
| Dragon Quest V                    | Family/generational arc in classic JRPG structure |

---

## 8. Open Questions

1. **Father's footprints on son's map** — fully hidden, partially revealed
   through narrative, or always visible? (Leaning toward narratively gated.)
2. **Gap year events** — how many? Are they unlockable or always available?
3. **Convergence mechanic scope** — how many convergence moments? What triggers
   them? Is the merged view a special scene or does it use the same tile engine?
4. **Combat system** — turn-based is assumed (Dragon Quest style) but not yet
   discussed in detail. How does echo battle integrate with the base combat?
5. **Party members** — does the father have companions? Does the son? Are any
   NPCs shared across eras?
6. **World size** — how many regions/towns/dungeons? What is a realistic scope
   for a web game?
7. **Progression structure** — is it linear chapters or open-world? Can the
   player revisit earlier areas freely?
8. **Save system** — how does saving work with two simultaneous timelines?

---

## 9. Next Steps

- Digest ideas in sections 3-6.
- Prioritize which mechanics to prototype first.
- Define world size and region structure.
- Design the core gameplay loop in detail.
- Begin combat system design.
