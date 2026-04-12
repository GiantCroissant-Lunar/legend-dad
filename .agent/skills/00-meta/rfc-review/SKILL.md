---
name: rfc-review
description: "Structured review of game design RFCs with quantitative scoring across 6 dimensions: core loop, progression, economy, player motivation, risk, cross-consistency. Use when reviewing docs/rfcs/ documents, evaluating game design decisions, or checking design health before implementation. Not for code review (use @implementation-review), not for balance numbers (use balance-review later)."
category: 00-meta
layer: governance
related_skills:
  - "@rfc-orchestrator"
  - "@context-discovery"
---

# /rfc-review: Game Design RFC Review

Interactive RFC review with quantitative scoring. Every recommendation includes WHY + concrete alternative. No vague praise.

Inspired by gstack-game's `/game-review`, adapted for RFC-driven development.

---

## Phase 0: Read & Orient

Read the target RFC from `docs/rfcs/`. Extract 5 context anchors:

| Anchor | Status | Found |
|--------|--------|-------|
| Genre & Platform | ✅/❌ | {what was found} |
| Target Session Length | ✅/❌ | {what was found} |
| Monetization Model | ✅/❌ | {what was found} |
| Target Audience | ✅/❌ | {what was found} |
| Design Pillars | ✅/❌ | {what was found} |

For ❌ items, provide best-guess with [inferred] tag.

**Confirm context before proceeding.** For missing anchors, ask ONE question with options and a RECOMMENDATION.

### Mode Selection

Select review mode based on game type:

| Mode | Focus |
|------|-------|
| **PC/Console RPG** (default for ultima-magic) | Core loop depth, mastery curve, narrative, session arc |
| **Mobile/Casual** | Retention, economy, session fit, monetization ethics |
| **Multiplayer/Competitive** | Balance, matchmaking, counterplay |

### Mode Weight Table (PC/Console RPG default)

| Section | Weight |
|---------|--------|
| 1. Core Loop | 30% |
| 2. Progression & Retention | 20% |
| 3. Economy | 10% |
| 4. Player Motivation | 15% |
| 5. Risk Assessment | 10% |
| 6. Cross-Consistency | 15% |

---

## Review Pacing

**After EACH section**, present:
- Section score: `Section {N} — {name}: {score}/10`
- 1-sentence biggest finding
- Options: A) Continue, B) Dig deeper, C) Fast-forward, D) Stop here

**STOP and wait after each section.**

---

## Section 1: Core Loop

Evaluate the nested loop model:

- **Micro loop** (moment-to-moment): Is the core action satisfying? What's the verb?
- **Meso loop** (session): What's the session goal? How long is a session?
- **Macro loop** (progression): What keeps the player coming back?
- **Meta loop** (mastery): What's the long-term aspiration?

Check:
- Loop clarity — can you describe each loop in one sentence?
- Loop depth — does the micro loop have meaningful decisions?
- Loop uniqueness — what differentiates from competitors?
- MDA alignment — do Mechanics produce intended Dynamics and Aesthetics?

**Score: ___/10**

---

## Section 2: Progression & Retention

Evaluate at each retention tier:

| Tier | Question |
|------|----------|
| FTUE | Does the first 5 minutes teach the core loop AND deliver an "aha moment"? |
| D1 | What reason does the player have to come back tomorrow? |
| D7 | What new system/content unlocks by day 7? |
| D30 | What's the long-term aspiration keeping mastery players? |

Check:
- Flow state design — is difficulty curve shaped for flow?
- Skill gates vs content gates vs time gates — which are used and are they appropriate?
- Churn points — where will players most likely quit?

**Score: ___/10**

---

## Section 3: Economy & Monetization

Evaluate currency and reward systems:

- **Currencies** — how many? Are they clear?
- **Sinks & Faucets** — is there a sink for every faucet?
- **Reward schedules** — variable ratio? Fixed interval?
- **Spending tiers** — does economy serve different player types?

Red flags:
- Economy with no sinks (hyperinflation)
- Pay-gated core progression
- Probabilistic rewards with no pity system

