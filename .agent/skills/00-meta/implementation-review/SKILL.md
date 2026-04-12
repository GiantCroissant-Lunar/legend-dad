---
name: implementation-review
description: "Three-pass code review for PRs and code changes: Pass 0 checks design intent survival against RFCs, Pass 1 catches critical issues (frame budget, memory, state sync, serialization), Pass 2 flags informational findings. Use when reviewing a PR, branch diff, or code change. Not for RFC review (use @rfc-review), not for feel evaluation (requires playable build)."
category: 00-meta
layer: governance
related_skills:
  - "@rfc-orchestrator"
  - "@validation-guard"
  - "@context-discovery"
---

# /implementation-review: Code Quality + Design Intent Survival

Three-pass review for game code changes. **Pass 0** checks whether RFC design intent survived implementation. **Pass 1** catches critical code issues. **Pass 2** flags informational findings.

Every finding is triaged **AUTO/ASK/ESCALATE** before presenting.

Inspired by gstack-game's `/gameplay-implementation-review`.

---

## Step 0: Diff Scope Analysis

Determine the diff to review:
- If on a feature branch: diff against `main`
- If reviewing specific commits: use the commit range
- If reviewing a package: focus on that package's files

```
BASE → HEAD: {N} files, {LOC} lines changed
```

### Scope Classification

| Diff Size | LOC | Review Depth |
|-----------|-----|-------------|
| Small | <50 | Pass 0 + Pass 1 only |
| Medium | 50-199 | All three passes |
| Large | 200+ | All three passes + adversarial |

**Confirm scope before proceeding.**

---

## Pass 0: Design Intent Survival

**Skip if no RFC exists for this feature.** Otherwise, read the relevant RFC from `docs/rfcs/` and check:

### §0.1 — RFC Acceptance Criteria
For each acceptance criterion in the RFC, verify it's implemented. Flag:
- Missing criteria (not implemented at all)
- Partial criteria (partially implemented without explanation)
- Extra scope (implemented beyond RFC without justification)

### §0.2 — Soul Preservation
Every RFC has a core design intent. Is the "soul" of the design preserved?
- Does the implementation capture the mechanic's intended feel?
- Are the critical constraints from the RFC respected?

### §0.3 — Scope Boundaries
- Over-scope: implementing SHOULD/COULD items before all MUST items are done
- Under-scope: missing MUST items

### §0.4 — Value Consistency
Do gameplay values in code match RFC-specified values? (damage, timing, distances, etc.)
Cross-reference with ScriptableObject configs where applicable.

### §0.5 — Silent Experience Changes
Refactors or "cleanup" that alter gameplay feel without design discussion:
- Changed timing constants
- Reordered state transitions
- Modified input handling sensitivity

**Present Pass 0 findings. Each ASK item one at a time.**

---

## Pass 1: Critical Issues

Six subsections. Each finding must cite specific code.

### 1.1 — Frame Budget
- Allocations in Update/Tick loops
- LINQ in hot paths
- Unbounded iteration (foreach over growing collections)
- Missing object pooling for frequently spawned objects

### 1.2 — Memory
- Missing IDisposable on classes holding subscriptions
- R3 subscriptions without `.AddTo()` — **mandatory rule from @unity-r3-reactive**
- MessagePipe subscriptions not disposed
- Event handler registration without deregistration

### 1.3 — State Synchronization
- Race conditions in async state transitions
- Fire-and-forget `.Forget()` on operations that need ordering
- Missing `_isTransitioning` guards
- CancellationToken not propagated — **mandatory rule from @unity-unitask**

### 1.4 — Serialization
- Direct editing of .prefab/.unity/.asset files — **mandatory rule from @unity-asset-edit**
- Missing `[SerializeField]` on fields that should be configurable
- Hardcoded gameplay values — **mandatory rule from @unity-configurable-data**

