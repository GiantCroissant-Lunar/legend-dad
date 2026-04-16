---
type: meta
---

# Curve Page Frontmatter

Curves define progression data consumed by the Godot leveling system.
Three kinds exist:

## xp_to_level

Maps cumulative XP to level thresholds. The ProgressionManager looks up
the highest level whose `xp_required` the player has reached.

```yaml
curve_kind: xp_to_level
applies_to: father    # "father" or "son"
data_points:
  - {level: 1, xp_required: 0}
  - {level: 2, xp_required: 7}
  - {level: 3, xp_required: 23}
```

## stat_growth

Maps level to stat values. The ProgressionManager interpolates linearly
between declared data points for intermediate levels.

```yaml
curve_kind: stat_growth
applies_to: father
data_points:
  - {level: 1, max_hp: 20, max_mp: 8, atk: 8, def: 4, spd: 6}
  - {level: 5, max_hp: 48, max_mp: 18, atk: 16, def: 10, spd: 8}
```

## monster_scaling

Maps zone difficulty_tier to a level_offset applied to monster base
stats at encounter spawn time.

```yaml
curve_kind: monster_scaling
data_points:
  - {level: 1, level_offset: 0}
  - {level: 5, level_offset: 5}
```
