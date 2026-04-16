---
type: curve
status: draft
articy-id: "72057594037930512"
curve_kind: monster_scaling
applies_to: ""
data_points:
  - {level: 1, level_offset: 0}
  - {level: 2, level_offset: 1}
  - {level: 3, level_offset: 2}
  - {level: 4, level_offset: 3}
  - {level: 5, level_offset: 5}
  - {level: 6, level_offset: 7}
  - {level: 7, level_offset: 9}
  - {level: 8, level_offset: 12}
last-agent-pass: "2026-04-16"
---

# Monster Scaling Curve

Maps zone difficulty_tier to a level_offset. At encounter spawn,
the monster's base level (from bestiary) is increased by this offset.
Higher-tier zones produce tougher monsters.

Tier 1 (Thornwall) = no scaling. Tier 5 (Iron Peaks) = +5 levels.
