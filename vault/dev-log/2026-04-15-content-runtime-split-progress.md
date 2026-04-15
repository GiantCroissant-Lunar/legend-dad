---
date: 2026-04-15
agent: claude-code
branch: feature/content-runtime-split
version: 0.1.0-content-runtime-split.1
tags: [dev-log, content-runtime-split, godot, pck, refactor, progress]
---

# Session Dev-Log — Content/Runtime Split Migration (in progress)

Live progress log for the [2026-04-15 content/runtime split spec][spec] and [implementation plan][plan]. Updated as phases complete. Records findings that weren't in the plan so the spec/plan can be amended afterwards.

[spec]: ../specs/2026-04-15-content-runtime-split-design.md
[plan]: ../plans/2026-04-15-content-runtime-split.md

## Phase Status

| Phase | Status | Commits |
|---|---|---|
| 1 — Cross-platform link infrastructure | ✅ done | `ae290ce`, `7628aa9`, `8ce1305`, `b661846`, `8a2d974`, `887c94e` |
| 2 — shared/ skeleton + relocation | ✅ done | `b95b672`, `d12bfd3`, `6d8b560`, `a7309e1`, `6cd841d`, `f94129c`, `7bf49a2` |
| 3 — shared lib (enums + Resources + contract) | in progress | — |
| 4 — content-app project.godot autoloads | pending | — |
| 5 — Manifest schema + ContentManager autoload | pending | — |
| 6 — Bundle packager + content:* taskfile targets | pending | — |
| 7 — Boot scene with safe fallback | pending | — |
| 8 — Preview harness in content-app | pending | — |
| 9 — hud-core bundle migration end-to-end | pending | — |
| 10 — Web build serves PCKs over HTTP | pending | — |
| 11 — AGENTS.md + dev-log update | pending | — |

## Findings Not in the Plan

These all surfaced during execution and were resolved inline. The plan should be amended (or a follow-up commit applied to it) to incorporate them before the next agent picks up the spec.

### F1 — Stale Windows junctions silently bypass cleanup (Phase 1, addressed in `7628aa9`)

`Path.is_symlink()` returns False for Windows junctions, and `Path.exists()` follows the link and returns False when the target is gone. The plan's draft cleanup guard (`if link_path.is_symlink() or link_path.exists()`) would skip a stale junction entirely, then `mklink /J` would fail because the entry is still in the directory.

**Fix applied:** replace guard with `os.path.lexists(str(link_path))`. `lexists` does not dereference; works for stale symlinks AND stale junctions. Compatible with Python 3.11 (`Path.is_junction()` is 3.12+).

**Plan amendment needed:** Task 1.2's `setup_shared_links.py` snippet should use `os.path.lexists` from the start.

### F2 — `subprocess.run(check=True, capture_output=True)` swallows mklink errors (Phase 1, addressed in `7628aa9`)

When `mklink /J` fails, `CalledProcessError` exposes `returncode` but not the stderr text. Windows users see `CalledProcessError: returncode=1` with no diagnostic.

**Fix applied:** capture explicitly, raise `SystemExit(f"mklink /J failed for {link_path} -> {target_dir}: {result.stderr.strip()}")`.

**Plan amendment needed:** same task snippet.

### F3 — `.gitignore` directory patterns don't match symlinks (Phase 2, addressed in `6cd841d`)

`project/hosts/complete-app/addons/` (with trailing slash) only matches a directory, not a symlink-to-directory. After `task share:link`, git showed every link as untracked.

**Fix applied:** drop trailing slash on link-path entries:
```
project/hosts/complete-app/addons          # not addons/
project/hosts/complete-app/lib
…
```

**Plan amendment needed:** Task 1.6's `.gitignore` block must omit trailing slashes for the 9 link paths.

### F4 — `setup_shared_links.py` requires content-app to exist before any links can be created (Phase 2, addressed in `a7309e1`)

The script iterates `LINKS` in order. When it hit the first `content-app` entry and the directory didn't exist, it `SystemExit`'d — but it had already created the 4 complete-app links, leaving partial state.

