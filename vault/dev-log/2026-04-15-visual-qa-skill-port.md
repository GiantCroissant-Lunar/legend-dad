---
date: 2026-04-15
agent: claude-code
branch: main
version: 0.1.0-278
tags: [dev-log, visual-qa, skill, tooling, follow-up]
---

# Session Dev-Log — Visual-QA Skill Port

Closes the work unblocked by `vault/specs/2026-04-15-visual-qa-skill-backend.md`
and the decision gate dev-log from earlier today.

## What landed

`.agent/skills/04-tooling/visual-qa/` — ported from
`ref-projects/godogen/claude/skills/visual-qa/`. Files:

```
SKILL.md                        adapted — Claude backends, legend-dad context
scripts/
  visual_qa.py                  rewritten on anthropic SDK, Haiku 4.5 default
  static_prompt.md              copied verbatim
  dynamic_prompt.md             copied verbatim
  question_prompt.md            copied verbatim
```

Plus an `INDEX.md` row under `04-tooling`, a `.vqa.log` gitignore, and a
`task skills:sync` to mirror into `.claude/skills/`.

## Backend decision

From the backend spec's four options, went with **Anthropic SDK + Claude
Haiku 4.5 default** — strong-enough vision for 2D HUD/sprite QA at a cost
that tolerates inclusion in an iteration loop. `--model claude-sonnet-4-6`
is available on the script for harder calls.

`--native` mode works without an API key (reads images via the Claude
harness inside a Claude Code session) and is the recommended path when
already inside the agent. The `ANTHROPIC_API_KEY` error from the script
is now friendly and points at `--native` as the alternative.

## Smoke tests (native path)

Three runs against preserved evidence in
`vault/references/visual-qa-experiment/`:

| Mode | Inputs | Expected | Observed |
|---|---|---|---|
| question | before.png + after-15s.png, "compare them" | Flag widget vanish | ✅ Called out Activity Log + Map panels gone, "Ashenmoor" label newly exposed |
| static (broken) | reference=before, shot=after-15s | `fail` with specific issues | ✅ `fail`, Issue 1 + Issue 2 localized to pixel regions |
| static (happy) | reference=before, shot=style-hot-reload-after | `pass` (widget present, color tweak is the intended delta) | ✅ `pass`, no issues, correctly identified the red-tint as intentional |

Third test is the important one — proves the skill doesn't just flag any
pixel difference as a defect. It correctly distinguished "expected style
tweak" from "unexpected widget loss" given the context string.

`.vqa.log` has one entry per run for replay.

## Known limitations (carried over from decision gate)

- Speed: 3–10s per call, not for every-commit CI. Fine for iteration.
- Reproducibility: LLM judgments drift between runs. Advisory, not
  blocking. Pair with deterministic checks (Playwright, pixel-diff,
  `get_state`) for anything that needs to gate a merge.

## Next follow-ups

1. The synced `.claude/skills/visual-qa/` won't show up in an already-open
   Claude Code session — new skills appear on the next start. No action
   for now; next session picks it up.
2. Dynamic mode (frame sequence) is ported but untested. First real
   use-case will probably be a mid-combat hot-reload animation check.
3. `--both` mode (script + native, aggregated verdict) is documented in
   SKILL.md but not exercised yet.

## Files changed

```
.agent/skills/04-tooling/visual-qa/       (new skill, 5 files)
.agent/skills/INDEX.md                    visual-qa row under 04-tooling
.claude/skills/visual-qa/                 mirrored by `task skills:sync`
.gitignore                                .vqa.log
vault/dev-log/2026-04-15-visual-qa-skill-port.md   (this file)
```
