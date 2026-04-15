---
date: 2026-04-15
status: decided — proceed with port
owner: (undecided)
related:
  - vault/specs/2026-04-15-visual-qa-skill-backend.md
  - vault/references/visual-qa-experiment/
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

## Experiment — 2026-04-15

Ran the cheapest honest test: one-shot Playwright spec
(`_experiment-visual-qa.spec.js`, since removed) that captures a BEFORE
screenshot, applies a controlled `BG_COLOR` tweak to
`activity_log_panel.gd` (red channel `0.05 → 0.45`), rebuilds `hud-core`,
presses F9, and captures AFTER screenshots at +5s and +15s. Screenshots
preserved under `vault/references/visual-qa-experiment/`.

Then fed all three PNGs to Claude native vision unprimed — "compare these,
flag anything that looks wrong."

### What native vision caught

Not the intended color shift. Both widgets in `hud-core` — the
`activity_log_panel` (bottom-left) and the `minimap` (top-right labeled
"Map") — **vanish after F9 and never come back** (still gone at +15s, so
not a timing artifact). Before.png has both; after-5s and after-15s have
neither.

Nothing else in the frame changed: tilemap, top-left HUD text,
"Haven Town" label, `hud-battle` preview on the right, and the floating
"Ashenmoor" label all render identically.

### What the existing stack said

`hot-reload.spec.js` runs the **same** F9 flow (with a smaller red-channel
tweak, `0.05 → 0.10`) and passes. It asserts:

1. Two distinct `hud-core@{hash}.pck` URLs cross the wire.
2. Console contains `manifest reloaded` / `hash` entries.

Both assertions would still pass even with invisible widgets. No pixel-diff
baseline exists for the HUD post-F9.

### Interpretation

Native vision caught a regression the deterministic stack is structurally
blind to. Either:
- F9 hot-reload has a latent re-instantiation bug that only fires with
  certain tweaks (plausible — my tweak produces different `.gdc` bytecode
  than the small-delta tweak the e2e uses), **or**
- F9 has been silently breaking widgets all along and no test ever looks
  at pixels post-reload.

Either way, the value case is proven. Visual-qa is not speculative.

## Decision matrix

| Question | Answer |
|---|---|
| Did the ad-hoc experiment find real gaps? | **Yes** — widgets disappearing after F9, invisible to `hot-reload.spec.js`. |
| Is the gap worth 3–10s + API cost per check? | Yes for iteration verification and pre-merge spot checks. Not for every-commit CI. |
| Which backend? | See `2026-04-15-visual-qa-skill-backend.md` — unblocked to decide. |
| Scope on first port | Static mode first (compare reference vs rendered). Dynamic + question modes as follow-up once we actually use static. |
| CI role | Advisory, never blocking. |

## Follow-ups filed by the experiment

1. **Investigate F9 widget re-instantiation regression.** Reproduce with
   both the small (e2e) and large (experiment) tweaks. If only the large
   tweak triggers it, root-cause the difference (probably resource cache,
   bundle metadata, or the `CACHE_MODE_REPLACE_DEEP` code path). If both
   trigger it, `hot-reload.spec.js` has been green under a real bug since
   it landed.
2. **Add a pixel / widget-count assertion to `hot-reload.spec.js`.**
   Minimum: after F9, assert that activity-log + minimap are still drawn
   (either via pixel sample of known regions, or by querying the Godot-side
   scene tree over WS for the expected nodes).
3. **Port visual-qa skill with Claude Haiku 4.5 backend** (subject to the
   backend spec) — the static-mode use case is proven.