Worse: `content-app/` was uncommitted in main (only the user's local stub). Branching from `5135d4f` for the worktree dropped it entirely.

**Fix applied:** committed a minimal content-app stub (`a7309e1`) so share:link sees both host projects. Phase 4 will populate the autoloads later.

**Plan amendment needed (two parts):**
- Phase 2 needs an explicit step "ensure `project/hosts/content-app/project.godot` is committed (minimal stub)" BEFORE Task 2.4 (run `task share:link`).
- `setup_shared_links.py` should validate ALL hosts in a pre-pass before creating any links — this is filed as a future improvement (TODO below) but isn't urgent now that content-app exists.

### F5 — GUIDE addon `_enable_plugin` mutates autoloads at runtime, breaking headless mode (Phase 2, addressed in `f94129c`)

The vendored GUIDE addon's `plugin.gd` calls `add_autoload_singleton("GUIDE", …)` from `_enable_plugin`. In editor mode this re-adds the autoload that's already statically declared in `project.godot [autoload]` — no harm done. In headless mode (`task test:godot`, `task build`) plugins never enable, so the autoload registration never happens via that path. `project.godot` does declare GUIDE statically, so headless *should* work — but Godot then sees a script that fails to parse because GUIDE's own internal types (`GUIDEActionMapping`, `GUIDERemappingConfig`, etc.) aren't registered, and the entire autoload load fails. Cascade: every script that references `class_name`'d types breaks (90+ parse errors observed).

The user already had this fix as uncommitted WIP in main. The worktree (branched from clean HEAD) didn't carry it.

**Fix applied:** make `_enable_plugin` and `_disable_plugin` no-ops; rely on the static `[autoload]` entry in `project.godot`. Committed inside `project/shared/addons/guide/plugin.gd`.

**Plan amendment needed:** Phase 2 should explicitly call out the GUIDE plugin patch as a prerequisite for headless mode. AGENTS.md (Phase 11) should mention this so future addon updates don't reintroduce the regression.

### F6 — `.godot/uid_cache.bin` must exist before headless commands work (Phase 2, addressed in `7bf49a2`)

`project.godot` uses UID-form autoload references like `BeehaveGlobalMetrics="*uid://c3ktl6ontsdt7"`. UIDs only resolve when `.godot/uid_cache.bin` exists. The cache is gitignored (correctly — it's machine-local). On a fresh clone there is no cache, so `task test:godot` and `task build` fail with "Unrecognized UID" → autoload load failure → cascading parse errors.

The cache is populated by an editor scan. Headless `--editor --headless --quit` performs the scan AND exits cleanly.

**Fix applied:** new `task setup:godot` runs the editor headlessly for each host project to populate the cache. Wired into `task setup` so a fresh clone gets it automatically.

**Plan amendment needed:** add `task setup:godot` to Phase 2 verification step (Task 2.4) and to the verification checklist at the bottom of the plan.

## Process Findings

### Subagent dispatch overhead is real but worth it for net quality

Phase 1 took ~2 implementer dispatches per task pair, ~1 spec reviewer, ~1 code-quality reviewer, plus 1 fix dispatch when reviewers found a critical issue. Each pair felt slow but the code-quality reviewer caught a Critical bug (F1 above) on the very first task — exactly the kind of stale-junction issue that wouldn't have surfaced on Mac CI but would have broken every Windows dev's first `task setup`. That alone justified the methodology for the rest of the migration.

For very small config-edit tasks (e.g. Phase 1.5+1.6, Phase 2.4-style verification), inline review by the controller was sufficient; the skill discipline allows this when the diff is genuinely trivial and easy to read.

### Worktree isolation worked exactly as advertised

The user's main checkout has ~20 modified files (including the GUIDE plugin WIP that turned out to be load-bearing). Branching the worktree from a clean HEAD meant the migration ran in true isolation. Discovering F5 in the worktree was actually useful — it forced us to make the GUIDE fix explicit and committed rather than inheriting it as silent local state.

## Future Improvements Worth Filing

(Out of scope for this migration; do not block on these.)

- `setup_shared_links.py` should validate every entry's prerequisites in a pre-pass before creating any links, so partial state can never result.
- A pre-commit / CI check that compares the autoload list across `complete-app/project.godot` and `content-app/project.godot` to catch kernel-set drift.
- The .uid files Godot generates are currently untracked (matches main's habit). At some point we should decide whether to commit them for build reproducibility or document why they stay out.
- AGENTS.md needs a "Cross-platform development" section explaining that Windows uses junctions (not symlinks), why, and how `task share:link` handles it.
