---
type: design
status: draft
tags: [gameplay, combat, battle, brainstorm]
last-agent-pass: 2026-04-12
---

# Combat System Design

Captured from brainstorming sessions on 2026-04-12. Builds on the dual-timeline
gameplay brainstorm (`vault/design/dual-timeline-gameplay-brainstorm.md`).

---

## 1. Core Style: Dragon Quest First-Person Turn-Based

The combat system follows the Dragon Quest tradition:

- **First-person perspective** — player sees the enemies, party is implied
  (off-screen). No character sprites on the battle screen.
- **Menu-driven commands** — Attack, Magic/Skill, Item, Defend, Flee.
- **Turn-based** — each party member selects a command, then the turn resolves
  in speed order.
- **Same system for both eras** — the only difference is party size.

This is the DQ1-through-DQ4 model: same battle engine, different party counts.

---

## 2. Era-Specific Party Structure

### Father Era: Solo with Advisor

- **Party size: 1** — the father fights alone.
- **One command per turn** — every turn is a single decision.
- **Combat feel:** Fast, personal, high-stakes. Every hit lands on you.
  Resource management (HP, MP, items) is critical because there's no healer
  to fall back on.
- **Advisor role:** A companion who does NOT fight but speaks during battle.
  The advisor interjects with:
  - Tactical hints ("This enemy is weak to fire")
  - Lore observations ("This is the beast that destroyed Ashenmoor")
  - Emotional reactions ("Watch out! That was close!")
  - Story foreshadowing ("Your son will face worse than this someday")
  - The advisor is a narrative device, not a mechanical one. They have no
    turn, no HP, no commands. They are a voice in combat.
  - **Open question:** Advisor identity and relationship to father (TBD,
    user noted "we will address this later").

### Son Era: Party of 3-4 with Banter

- **Party size: 3 or 4** (exact count TBD).
- **Multiple commands per turn** — one per party member.
- **Combat feel:** Tactical, social, team-based. Party composition matters
  (tank, healer, damage, support).
- **Party banter:** Members talk frequently during battle:
  - Reactions to big hits, critical strikes, near-death moments
  - Character-specific lines for enemy types
  - Encouragement, disagreements, humor
  - Story-relevant comments when fighting narratively important enemies
  - Banter frequency should feel natural, not every single turn. Maybe
    30-40% of turns have a comment.
- **Open question:** Who are the party members? Are any connected to
  father's story? (e.g., blacksmith's child, advisor's descendant, child
  of someone father saved/failed).

---

## 3. Battle Flow (Shared Between Eras)

The turn structure is identical for solo and party. Party just has more
command inputs per turn.

```
1. ENCOUNTER TRIGGER
   - Player touches enemy on overworld (visible enemies, not random)
   - OR scripted encounter (boss, story event)
   - Screen transitions to battle view

2. COMMAND PHASE
   - For each party member (1 for father, 3-4 for son):
     - Show command menu: Attack | Skill | Item | Defend | Flee
     - Player selects command and target (if applicable)
   - Advisor/banter text may appear between command selections

3. RESOLUTION PHASE
   - All actions (party + enemies) sorted by speed stat
   - Actions execute one by one with text/animation feedback
   - "Father attacks! 12 damage to Slime."
   - "Slime attacks! 8 damage to Father."
   - Advisor/banter may react to results

4. END-OF-TURN CHECK
   - If all enemies defeated → VICTORY
   - If party wiped → DEFEAT
   - If flee succeeded → return to overworld
   - Otherwise → back to COMMAND PHASE

5. VICTORY
   - EXP gained, gold gained, item drops
   - Level up check with stat growth
   - Return to overworld

6. DEFEAT
   - Game over screen or revival mechanic (TBD)
```

---

## 4. Command Menu

### Attack
- Basic physical attack against one enemy.
- Damage = ATK stat - enemy DEF stat (with variance).
- Always available.

### Skill (Magic)
- Special abilities that cost MP.
- Father: limited skill set, powerful single-target or self-buff abilities.
- Son's party: diverse skills across members (heals, buffs, AoE, debuffs).
- Skill list grows with level.

### Item
- Use consumable items from inventory.
- Healing herbs, antidotes, attack items.
- Shared inventory across party.

### Defend
- Reduce incoming damage by 50% this turn.
- Useful for surviving big enemy attacks.
- Father uses this more often (solo survivability).

### Flee
- Attempt to escape battle.
- Success based on speed vs enemy speed.
- Cannot flee from boss battles.

---

## 5. Stats

Core stats for all combatants (player and enemy):

| Stat | Abbrev | Purpose |
|------|--------|---------|
| Hit Points | HP | Health. Reaches 0 = KO. |
| Magic Points | MP | Resource for skills. |
| Attack | ATK | Physical damage dealt. |
| Defense | DEF | Physical damage reduced. |
| Speed | SPD | Turn order + flee chance. |
| Level | LV | Progression tier. Determines stat growth. |

Minimal stat set. No elemental affinities or resistance tables for the
prototype. Those can be layered on later.

---

## 6. Enemy Design

For the prototype, keep enemies simple:

- Each enemy has: name, HP, ATK, DEF, SPD, EXP reward, gold reward.
- Enemies select actions from a weighted action table (e.g., 70% attack,
  20% skill, 10% defend).
- Enemy sprites are static illustrations (or placeholder colored shapes
  for now).
