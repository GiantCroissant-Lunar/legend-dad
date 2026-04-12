---
name: world-refiner
description: "Iteratively score and improve world bible vault pages against 8 quality metrics. Use after world-writer generates drafts, or to batch-improve existing pages."
category: 05-world
layer: world
related_skills:
  - "@world-writer"
  - "@lore-checker"
---

# World Refiner

Autonomous iterative improvement loop for world bible vault pages. Scores pages against measurable quality metrics, identifies weaknesses, fixes them, and re-scores until all dimensions pass.

## Quality Metrics (8 dimensions)

| # | Metric | How to Measure | Pass Threshold |
|---|--------|---------------|----------------|
| 1 | **Link Coverage** | Count `[[links]]` in content | ≥ 3 for characters/locations, ≥ 2 for lore/bestiary |
| 2 | **Timeline Consistency** | Cross-check dates/events against `world/history/timeline.md` | 0 contradictions |
| 3 | **Name Consistency** | All proper nouns match spelling across referenced pages | 0 mismatches |
| 4 | **Creative Prompt Completeness** | Required prompt types present per page type | All required types present |
| 5 | **Creative Prompt Quality** | Each prompt ≥ 100 chars, includes art style prefix for visual prompts | All prompts pass |
| 6 | **Section Completeness** | All sections from the prompt template are present | All required sections |
| 7 | **Tone Consistency** | No game-design jargon (stat blocks, dice notation, variable names) | 0 violations |
| 8 | **Connection Reciprocity** | If page A links to B, does B link back to A? | ≥ 80% reciprocal |

### Required Creative Prompts by Type

| Page Type | Required Prompts |
|-----------|-----------------|
| character | portrait, voice, theme-music |
| location | environment-art, ambience, music |
| faction | emblem, theme-music, color-palette |
| event | scene-art, sound-design |
| lore | concept-art (if visual), music (if atmospheric) |
| quest | scene-art, music, sound-design |

### Tone Violations (patterns to flag)

- Dice notation: `1d6`, `2d8`, `d10`
- Stat references: `HP`, `AC`, `THAC0`, `STR 16`, `INT modifier`
- Variable names: `GameProgress.`, `Quest.`, `Party.`
- Mechanical language: "saving throw", "spell slot", "damage roll"
- Design-speak: "the player", "game mechanic", "UI element"

## Process

1. **Score** — read the page, evaluate all 8 metrics, produce a score card
2. **Prioritize** — rank FAIL > WARN > PASS, pick the highest-priority issue
3. **Fix** — modify the page to address the issue
4. **Re-score** — evaluate the changed page
5. **Accept/Reject** — if score improved, keep the change; if not, revert
6. **Repeat** — go to step 2 until all PASS or max iterations reached

## Score Card Format

```
## Score Card: [page path]

| # | Metric | Status | Detail |
|---|--------|--------|--------|
| 1 | Link Coverage | PASS | 5 links (min 3) |
| 2 | Timeline Consistency | PASS | 0 contradictions |
| 3 | Name Consistency | WARN | "Academy of Starlight" vs "Starlight Academy" in line 24 |
| 4 | Creative Prompt Completeness | PASS | 3/3 present |
| 5 | Creative Prompt Quality | FAIL | portrait prompt is 47 chars (min 100) |
| 6 | Section Completeness | PASS | 6/6 sections |
| 7 | Tone Consistency | PASS | 0 violations |
| 8 | Connection Reciprocity | WARN | sera.md links to elder-aldric.md but not vice versa |

**Result: 5 PASS / 2 WARN / 1 FAIL**
**Priority fix: #5 Creative Prompt Quality — expand portrait prompt**
```

## Iteration Limits

- **Default max iterations:** 5 per page
- **Batch mode:** process all pages, 5 iterations each
- **Stop early:** if all 8 metrics PASS
- **Escalate:** if a FAIL persists after 3 attempts, report it instead of retrying
