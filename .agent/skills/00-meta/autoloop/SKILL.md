---
name: autoloop
description: Use when setting up autonomous agent iteration — keep/discard cycle with git-as-state-machine, context window management, and simplicity-weighted evaluation.
category: 00-meta
layer: governance
related_skills:
  - "@rfc-orchestrator"
  - "@validation-guard"
  - "@context-discovery"
  - "@skill-creator"
  - "@unity-mcp"
---

# Autoloop — Autonomous Iteration Protocol

This skill defines the **autonomous loop pattern** for iterative agent work. It is not a standalone workflow — other skills invoke it as a protocol when they need to run an iterative keep/discard cycle.

Inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch): the insight is that you don't write Python to orchestrate the agent — you write a Markdown file (this one) that the agent follows autonomously.

## Core Principles

1. **NEVER STOP** — Once in a loop, do not pause to ask the human. Run until the goal is met, a hard blocker is hit, or the human interrupts.
2. **Keep or discard** — Every iteration produces a measurable result. If it improves the metric, keep (commit). If it regresses, discard (reset).
3. **Git is the state machine** — Branch tip = current best state. No databases, no experiment trackers.
4. **Protect the context window** — Redirect verbose output to files. Extract only what you need via grep.
5. **Simplicity wins** — A small improvement with ugly complexity is not worth keeping. Removing code for equal results is a win.

## The Loop

```
SETUP:
  1. Create branch: autoloop/<tag> from current HEAD
  2. Establish baseline metric (compile, test, validate — whatever the loop measures)
  3. Log baseline to results.tsv

LOOP (repeat until goal met or hard blocker):
  1. Check state       — git status, read_console, @context-discovery (light)
  2. Plan change       — pick ONE focused change (not multiple)
  3. Implement          — make the change
  4. Commit            — git add + commit (so we can reset if needed)
  5. Measure           — run the metric (compile, test, validate)
  6. Evaluate          — compare to previous best
  7. Decide:
     - KEEP:    metric improved or equal with less complexity → advance
     - DISCARD: metric regressed or equal with more complexity → git reset --hard HEAD~1
     - CRASH:   attempt fix (max 3 tries), then skip and reset
  8. Log              — append to results.tsv
  9. GOTO 1
```

## Context Window Management

Long-running loops will exhaust the context window if output is not managed. Follow these rules:

### Redirect verbose output
```bash
# WRONG — floods context
uv run python train.py

# RIGHT — captures to file, extracts only metrics
uv run python train.py > run.log 2>&1
grep "^val_bpb:\|^peak_vram_mb:" run.log
```

### Unity-specific redirects
```
# WRONG — read_console returns everything
read_console()

# RIGHT — filter to only errors
read_console(filter_type="Error")

# For large scene hierarchies, page instead of dumping
manage_scene(action="get_hierarchy", page_size=50)
```

### What to keep in context
- Current metric value and previous best
- What you just tried and whether it worked
- The next idea to try

### What to redirect to files
- Full compilation output
- Test runner output
- Scene hierarchy dumps
- Console logs
- Stack traces (read only the relevant portion)

## Results Logging

Every loop must maintain a results log. Use TSV for simplicity (git-friendly, grep-friendly):

```
# results.tsv — NOT committed to git (add to .gitignore)
commit	metric	status	description
abc123	baseline	keep	Initial state before loop
def456	0.95	keep	Added GridService caching
ghi789	0.93	discard	Tried parallel loading — slower
jkl012	0.96	keep	Simplified tile lookup
```

Columns depend on what the loop measures:
- **Implementation loops**: commit, compiles, tests_pass, violations, status, description
- **Optimization loops**: commit, metric_value, memory, status, description
- **Eval loops**: commit, pass_rate, tokens, duration, status, description

## Branching Strategy

```
main
 └── autoloop/rfc001-grid          ← implementation loop
 └── autoloop/rfc002-statemachine  ← implementation loop
 └── autoloop/skill-tuning-mcp    ← eval loop
```

- Each loop gets its own branch
- Branch tip always represents the best state achieved so far
- On completion, the branch can be merged to main (or PR'd)
- If abandoned, the branch preserves all progress

## Keep/Discard Criteria

### For Implementation Loops (@rfc-orchestrator)
```
KEEP if:
  - Compiles cleanly (zero errors)
  - @validation-guard passes (all checks)
  - Moves closer to RFC completion
  - Does not increase complexity without clear benefit

DISCARD if:
  - Compilation errors (after 3 fix attempts)
  - @validation-guard fails on BLOCK-level violations
  - Introduces unnecessary abstraction
  - Breaks existing functionality
```

### For Eval Loops (@skill-creator)
```
KEEP if:
  - pass_rate improved OR equal with fewer tokens/time
  - No regressions on previously passing assertions

DISCARD if:
  - pass_rate decreased
  - Token usage increased >20% for same pass_rate
  - Previously passing assertions now fail
```

### For Optimization Loops
```
KEEP if:
  - Metric improved (even slightly)
  - Equal metric with less code (simplicity wins)

DISCARD if:
  - Metric regressed
  - Equal metric with more code
  - Improvement < noise threshold
```

## Crash Handling

When a loop iteration crashes (compilation error, runtime exception, tool failure):

1. **Read the error** — tail the log, extract the relevant portion
2. **Classify**:
   - **Fixable bug** (typo, missing import, wrong parameter): attempt fix, max 3 tries
   - **Fundamentally broken idea** (wrong approach, incompatible API): skip immediately
   - **Environment issue** (MCP disconnected, Unity not responding): pause loop, notify human
3. **After fix attempts**:
   - If fixed: continue (the fix counts as part of this iteration)
   - If not fixed: `git reset --hard HEAD~1`, log as `crash`, move on

## Simplicity-Weighted Evaluation

Not all improvements are equal. Before keeping a change, ask:

```
COMPLEXITY COST:
  - How many lines were added/removed? (net negative is a win)
  - How many new abstractions were introduced? (fewer is better)
  - Would another developer understand this change in 30 seconds?

IMPROVEMENT VALUE:
  - How much did the metric improve?
  - Is this improvement real or noise?
  - Does this unlock future improvements?

DECISION:
  - Big improvement + any complexity    → KEEP
  - Small improvement + no complexity   → KEEP
  - Small improvement + high complexity → DISCARD (not worth it)
  - No improvement + less complexity    → KEEP (simplification is valuable)
  - No improvement + more complexity    → DISCARD
```

## Integrations

### With @rfc-orchestrator
The orchestrator's phase loop invokes autoloop for each implementation step:
```
For each RFC task in the current phase:
  AUTOLOOP: implement → compile → validate → keep/discard
```

### With @validation-guard
Validation runs as the "measure" step inside every implementation loop iteration.

### With @skill-creator
The eval loop is an autoloop where the metric is pass_rate:
```
AUTOLOOP: modify skill → run evals → grade → keep/discard
```

### With @unity-mcp
MCP provides the measurement tools (read_console, screenshots, test results).
Context window management rules apply especially to MCP output.

## When NOT to Use Autoloop

- **Exploratory work** — When you don't know what metric to optimize yet
- **Design decisions** — When the human needs to make subjective choices
- **First implementation** — When there's no baseline to compare against (run setup first)
- **Destructive operations** — When mistakes can't be undone with git reset
