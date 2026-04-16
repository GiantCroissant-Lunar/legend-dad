---
type: meta
---

# Zone Page Mechanical Frontmatter

## encounter_table

Weighted monster pool for this zone. The battle system rolls once per
encounter trigger using `weight` for probability, filtered by `era`.

```yaml
encounter_table:
  - bestiary: "[[Crystal Crawler]]"   # vault wikilink to a bestiary entry
    weight: 3                         # integer >= 1, relative weight
    era: "son"                        # "father" | "son" | "both"
  - bestiary: "[[Slime]]"
    weight: 5
    era: "both"

encounter_rate: 0.15   # 0.0-1.0; probability per player-step of triggering an encounter
difficulty_tier: 2     # 1-10; feeds monster level scaling in Phase 2B
```

## Era gating

`era: "father"` -- only rolls during the Father timeline.
`era: "son"` -- only rolls during the Son timeline.
`era: "both"` -- rolls in both eras (but individual stats may differ
via monster-scaling in Phase 2B).

## Encounter-free zones

Omit `encounter_table` entirely for towns / safe zones.
Set `encounter_rate: 0` to explicitly mark as safe.
