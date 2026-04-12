---
name: validation-guard
description: Post-implementation verification — checks Godot project, server code quality, mandatory rule compliance, and linting. Run AFTER completing any implementation work to catch violations before committing.
category: 00-meta
layer: governance
always_active: false
related_skills:
  - "@rfc-orchestrator"
  - "@context-discovery"
  - "@autoloop"
---

# Validation Guard

Run this skill **after** completing implementation work. It verifies that code meets project standards and catches violations before they're committed.

## When to Run

- After implementing a feature
- After modifying server packages
- After any significant code change
- Before committing (final gate)

## Validation Checks

### Check 1: Linting

```
JS/TS (biome):
  cd project/server && pnpm run lint
  Pass: Zero errors
  Fail: List all errors — fix before proceeding

Python (ruff):
  ruff check scripts/
  Pass: Zero errors
  Fail: List all errors — fix before proceeding

GDScript:
  Check for syntax errors via: $GODOT_PATH --headless --path project/hosts/complete-app --check-only
  Pass: Clean exit
  Fail: List errors
```

### Check 2: Mandatory Rules

Scan all new/modified files for violations:

| Rule | Scope | Grep Pattern | Fix |
|---|---|---|---|
| No hardcoded server ports | JS | Literal port numbers in logic | Use env vars or config |
| No console.log in production | JS | `console\.log` in non-dev files | Use structured logger |
| No var declarations | JS | `\bvar\b` | Use `const` or `let` |
| No any types | TS (future) | `: any` | Use proper types |
| No unused imports | Python | ruff F401 | Remove import |
| No bare except | Python | `except:` without type | Catch specific exceptions |

### Check 3: Server Package Structure

For any new or modified package under `project/server/packages/`, verify:

```
packages/<name>/
├── package.json    (required — name, version, main, scripts)
├── src/
│   └── index.js    (required — entry point)
└── nodemon.json    (if dev server)
```

### Check 4: Godot Project Integrity

```
Checks:
- [ ] project.godot parses without errors
- [ ] export_presets.cfg has Web preset
- [ ] No .godot/ cache files staged in git
- [ ] Scene files (.tscn) reference valid scripts
```

### Check 5: Build Verification

```
Quick build check:
  task build
  Pass: Build completes, files in build/_artifacts/{version}/web/
  Fail: Export errors — check Godot output
```

### Check 6: Pre-commit Dry Run

```
pre-commit run --all-files
Pass: All hooks pass
Fail: List failures — hooks may auto-fix, re-stage and retry
```

## Validation Report Format

```markdown
## ValidationReport — [date]

### Linting: PASS/FAIL
| Linter | Status | Issues |
|---|---|---|
| biome | PASS | — |
| ruff | PASS | — |

### Mandatory Rules: PASS/FAIL
| Rule | Status | Violations |
|---|---|---|
| No hardcoded ports | PASS | — |
| No console.log | PASS | — |
| ... | ... | ... |

### Package Structure: PASS/FAIL
[missing files if any]

### Godot Integrity: PASS/FAIL
[issues if any]

### Build: PASS/FAIL
[errors if any]

### Pre-commit: PASS/FAIL
[failures if any]

### Overall: PASS/FAIL
[summary of what needs fixing]
```

## Severity Levels

- **BLOCK**: Must fix before committing (lint errors, build failures, mandatory rule violations)
- **WARN**: Should fix but won't break builds (missing tests, incomplete docs)
- **INFO**: Suggestions for improvement (naming, organization)

## How to Execute

| Check | Tool/Command |
|---|---|
| JS/TS lint | `cd project/server && pnpm run lint` |
| Python lint | `ruff check scripts/` |
| Godot check | `$GODOT_PATH --headless --path project/hosts/complete-app --check-only` |
| Build | `task build` |
| Pre-commit | `pre-commit run --all-files` |
| Git diff | `git diff --name-only` for modified files scope |

## Inline Mode (for @autoloop iterations)

When called inside an autoloop iteration, run a **lightweight inline check**:

```
INLINE VALIDATION (fast — for each loop iteration):
  1. Linting — biome + ruff on CHANGED FILES ONLY
  2. Mandatory rules — grep only the FILES CHANGED in this iteration
  3. Pre-commit dry run on staged files
  Skip: build verification, full Godot check
  (these run in full validation at loop end)

RETURN:
  - PASS: no blockers found
  - BLOCK: list violations (autoloop will attempt fix or discard)
  - WARN: list warnings (autoloop will keep but log)
```

## Related Skills

- `@autoloop` (00-meta) — invokes validation as the measure step in each loop iteration
- `@context-discovery` (00-meta) — run before implementation
- `@rfc-orchestrator` (00-meta) — determines what was supposed to be built
