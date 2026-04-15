---
date: 2026-04-15
agent: claude-code
branch: main
version: 0.1.0-258
tags: [dev-log, visual-qa, verification, f9, hot-reload, hud]
---

# Session Dev-Log — Visual QA Decision Gate

Ran the ad-hoc experiment called for by
`vault/specs/2026-04-15-visual-qa-vs-existing-verification.md`. The question:
does native vision catch anything `hot-reload.spec.js` + pixel-diff miss?

**Answer: yes — on the first honest attempt.**

## Method

- Created a one-shot Playwright spec (`_experiment-visual-qa.spec.js`, now
  removed) that mirrors `hot-reload.spec.js` but uses a bigger tweak
  (`BG_COLOR` red channel `0.05 → 0.45` instead of `0.05 → 0.10`) and
  captures screenshots: BEFORE, +5s after F9, +15s after F9.
- Preserved evidence at `vault/references/visual-qa-experiment/`.
- Fed all three PNGs to Claude native vision unprimed ("compare these,
  flag anything that looks wrong").

## Findings

Native vision flagged — correctly and immediately — that **both**
`hud-core` widgets (`activity_log_panel` bottom-left, `minimap` top-right
labeled "Map") **vanish after F9 and don't come back** (same at +5s and
+15s, ruling out timing). The intended red-channel shift is invisible
because the panel itself stops drawing.

The existing `hot-reload.spec.js` asserts:
1. Two distinct `hud-core@{hash}.pck` URLs cross the wire.
2. Console contains `manifest reloaded` / `hash` entries.

Both still pass in this scenario. Pixel-diff would flag "things differ"
without saying which things. Native vision said "the activity-log and
minimap are gone."

## Consequences

1. **Visual-qa skill is unblocked for porting.** Backend choice reopens in
   `vault/specs/2026-04-15-visual-qa-skill-backend.md`.
2. **F9 hot-reload likely has a real bug.** Either the larger bytecode delta
   from my tweak breaks `_on_bundle_reloaded`'s re-instantiation path, or
   the path has been silently broken all along and no test pixel-checks
   post-reload. Either way, `hot-reload.spec.js` needs a widget-present
   assertion — filed as a follow-up in the spec.

## Artifacts

| File | Purpose |
|---|---|
| `vault/references/visual-qa-experiment/2026-04-15-before.png` | HUD with activity log + minimap |
| `vault/references/visual-qa-experiment/2026-04-15-after-5s.png` | +5s after F9; both widgets gone |
| `vault/references/visual-qa-experiment/2026-04-15-after-15s.png` | +15s after F9; still gone |
| `vault/specs/2026-04-15-visual-qa-vs-existing-verification.md` | Decision recorded, follow-ups listed |
| `vault/specs/2026-04-15-visual-qa-skill-backend.md` | Status → unblocked |

## No files changed in the runtime

The experiment restored `activity_log_panel.gd` to its original content in
its `finally` block and rebuilt `hud-core` back to the original hash. Only
new content is in `vault/`.