### 1.5 — Input
- Using legacy `Input` class — **mandatory rule from @unity-input-system**
- Using coroutines — **mandatory rule from @unity-unitask**
- Using uGUI Canvas — **mandatory rule from @unity-uitoolkit**

### 1.6 — Architecture
- Service Locator pattern — **mandatory rule from @unity-vcontainer**
- Missing constructor injection (using `[Inject]` attribute instead of constructor)
- Circular package dependencies via asmdef references

**Present AUTO-fixed summary, then each ASK item one at a time. ESCALATE items stop review.**

---

## Pass 2: Informational

Only after Pass 1 resolved.

### 2.1 — Data-Driven Design
- Values that should be in ScriptableObjects but are hardcoded
- Missing `[CreateAssetMenu]` on data definitions
- Missing `[Tooltip]` on serialized fields

### 2.2 — Organization
- Namespace doesn't follow `UltimaMagic.*` convention
- Package ID doesn't follow `com.giantcroissant.*` convention
- Code in wrong package (feature leak across package boundaries)

### 2.3 — Testing
- Public service methods without test coverage
- Async tests using `.Forget()` instead of `await`
- Missing test doubles for MessagePipe publishers/subscribers

### 2.4 — Performance
- Observable chains that could use `.DistinctUntilChanged()`
- Using `CompositeDisposable` where `DisposableBag` would suffice
- Missing `AwaitOperation` on async operators

### 2.5 — Dead Code
- Unused usings, unreachable branches, commented-out code
- TODO comments without tracking

**Present findings. Ask: continue to adversarial (if Large), or done?**

---

## Adversarial Pass (Large diffs only)

Review the diff from three adversarial perspectives:
1. **Cheater** — can any state be manipulated client-side?
2. **Crash tester** — what happens with null/empty/max values?
3. **Speedrunner** — can any sequence be skipped or broken?

---

## Action Triage

### AUTO — fix silently
Import ordering, formatting, unused vars, simple naming, obvious missing `.AddTo()`.

### ASK — one at a time
Architecture decisions, performance tradeoffs, gameplay logic vs RFC, API changes, design intent mismatches from Pass 0.

### ESCALATE — stop immediately
- Security vulnerability or cheat vector
- Data loss risk
- Core system change with no tests
- 3+ interconnected issues suggesting wrong abstraction
- Soul of mechanic destroyed by implementation
- Mandatory rule violations that affect multiple files

---

## Pass Transitions

After each pass: present summary, ask before continuing.

```
Pass 0 complete. {N} design intent findings.
Pass 1 complete. {N} critical issues.
A) Continue to Pass 2
B) Skip to summary
C) Launch adversarial
```

**STOP at each transition.**

---

## Completion Summary

```
Implementation Review
================================
  Branch: ___  Commit: ___  Diff: ___ LOC
  RFC: {found/none}

  Pass 0 — Design Intent:  ___ findings
  Pass 1 — Critical:       ___ issues (___ AUTO, ___ ASK, ___ ESCALATE)
  Pass 2 — Informational:  ___ issues
  Adversarial:              [SKIPPED | ___ findings]

  Mandatory Rules Checked:
    [ ] No hardcoded gameplay values
    [ ] No legacy Input class
    [ ] No coroutines
    [ ] No direct .prefab/.unity edits
    [ ] No uGUI Canvas
    [ ] No Service Locator
    [ ] All subscriptions disposed
    [ ] CancellationToken propagated

  STATUS: DONE / DONE_WITH_CONCERNS / BLOCKED
```

## Important Rules

- **Pass 0 first.** Design intent violations are more important than code style.
- **AUTO fix silently, ASK one at a time, ESCALATE stops review.**
- **Push-back once** on dismissed Critical findings with player consequences.
- **Never redesign.** "This should be pooled" = review. "Here's how to pool it" = implementation.
- **Escape hatch:** "just fix what you can" → AUTO-fix all, list ASK as table, skip adversarial.