- 3-4 enemy types for the prototype:
  - **Slime** — weak, tutorial enemy. Attacks only.
  - **Bandit** — moderate. Can attack or defend.
  - **Wolf** — fast, low HP. Attacks twice sometimes.
  - **Boss: Stone Guardian** — high HP/DEF, has a charge attack pattern.

---

## 7. Cross-Timeline Combat Effects (Approach 1)

**Confirmed direction:** No direct cross-timeline combat for now.
Father and son never share a battlefield. Instead, the connection is
strategic — father's battles leave lasting effects on enemies in the
son's era.

### Echo Battle: Inherited Scars

When the father defeats or damages certain marked enemies (bosses,
named enemies), the result is recorded as a **scar** — a permanent
debuff on the enemy's counterpart in the son's era.

Examples:
- Father wounds the Stone Guardian's left arm → Son fights the Ancient
  Guardian, whose ATK is permanently reduced.
- Father uses fire on the Forest Beast → Son's version of the beast
  is vulnerable to fire (takes 2x damage).
- Father poisons a dragon → Son's dragon starts battle at 80% HP.

### Implementation

Scars are stored as component data on the enemy entity:

- `C_EnemyScar` component with an array of scar effects.
- Each scar has: `type` (stat_reduction, vulnerability, hp_reduction),
  `stat`, `amount`.
- Father's battles write scars to a shared state.
- Son's enemy spawns read that state and apply scars.

This uses the existing `C_TimelineLinked` pattern — enemies can be
linked across eras just like the boulder/blocked path.

### Future: Approach 2 (Relay Boss Fights)

For later implementation. At key story moments, a boss fight alternates
between eras:
- Father fights solo for N turns (dealing damage, applying scars).
- Scene cuts to son's party finishing the fight.
- Boss HP and status carry across.
- Each era uses its own combat system (solo vs party).

### Future: Approach 3 (Convergence Fight)

For the final boss only. Father and son fight together across time.
Father's solo commands and son's party commands interleave on the same
turn order. The most dramatic moment in the game. Build this last.

---

## 8. Battle UI Layout (Web)

The battle screen replaces the normal dual-view layout. When combat
triggers, the active era's view transitions to a battle screen.
The inactive era's view remains visible but dimmed (you can still see
the other timeline while fighting).

```
+------------------------------------------+
|                                          |
|           [ Enemy Sprites Area ]         |
|          Slime A    Slime B    Wolf      |
|                                          |
|------------------------------------------|
|                                          |
|  [ Message Box ]                         |
|  "Father attacks! 12 damage to Slime A." |
|  "Advisor: Watch the wolf — it's fast!"  |
|                                          |
|------------------------------------------|
|  [ Command Menu ]          [ Status ]    |
|  > Attack                  Father        |
|    Skill                   HP: 45/60     |
|    Item                    MP: 12/20     |
|    Defend                  LV: 3         |
|    Flee                                  |
+------------------------------------------+
```

For the son's party, the status panel shows all members:

```
|  [ Command Menu ]          [ Status ]    |
|  > Attack                  Son   HP:80   |
|    Skill                   Ally1 HP:65   |
|    Item                    Ally2 HP:50   |
|    Defend                  Ally3 HP:45   |
|    Flee                                  |
```

---

## 9. Encounter Design

- **Visible enemies on overworld** — no random encounters. Player can see
  and choose to engage or avoid enemies on the tile map.
- **Enemies are entities** with `C_GridPosition` and `C_TimelineEra`, just
  like interactables. Walking into them triggers combat.
- **Respawn:** Enemies respawn when the player leaves and re-enters an area.
- **Boss encounters:** Scripted, non-respawning, story-gated.

---

## 10. Prototype Scope

For the first implementation, build:

1. **Battle screen transition** — entering combat from overworld.
2. **Enemy display** — 1-3 enemies shown as colored shapes (placeholder).
3. **Command menu** — Attack, Defend, Flee only. No skills/items yet.
4. **Turn resolution** — speed-based turn order, damage calculation.
5. **Victory/defeat** — EXP/gold reward, simple game over.
6. **Father solo combat** — one command per turn.
7. **Son party combat** — 3 commands per turn (placeholder party members).
8. **One overworld enemy** — a slime entity on the father's tilemap that
   triggers combat when walked into.

Leave for later:
- Skills/magic system
- Items in combat
- Enemy AI beyond basic attack
- Echo Battle scar system
- Advisor dialogue in combat
- Party banter
- Level up stat growth formulas
- Multiple enemy types

---

## 11. Open Questions

1. **Advisor identity** — who is the advisor? Why do they travel with
   the father? Are they human, spirit, magical artifact?
2. **Son's party members** — who are they? How many (3 or 4 total
   including son)? Connections to father's story?
3. **Encounter balance** — how hard should combat be? DQ is traditionally
   grindy. Do we want that for a web game?
4. **Death penalty** — game over and reload? Lose half gold (DQ style)?
   Respawn at last save point?
5. **Experience curve** — linear, exponential? How fast should levels come?
6. **Equipment system** — weapons/armor that change ATK/DEF? For prototype
   or later?
7. **Exact party size for son** — 3 (son + 2) or 4 (son + 3)?

---

## 12. Reference

- **Dragon Quest I** — solo hero, first-person, menu combat. The template
  for father's era.
- **Dragon Quest III/IV** — party of 4, same first-person system. The
  template for son's era.
- Both use identical battle engines with the only difference being the
  number of command inputs per turn.
