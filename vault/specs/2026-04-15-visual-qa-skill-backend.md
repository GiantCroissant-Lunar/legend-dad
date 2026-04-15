---
date: 2026-04-15
status: open
owner: (undecided)
---

# Visual QA skill — backend decision

## Context

`ref-projects/godogen/claude/skills/visual-qa/` is a good fit for legend-dad's e2e
testing workflow (Playwright already captures screenshots; pairing with an
LLM judge would catch layout/color/placement regressions that screenshot-diff
tools miss).

The godogen skill defaults to **Gemini Flash** (`gemini-3-flash-preview`) with
an optional `--native` mode that reads images via the Claude harness. We won't
use Gemini.

## Decision needed

Pick the Python-script backend that replaces Gemini before bringing the skill
into `.agent/skills/04-tooling/visual-qa/`.

## Options

1. **Anthropic SDK, Claude Haiku 4.5 default** — cheap enough for loops, strong
   vision, stays in the Anthropic ecosystem.
2. **Anthropic SDK, Sonnet 4.6 default** — higher fidelity, higher cost per run.
3. **OpenAI SDK, GPT-4o-mini default** — similar cost to Haiku, different family.
4. **Drop the external script, keep only `--native` mode** — skill invokes Claude
   via the Read tool in a forked context. Works only inside Claude Code.

## Considerations

- Legend-dad already assumes Claude Code as the harness; `--native` would be
  friction-free in-session but unusable from CI / non-Claude agents.
- Haiku 4.5's vision is strong enough for 2D sprite/HUD QA from cold experience
  on similar tasks, but confirm before locking in.
- Whatever we pick, keep the `--model` override flag so we can escalate per-run.
- Update `static_prompt.md`, `dynamic_prompt.md`, `question_prompt.md` copy if
  the wording references "Gemini" anywhere.

## Next action

When this is resolved, port the skill, update `.agent/skills/INDEX.md` under
`04-tooling`, and add a dev-log entry. Source files:

```
ref-projects/godogen/claude/skills/visual-qa/
├── SKILL.md
└── scripts/
    ├── visual_qa.py        # rewrite backend
    ├── static_prompt.md
    ├── dynamic_prompt.md
    └── question_prompt.md
```
