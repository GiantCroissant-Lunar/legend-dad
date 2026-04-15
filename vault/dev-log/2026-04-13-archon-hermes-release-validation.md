---
date: 2026-04-13
agent: codex
branch: main
version: 0.1.0-144
tags: [archon, hermes, godot, workflow, validation, bugfix, tooling]
---

# Archon + Hermes release validation and workflow hardening

## Summary

Validated the `legend-dad` Archon + Hermes operating model end to end against the live repo instead of relying on assumptions. Fixed the Hermes invocation form in Archon, pinned Python tooling to the repo’s required interpreter, hardened Godot validation so script errors fail the workflow for real, fixed the GUIDE autoload/export issue, and confirmed `legend-dad-release-validate` completes with `anyFailed:false`.

Also hardened the live `legend-dad-feature` and `legend-dad-bugfix` workflows to use explicit required input (`FEATURE_REQUEST` / `BUG_REPORT`) plus the same deterministic validation chain as the release workflow. Related architecture notes live in [[architecture/2026-04-13-archon-hermes-operating-model]].

## Changes

No commits were made in this session. Files changed:

- `.archon/config.yaml`
- `.archon/workflows/legend-dad-release-validate.yaml`
- `.archon/workflows/legend-dad-feature.yaml`
- `.archon/workflows/legend-dad-bugfix.yaml`
- `Taskfile.yml`
- `scripts/run_godot_checked.py`
- `project/hosts/complete-app/project.godot`
- `project/hosts/complete-app/addons/guide/plugin.gd`
- `vault/architecture/2026-04-13-archon-hermes-operating-model.md`

Validation evidence gathered during the session:

- `archon workflow run legend-dad-release-validate --cwd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad`
- `task lint`
- `task test:python`
- `task test:server`
- `task test:godot`
- `task build`
- `archon validate workflows --cwd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad`

## Decisions

- Use Archon as the deterministic outer workflow shell and Hermes as the inner reasoning/implementation worker for `legend-dad`.
- Use the absolute profile alias path `/Users/apprenticegc/.local/bin/legend-dad` inside Archon bash nodes; `hermes --profile legend-dad ...` was not reliable in Archon/worktree shell context.
- Honor the repo’s declared Python 3.11+ policy by pinning Taskfile Python commands to `/Users/apprenticegc/.pyenv/versions/3.13.4/bin/python3` instead of ambient `python3`.
- Do not trust raw Godot exit codes for build/test gates; route Godot commands through `scripts/run_godot_checked.py` so `SCRIPT ERROR`, parse errors, compile errors, and failed script loads become real task failures.
- Make `GUIDE` a real `[autoload]` entry in `project.godot` and stop the GUIDE editor plugin from dynamically adding/removing that singleton. This removed headless export parse errors caused by bare `GUIDE` references during script parsing.
- Make `legend-dad-feature` and `legend-dad-bugfix` explicitly require shell-provided input (`FEATURE_REQUEST` / `BUG_REPORT`) rather than relying on undocumented Archon runtime interpolation.
- Treat Archon’s final success footer as non-authoritative unless the run also shows `anyFailed:false` and no `dag_node_failed` lines.

## Blockers

- Archon 0.3.6 can print `Workflow completed successfully.` and exit 0 even when DAG nodes failed earlier. This was worked around operationally by checking DAG log state, not just the footer.
- Godot export/test commands can emit real script compile/load errors while still exiting 0. This is now mitigated by `scripts/run_godot_checked.py`.
- `task build` still prints non-fatal Godot exit warnings about leaked `ObjectDB` instances/resources. These did not block the validated build after the GUIDE fix but should be investigated later if they become noisy or symptomatic.
- The working tree contains many unrelated pre-existing modifications outside this session, so this session intentionally stopped short of committing.

## Next Steps

- [ ] Run the patched `legend-dad-feature` workflow with a real `FEATURE_REQUEST` value.
- [ ] Run the patched `legend-dad-bugfix` workflow with a real `BUG_REPORT` value.
- [ ] Optionally package the proven Archon + Hermes + Taskfile + checked-Godot pattern into a reusable template under `project-agent-union`.
- [ ] Decide whether to commit the Archon/Hermes/Godot workflow hardening separately from the repo’s unrelated existing changes.
