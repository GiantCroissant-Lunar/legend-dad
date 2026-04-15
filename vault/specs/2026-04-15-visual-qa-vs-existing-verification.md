---
date: 2026-04-15
status: open
owner: (undecided)
related:
  - vault/specs/2026-04-15-visual-qa-skill-backend.md
---

# Visual QA vs existing web-build verification

Captures the discussion: does a visual-qa skill add real value on top of the
verification stack we already have, or is it speculative?

## Verification stack we already have

| Tool | Question it answers | Deterministic? |
|---|---|---|
| Playwright e2e (`task test:e2e`) | "Did the element appear / assertion pass?" | Yes |
| Screenshot capture (e.g. commit 63f961e — HUD visual regression) | "Did pixels change?" (if diffed) or "here's a PNG for later" (if archived) | Yes / N/A |
| MCP `get_state` / `poll_events` | "Is entity at (col,row) with state X? Did event Y fire?" | Yes |
| `browser-screenshot` MCP tool | Raw PNG capture — no judgment | N/A |
| `@game-player` skill | Drive the game + assert state via MCP | Yes |

Every one of these answers a question we **knew to ask**. Pixel-diff is
closest to "catch the unexpected", but it fires on *any* change — so either
we re-baseline constantly (losing signal) or it blocks legitimate edits.

## What a visual-qa skill would add

Answers: **"does this look right?"** — where *right* includes things we
never wrote a test for.

Concrete scenarios where the existing stack is silent but visual-qa speaks:

### 1. Legitimate change that broke something else

Tweak `activity_log_panel.gd` colors. Playwright still sees the widget.
Pixel-diff fails because pixels changed (expected) → re-baseline. In the
process, the new layout clipped the minimap. No test catches it.
Visual-qa flags "minimap partially behind activity log panel."

### 2. Intent mismatch vs reference

Reference image shows "warm lantern glow at dusk" for Whispering Woods.
The tileset is placed correctly (e2e passes), but the ambient color is
too cold. Pixel-diff has no reference to compare against.
Visual-qa static mode compares implementation against reference intent.

### 3. Perceptual regressions pixel-diff can't triage

An e2e screenshot shifts 2%. Was that the color tweak we meant, or did
a placeholder magenta leak in? Pixel-diff says "different". Visual-qa
says "pass: color shift as expected" or "fail: placeholder texture at (x,y)."

### 4. Motion sanity (dynamic mode)

Hot-reload `hud-battle` mid-combat. The widget reappears, but damage
numbers are frozen. `poll_events` shows events firing; Playwright passes.
Visual-qa on a 6-frame sequence flags "damage number at (120,340)
unchanged across frames — expected animation."

### 5. Placeholder detection

A TileSet cell never got its texture assigned; Godot renders default grey.
No e2e test asserts "no untextured primitives." Visual-qa's taxonomy
includes placeholder-remnants explicitly.

## What visual-qa is NOT better at

- **Speed.** Playwright runs in seconds; one LLM vision call is 3–10s and
  costs money. Wrong tool for every-commit CI.
- **Reproducibility.** LLM judgments drift between runs; e2e assertions
  don't. Wrong tool for blocking gates.
- **State assertions.** "Player HP is 47" — use `get_state`, not vision.

## Realistic split

- **CI / regression**: Playwright + pixel-diff + `get_state` (the stack
  we have). Fast, deterministic, blocks merges.
- **Iteration verification** (paired with `@web-build-iterate`): after F9
  hot-reload, visual-qa answers *"did the change land well?"* not just
  *"did the change land?"*
- **Pre-merge spot check**: one visual-qa pass against a reference image
  to catch regressions our deterministic tests didn't know to write.

## Honest caveat — is this speculative value?

Until we know whether the HUD iteration loop actually produces bugs that
existing tests miss, visual-qa is speculative. Cheapest way to validate
before committing to a backend + skill port:

1. Next HUD iteration (widget layout / color change), take a
   before/after screenshot.
2. Run both through Claude native vision ad-hoc (no skill yet):
   "compare these, flag anything that looks wrong."
3. If Claude catches something pixel-diff + Playwright missed, the skill
   pays for itself.
4. If not, it's overkill for the current surface area — defer until we
   have more visually-complex content (locations, NPCs, battle VFX).

**This experiment is the right gate before committing to a backend choice
in `2026-04-15-visual-qa-skill-backend.md`.**

## Decision matrix (fill in when deciding)

| Question | Answer |
|---|---|
| Did the ad-hoc experiment find real gaps? | (pending) |
| Is the gap worth 3–10s + API cost per check? | (pending) |
| Which backend? | see backend spec |
| Scope on first port: static only, or static + dynamic + question? | (pending) |
| CI role: advisory warning, or blocking gate? | advisory (default) |
