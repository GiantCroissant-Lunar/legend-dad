# Archon + Hermes operating model for legend-dad

Date: 2026-04-13
Status: initial setup drafted and Hermes profiles created

## Decision summary

For `legend-dad`, use:
- Archon as the outer workflow/process shell
- Hermes as the inner reasoning/implementation worker
- repo Taskfile commands as deterministic validation/build gates

This repo already has the right command surface for a deterministic outer workflow:
- `task setup`
- `task lint`
- `task build`
- `task test:python`
- `task test:server`
- `task test:godot`
- `task test:e2e`
- `task test`

## Hermes profiles created

Two profiles were created for this project:

1. `legend-dad`
   - primary implementation / debugging / validation worker
   - cwd: `/Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad`
   - memory database: `legend_dad`
   - recontext database: `legend_dad_recontext`
   - local skill dir loaded from `.agent/skills/`

2. `legend-dad-world`
   - worldbuilding / lore / vault/spec work
   - cwd: `/Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad`
   - memory database: `legend_dad_world`
   - recontext database: `legend_dad_world_recontext`
   - local skill dir loaded from `.agent/skills/`

Both profiles currently inherit the working model route from the cloned proxy-based setup and have their own SOUL.md files.

The `vampire_recontext` plugin has been patched to read `recontext.persistence` from the active Hermes profile config first, then fall back to older env/default behavior.

## Why two profiles

`legend-dad` has two genuinely different work modes:

### `legend-dad`
Use for:
- Godot gameplay code
- scene / addon integration
- Node WebSocket server work
- debugging
- validation and repair
- Archon-driven implementation workflows

### `legend-dad-world`
Use for:
- `vault/world/`
- `vault/specs/`
- `vault/plans/`
- lore, quest, faction, event, and world consistency work
- design-first sessions that should not contaminate implementation memory

## Repo rules the setup must respect

From `AGENTS.md`:
- docs belong in `vault/`, not `docs/`
- Godot binary defaults to `/Users/apprenticegc/Work/lunar-horse/tools/Godot.app/Contents/MacOS/Godot`
- web export goes through `task build`
- implementation sessions should use repo-local skills in `.agent/skills/`
- run `@context-discovery` before implementation work
- run `@validation-guard` after implementation work
- every session writes a `vault/dev-log/` entry

## Role split

### Archon owns
- workflow order
- deterministic shell stages
- retry loops
- validation gates
- stop/approval points
- issue/feature/release workflow standardization

### Hermes owns
- context discovery
- RFC/spec interpretation
- implementation planning
- code changes
- review
- repair after failures
- local subagent delegation when helpful

### Repo tooling owns
- linting
- test execution
- web export
- server start/serve commands
- artifact generation

## Recommended first Archon workflows

An actual first workflow file now exists at:
- `.archon/workflows/legend-dad-release-validate.yaml`
- `.archon/workflows/legend-dad-bugfix.yaml`
- `.archon/workflows/legend-dad-feature.yaml`

Start with three workflows only:

1. `legend-dad-bugfix`
2. `legend-dad-feature`
3. `legend-dad-release-validate`

Do not start with PR automation, multi-branch fanout, or release publishing.

## Recommended validation order

Use the narrowest useful checks first.

General default order:
1. `task lint`
2. targeted tests (`task test:godot` or `task test:server`)
3. broader tests if needed (`task test` or `task test:e2e`)
4. `task build`

Notes:
- `task test:e2e` requires a web build and is more expensive
- `task build` is the canonical web export path and should be near the end unless the task specifically targets export behavior

## Workflow 1: legend-dad-bugfix

Use when the user has:
- a broken test
- a runtime error
- a build failure
- a server/game integration regression
- an E2E failure

Suggested shape:

1. Archon passes the bug report / failure log to Hermes (`legend-dad`)
2. Hermes runs repo-local context discovery and localizes the likely subsystem
3. Hermes makes the smallest safe repair
4. Archon runs the narrowest validation step first:
   - server bug -> `task test:server`
   - Godot bug -> `task test:godot`
   - general formatting/lint issue -> `task lint`
5. If still failing, Archon sends exact failure output back to Hermes
6. Hermes repairs again
7. Archon reruns validation
8. Optional final `task build` if the fix touches export-sensitive behavior

## Workflow 2: legend-dad-feature

Use when adding gameplay, UI, server protocol, tools, or pipeline features.