**Score: ___/10**

---

## Section 4: Player Motivation & Emotion

Evaluate using Self-Determination Theory (SDT):

| Need | In RFC? | How? |
|------|---------|------|
| Autonomy | ✅/❌ | {meaningful choices} |
| Competence | ✅/❌ | {skill growth} |
| Relatedness | ✅/❌ | {connection} |

Check:
- Bartle type coverage — which player types are served?
- Emotional arc — does the design create tension/release cycles?
- Ludonarrative consonance — do mechanics support the story?

**Score: ___/10**

---

## Section 5: Risk Assessment

Evaluate across 5 categories:

| Risk | Level | Detail |
|------|-------|--------|
| Pillar violation | H/M/L | Does any system contradict design pillars? |
| Scope (Lake vs Ocean) | H/M/L | Is scope achievable? Deep and narrow > shallow and wide. |
| Technical feasibility | H/M/L | Can this be built with current tech stack? |
| Market differentiation | H/M/L | What makes this different from competitors? |
| Retention cliffs | H/M/L | Where does content/system depth run out? |

**Score: ___/10**

---

## Section 6: Cross-RFC Consistency

Cross-validate findings across sections AND across related RFCs:

- Does the combat RFC's difficulty curve match the progression RFC's pacing?
- Does the party RFC's character growth match the dungeon RFC's challenge scaling?
- Does the overworld RFC's exploration match the state machine RFC's transitions?
- Does the UI RFC support all the information needs of combat, dungeon, and overworld?

Flag contradictions invisible within any single RFC.

**Score: ___/10**

---

## Forcing Questions

Minimum 2, routed by RFC maturity:

| RFC State | Focus |
|-----------|-------|
| Early/skeleton | "Describe the core loop in one sentence" / "Who comes back tomorrow?" |
| Detailed | "Have you prototyped this?" / "What breaks at 2x scale?" |
| Post-implementation | "What surprised you in testing?" / "What changed from the RFC?" |

---

## Fix-then-Rescore

When user updates the RFC during review:
1. Re-read updated section
2. Re-score ONLY that section
3. Update running total
4. If final < baseline: **WARN** — fix introduced new problem

---

## Game Design Vocabulary

Use these terms consistently:

- **Core loop, session loop, meta loop** — loop hierarchy
- **FTUE** — First Time User Experience
- **Aha moment** — when the player "gets it"
- **Churn point** — where players quit
- **Sink/faucet** — currency consumption/generation
- **Skill gate** — requires player skill to pass
- **Content gate** — requires content consumption to pass
- **Time gate** — requires real time to pass
- **Flow state** — optimal challenge/skill balance

---

## Completion Summary

```
RFC Review: {RFC name}
═══════════════════════════════════════════════
  Mode: PC/Console RPG

  Section 1 — Core Loop:         _/10  (30%)  → weighted: _.__
  Section 2 — Progression:       _/10  (20%)  → weighted: _.__
  Section 3 — Economy:           _/10  (10%)  → weighted: _.__
  Section 4 — Player Motivation: _/10  (15%)  → weighted: _.__
  Section 5 — Risk Assessment:   _/10  (10%)  → weighted: _.__
  Section 6 — Cross-Consistency: _/10  (15%)  → weighted: _.__
  ─────────────────────────────────────────────
  WEIGHTED TOTAL:                _._/10

Top 3 Deductions:
  1. [Section] [Issue]: -N because [specific reason]
  2.
  3.

  STATUS: DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT
```

## Important Rules

- **ONE question at a time.** Never batch forcing questions.
- **Section transitions mandatory.** Score + pacing options after every section.
- **Push twice max.** Vague answer → push for specifics → still vague → flag, move on.
- **Escape hatch:** "skip ahead" → AUTO-only remaining sections.
- **No code suggestions.** Design review only. Technical → note for @implementation-review.
- **Anti-sycophancy:** Score honestly. A 5/10 with specific deductions is more useful than a polite 8/10.
