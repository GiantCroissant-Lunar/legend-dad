---
type: curve
status: draft
articy-id: ""
curve_kind: stat_growth
applies_to: father
data_points:
  - {level: 1,  max_hp: 20, max_mp: 8,  atk: 8,  def: 4,  spd: 6}
  - {level: 4,  max_hp: 60, max_mp: 20, atk: 15, def: 10, spd: 8}
  - {level: 5,  max_hp: 48, max_mp: 18, atk: 16, def: 10, spd: 8}
  - {level: 10, max_hp: 95, max_mp: 32, atk: 26, def: 18, spd: 10}
  - {level: 15, max_hp: 150, max_mp: 44, atk: 36, def: 26, spd: 12}
  - {level: 20, max_hp: 220, max_mp: 56, atk: 48, def: 34, spd: 14}
last-agent-pass: "2026-04-16"
---

# Father Stat Growth Curve

Stats per level for the Father character. Intermediate levels are
linearly interpolated. Level 4 matches the current hardcoded
FATHER_STATS (HP 60, MP 20, ATK 15, DEF 10, SPD 8).