Suggested shape:

1. Archon invokes Hermes (`legend-dad`) to:
   - load `AGENTS.md`
   - use `@context-discovery`
   - interpret the relevant spec/RFC or user request
2. Hermes produces a concise implementation plan
3. Hermes implements the change
4. Archon runs appropriate validations:
   - `task lint`
   - `task test:godot` and/or `task test:server`
   - `task build`
   - `task test:e2e` when browser behavior matters
5. On failure, Archon sends logs back to Hermes for repair
6. Hermes performs a review pass
7. Human approval / next action

## Workflow 3: legend-dad-release-validate

Use for deterministic repo health and release checking.

Suggested shape:

1. `task setup`
2. `task lint`
3. `task test:python`
4. `task test:server`
5. `task test:godot`
6. `task build`
7. `task test:e2e`
8. summarize artifacts, failures, and release readiness

## Hermes invocation model inside Archon

Use the `legend-dad` profile for implementation stages.

Suggested command style:

```bash
hermes --profile legend-dad chat -q "<stage-specific instruction>"
```

Keep prompts narrow by stage:
- one planning prompt
- one implementation prompt
- one repair prompt
- one review prompt

Use `legend-dad-world` only for world/spec/lore/documentation stages.

```bash
hermes --profile legend-dad-world chat -q "<world/spec instruction>"
```

## Hermes team pattern inside a stage

If Hermes needs multiple specialists, let Hermes do inner delegation while Archon stays at the outer workflow layer.

Recommended inner team pattern for `legend-dad`:
- controller Hermes session
- implementer subagent
- spec/repo-rule reviewer
- quality reviewer

Do not make both Archon and Hermes perform the same decomposition role at the same level.

Correct layering:
- Archon = macro orchestration
- Hermes = micro orchestration within a stage

## Starter pseudo-workflow: feature

This is intentionally structural, not exact Archon syntax.

```yaml
name: legend-dad-feature
inputs:
  - task_description

stages:
  - id: implement
    type: ai
    command: |
      cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad && \
      hermes --profile legend-dad chat -q "
      Implement: ${TASK_DESCRIPTION}
      Follow AGENTS.md.
      Run context-discovery before implementation and validation-guard after.
      Summarize changed files and likely risks.
      "

  - id: lint
    type: shell
    command: |
      cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad && task lint
    on_failure: repair

  - id: targeted_tests
    type: shell
    command: |
      cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad && task test:godot
    on_failure: repair

  - id: build
    type: shell
    command: |
      cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad && task build
    on_failure: repair

  - id: review
    type: ai
    command: |
      cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad && \
      hermes --profile legend-dad chat -q "
      Review the current implementation for AGENTS.md compliance, integration risk, export risk, and missing validation.
      "

  - id: repair
    type: ai
    command: |
      cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad && \
      hermes --profile legend-dad chat -q "
      The previous validation stage failed.
      Use the exact failure output from Archon to repair the issue with minimal changes.
      "
```

## Recommended first implementation order

1. Build `legend-dad-release-validate` first
   - easiest to prove
   - mostly deterministic
   - validates Archon shell integration with this repo

2. Build `legend-dad-bugfix` second
   - validates failure capture -> Hermes repair -> retry

3. Build `legend-dad-feature` third
   - highest prompt complexity

## Operational commands

Useful direct invocations:

```bash
hermes --profile legend-dad chat
hermes --profile legend-dad-world chat
hermes profile show legend-dad
hermes profile show legend-dad-world
```

## Follow-ups worth doing next

1. Decide whether to keep recontext persistence file-backed or wire true SurrealDB-backed supervisor state for legend-dad. Important: the current supervisor reads `SURREALDB_*` env vars, not Hermes `memory.provider_config`, so DB-backed supervisor state needs explicit env wiring or a code patch.
2. Add project-specific profile notes or extra disabled skills once real usage patterns emerge
3. Expand the Archon workflow set beyond the first real file at `.archon/workflows/legend-dad-release-validate.yaml`
4. Record the first real Archon/Hermes run in `vault/dev-log/`

## Final operating rule

For `legend-dad`, Archon should orchestrate the workflow and deterministic gates, while Hermes performs the actual reasoning, implementation, review, and repair using the `legend-dad` profile; `legend-dad-world` stays reserved for world/spec/lore work.
