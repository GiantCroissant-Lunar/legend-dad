---
name: visual-qa
description: Visual quality assurance — analyze game screenshots for defects, compare against reference, check motion in frame sequences. Backed by Claude Haiku 4.5 vision by default; supports native Claude vision and aggregated mode. Use when a visual change needs a second opinion that pixel-diff or Playwright can't provide.
category: 04-tooling
layer: tooling
related_skills:
  - "@web-build-iterate"
  - "@game-player"
---

# Visual QA

$ARGUMENTS

CRITICAL: Your job is to find problems, not confirm things look fine. Do not rationalize, justify, or explain away what you see. If it looks wrong, report it.

## When This Applies

You have screenshots from the running game (headed Playwright, a manual F9 capture, `@web-build-iterate` output, etc.) and a deterministic check isn't the right tool:

- Pixel-diff can't explain *why* pixels changed — it only says they did.
- Playwright asserts state you thought to assert — this catches the things you didn't.
- Pair with `@web-build-iterate`: after F9 hot-reload, ask "did the change land well?" not just "did the change land?"

Not a replacement for deterministic CI. Advisory, never blocking.

## Backend

- **Default (Claude via script):** Run the Python script below. All queries go to `claude-haiku-4-5-20251001` — strong enough for 2D HUD/sprite QA, cheap enough to stay inside an iteration loop.
- **`--native`** flag in arguments: Use the Read tool on every image, analyze directly. Do NOT run the script. Use when you're already inside Claude Code and don't want to cross the API boundary.
- **`--both`** flag in arguments: Run the script first, then do native analysis. Aggregate verdicts (details below).
- **`--model claude-sonnet-4-6`** on the script invocation escalates to Sonnet for harder calls (motion, ambiguous dynamic frames, fine-grained layout).

Requires `ANTHROPIC_API_KEY` in the environment when using the script backends.

## Mode Detection

From the arguments — freeform text with file paths:

- Reference image + 1 screenshot → **Static mode**
- Reference image + multiple frames → **Dynamic mode** (frames assumed 0.5s apart, 2 FPS cadence)
- No reference, just a question about screenshots → **Question mode**

## Script Execution

The script lives at `${CLAUDE_SKILL_DIR}/scripts/visual_qa.py`. Always pass `--log .vqa.log`. Print the script output as your response.

```bash
# Static
python3 ${CLAUDE_SKILL_DIR}/scripts/visual_qa.py --log .vqa.log \
  [--context "Goal: ... Requirements: ... Verify: ..."] \
  reference.png screenshot.png

# Dynamic
python3 ${CLAUDE_SKILL_DIR}/scripts/visual_qa.py --log .vqa.log \
  [--context "..."] \
  reference.png frame1.png frame2.png ...

# Question
python3 ${CLAUDE_SKILL_DIR}/scripts/visual_qa.py --log .vqa.log \
  --question "the question" screenshot.png [frame2.png ...]
```

## Native Execution

Read every image file referenced in the arguments using the Read tool. Analyze using the criteria and output format below. Never look at code — only images.

After producing output, append a debug log entry:

```bash
printf '%s\n' "$(cat <<'LOGEOF'
{"ts":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","mode":"MODE","model":"native","query":"QUERY","files":["FILE1","FILE2"],"output":"FIRST_LINE..."}
LOGEOF
)" >> .vqa.log
```

## Aggregated Mode (`--both`)

1. Run the Python script, capture output.
2. Read all images with the Read tool, do native analysis using criteria below.
3. Produce combined verdict:
   - Either says `fail` → `fail`
   - Either says `warning` and neither `fail` → `warning`
   - Both `pass` → `pass`
4. Merge issue lists from both, deduplicate by location + description.
5. Label each issue source: `[script]`, `[native]`, or `[both]`.
6. Log both outputs to `.vqa.log`.

## Analysis Criteria

### Implementation Quality (static + dynamic)

Assets are usually fine — what breaks is how they're placed, scaled, composed:

- Grid/uniform placement when reference shows organic arrangement
- Uniform/default scale when reference shows varied, purposeful sizing
- Flat composition when reference has depth and layering
- Stretched, tiled, or carelessly applied materials
- Objects unrelated to environment (just placed on a flat plane)
- Camera framing doesn't match reference perspective

### Visual Bugs

- Z-fighting (flickering overlapping surfaces)
- Texture stretching, tiling seams, missing textures (magenta/checkerboard)
- Geometry clipping (objects visibly intersecting)
- Floating objects that should be grounded
- Shadow artifacts (detached, through walls, missing)
- Lighting leaks through opaque geometry
- Culling errors (missing faces, disappearing objects)
- UI overlap, truncated text, offscreen elements
- **Missing widgets** (this is the thing visual-qa uniquely caught in the legend-dad decision gate — panel bg rendered as page background means the widget failed to re-instantiate silently)

### Logical Inconsistencies

- Impossible orientations (sideways, upside-down, embedded in terrain)
- Scale mismatches (tree smaller than character, door too small)
- Misplaced objects (furniture on ceiling, rocks in sky)
- Broken spatial relationships (bridge not connecting, stairs into wall)

### Placeholder Remnants

- Untextured primitives contrasting with surrounding detail
- Default Godot materials (grey StandardMaterial3D, magenta missing shader)
- Debug artifacts (collision shapes, nav mesh, axis gizmos)

### Motion & Animation (dynamic mode only)

Compare consecutive frames (0.5s apart):

- Stuck entities (same position/pose across frames when movement expected)
- Jitter/teleportation (large position jumps between frames)
- Sliding (position changes but pose frozen — ice-skating)
- Physics breaks (objects through walls, endless bouncing, unnatural acceleration)
- Animation mismatches (walk anim at running speed, idle while moving)
- Camera issues (sudden jumps, clipping through geometry)
- Collision failures (overlapping objects that should collide)

## Output Format

### Static / Dynamic

```
### Verdict: {pass | fail | warning}

### Reference Match
{1-3 sentences: does the game capture the reference's *intent* — placement logic, scaling, composition, camera? Distinguish lazy implementation (fail) from asset/engine limitations (acceptable).}

### Goal Assessment
{1-3 sentences from Task Context. "No task context provided." if none.}

### Issues

{If none: "No issues detected." Otherwise:}

#### Issue {N}: {short title}
- **Type:** style mismatch | visual bug | logical inconsistency | motion anomaly | placeholder
- **Severity:** major | minor | note
- **Frames:** {dynamic only: which frames}
- **Location:** {where in frame}
- **Description:** {1-2 sentences}

### Summary
{One sentence.}
```

Severity: major/minor = must fix. note = cosmetic, can ship.

### Question Mode

```
### Answer
{Direct, specific, actionable answer. Reference locations, frames, colors, objects.}

### Visual Evidence
{What in the screenshots supports the answer. Reference specific frames and locations.}
```
