---
type: meta
---

# Bestiary Page Mechanical Frontmatter

Every bestiary entry carries both narrative prose (Overview, Ecology,
Behavior, Lore, Creative Prompts) AND mechanical data in frontmatter.
The mechanical layer feeds `EnemyDefinition` .tres resources in Godot
via the vault -> articy -> canonical pipeline.

## Required fields

```yaml
battle_stats:
  max_hp: 30            # integer >= 1
  max_mp: 0             # integer >= 0
  atk: 12               # integer >= 0
  def: 8                # integer >= 0
  spd: 6                # integer >= 1
  level: 2              # DQ1-style flat level (NOT scaled -- see curves)
  xp_reward: 15
  gold_reward: 10

actions:
  - id: "crystal_slash"         # unique within this bestiary entry
    kind: "attack"              # "attack" | "spell" | "status_inflict"
    frequency: 0.7              # 0.0-1.0; weights within the entry's action roll
    power_min: 4
    power_max: 8
    target_kind: "enemy"
    status_effect: "paralysis"  # optional -- applies status on hit

  - id: "resonance_pulse"
    kind: "status_inflict"
    frequency: 0.3
    status_effect: "paralysis"
    target_kind: "all_enemies"

group_size_min: 3
group_size_max: 6

zone_affinity:
  - "[[Iron Peaks Upper Mines]]"
  - "[[Iron Peaks Trail]]"
```

## Action frequencies

`frequency` fields within a bestiary's `actions` array are normalized
(don't have to sum to 1). The battle system picks one action per
enemy-turn using weighted random.

## Status effect ids

Must match a case in `BattleManager._apply_status_effect`. Current set:
`sleep`, `poison`, `paralysis`, `stopspell`. New ids require a matching
case before the action is usable.
