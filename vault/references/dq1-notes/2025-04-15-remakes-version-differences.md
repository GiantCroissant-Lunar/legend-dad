# Dragon Quest 1: Remakes and Version Differences Research

**Date:** 2025-04-15
**Topic:** DQ1 remakes, localization changes, and quality-of-life improvements across versions
**Sources:** Wikipedia, Dragon Quest Wiki (dragon-quest.org)

---

## Overview of Releases

| Platform | Year (JP) | Key Notes |
|----------|-----------|-----------|
| Famicom/NES | 1986 (JP) / 1989 (NA) | Original release |
| MSX/MSX2 | 1986 | PC ports |
| Super Famicom | 1993 | First remake, combined with DQ2 |
| Game Boy Color | 1999 (JP) / 2000 (NA) | Portable remake |
| Mobile phones | 2004 | Graphical updates |
| Wii | 2011 | 25th Anniversary Collection |
| iOS/Android | 2013-2014 | Mobile ports |
| Nintendo Switch | 2019 | HD-2D style remake (with DQ2/3) |
| HD-2D Remake | 2025 (Oct 30) | Dragon Quest I & II HD-2D Remake |

---

## Key Version Differences

### Original Famicom (1986) vs NES "Dragon Warrior" (1989)

**Save System:**
- **Famicom:** Password-based "Spell of Restoration" (no battery save)
  - HP and MP reset on load
  - Treasure chest states not tracked — can reopen chests by reloading
- **NES:** Battery-backed SRAM save ("Adventure Log")

**Graphics:**
- NES version has improved graphics over original Famicom
- Character sprites given directional facing (Famicom sprites always face forward)
- Coastline graphics upgraded
- Title screen redesigned

**Translation & Localization:**
- Title changed from "Dragon Quest" to "Dragon Warrior" (trademark conflict with tabletop RPG "DragonQuest")
- Added pseudo-Elizabethan "thee/thou" dialogue style
- Name changes: "Loto" → "Erdrick", "DracoLord" → "Dragonlord"
- Different town/character names

**Gameplay Interface:**
- Direction selection required for interactions in Famicom (no directional sprites)
- NES: Face direction automatically used for talking/searching

---

### Super Famicom Remake (1993)

Part of "Dragon Quest I & II" compilation.

**Major Changes:**
- **Equipment System:** Can carry multiple weapons/armor (previously only 1 of each type, new equipment auto-replaced old)
- **Dungeon Scale:** Dungeons greatly expanded in size
- **Craggy Cave:** Completely redesigned
- **Leveling:** Reduced XP needed to level; increased XP/gold from monsters
- **Dragon sprite:** Given on-screen sprite (was invisible in original)
- **Shrines:** Given world map sprites and unique music (from DQ2)
- **Lyre of Ire:** Now summons any enemy in area (was limited to Tantegel/Mountain Cave monsters)
- **Erdrick's Tablet:** Now a tombstone instead of chest
- **Damdara music:** Changed from dungeon theme to DQ2's Requiem

---

### Game Boy Color Version (1999/2000)

**Convenience Features:**
- **Quick Save:** Can quicksave anytime outside battle (returns to title screen)
- **Gold Storage:** Can store some gold
- **Streamlined menus**
- **Field log save**

**Balance Changes:**
- Monsters give more XP and gold (reduced grinding)
- Golem in Mercado given on-screen sprite

**Presentation:**
- Names shortened due to GBC display constraints
- New translation closer to Japanese (discarded pseudo-Elizabethan style)
- Names: "Dragonlord" → "DracoLord", "Erdrick" → "Loto"

---

### Mobile/Smartphone Versions (2004, 2013-2014)

**Graphics:**
- Based on Super Famicom remake visuals
- Higher resolution sprites

**iOS/Android Specific (2014):**
- Uses NES-era names but more faithful script translation
- Touch controls
- Quicksave functionality
- Updated UI

---

### Nintendo Switch HD-2D (2019)

Part of "Dragon Quest I, II & III" collection.

**Visual Style:**
- HD-2D graphics (2D sprites with 3D lighting/effects)
- Similar style to Octopath Traveler

**Modern Features:**
- Auto-save
- Increased battle speed
- UI improvements

---

### Dragon Quest I & II HD-2D Remake (October 30, 2025)

Upcoming release for Nintendo Switch, PS5, Xbox Series X/S, PC.

**Confirmed Features:**
- Fully rebuilt HD-2D graphics
- Modernized UI and controls
- Quality-of-life improvements
- Orchestrated soundtrack

---

## Design Lessons for Legend Dad

### 1. Progressive Modernization
Each remake of DQ1 demonstrates how to modernize a classic without losing its core identity:
- **Keep the soul:** Same overworld layout, same progression, same story beats
- **Streamline friction:** Auto-facing, quicksave, streamlined menus
- **Add convenience without breaking balance:** Gold storage, multiple equipment slots

### 2. The Save System Evolution
DQ1's save system history shows a progression:
- Password (hardcore, punishing) → Battery save (convenient) → Quick save (modern)

For **Legend Dad**: Consider a tiered approach:
- Inn/sanctuary save = full save, restores HP/MP
- Camp/tent save = quick save, limited uses
- Death = lose gold/gems but keep experience

### 3. Localization Philosophy Shifts
- NES: Dramatic reimagining ("Dragon Warrior", pseudo-Elizabethan)
- GBC: Closer to Japanese, modernized names
- Mobile: NES names with faithful script

For **Legend Dad**: Consistent naming from the start; avoid the "Loto/Erdrick" confusion.

### 4. Balance Tuning Over Time
Later remakes consistently:
- Reduced grinding (more XP/gold from monsters)
- Lowered level requirements
- Added convenience (quick travel, storage)

For **Legend Dad**: Front-load the fun, keep the challenge in the *decisions*, not the *time investment*.

### 5. UI/UX Lessons
- Original: Direction selection for every interaction
- NES: Auto-facing simplified this
- GBC: Streamlined menus
- Modern: Touch controls, auto-save

For **Legend Dad**: One-button context actions, smart cursor, don't make players navigate menus for common actions.

---

## Key Takeaways

1. **The core loop must remain intact** — every successful remake preserved the original overworld, towns, and progression.

2. **Frustration != Challenge** — removing tedium (passwords, grinding, menu friction) makes the game better without making it easier.

3. **Modern expectations matter** — auto-save, quick travel, and visual feedback are baseline now.

4. **Names matter, consistency matters more** — "Erdrick/Loto/DracoLord" confusion shows the cost of changing established names.

---

*Research compiled for Legend Dad game project — reference material for web RPG design decisions.*
