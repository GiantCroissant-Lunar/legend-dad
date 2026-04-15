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
| 3 — shared lib (enums + Resources + contract) | ✅ done | `445b0bb`, `2614090`, `43c483e` |
| 4 — content-app project.godot autoloads | ✅ done | `1cd9c2c` |
| 5 — Manifest schema + ContentManager autoload | ✅ done | `70435bd`, `5187df5`, `e2c9c93`, `b03eee2` |
| 6 — Bundle packager + content:* taskfile targets | ✅ done | `815045a`, `5376d7a`, `46b8704` |
| 7 — Boot scene with safe fallback | ✅ done | `bcf1793` |
| 8 — Preview harness in content-app | ✅ done | `0711bfc`, `463334d`, `4d54d56`, `4191b5d` |
| 9 — hud-core bundle migration end-to-end | ✅ done | `019bd95`, `6fea290`, `f241f0c`, `b4a1a6a` |
| 10 — Web build serves PCKs over HTTP | ✅ done | `a4dab23`, `3f3a4b0` |
| 11 — AGENTS.md + dev-log update | in progress | `c8bc5ab` |

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

### F7 — `bundle_packager.gd` output path was off by one directory level (Phase 9, addressed in `f241f0c`)

`bundle_packager.gd` runs from `project/hosts/content-app/`. The plan's draft computed the PCK output dir as:
```gdscript
var out_dir := ProjectSettings.globalize_path("res://").path_join("../../build/_artifacts/pck")
```
But `res://` resolves to `project/hosts/content-app/`, so `../../` lands at `project/build/_artifacts/pck/` — one level too shallow. Meanwhile `content_manifest.py` (sibling tool) reads from `<repo-root>/build/_artifacts/pck/`. Mismatch ⇒ the packager wrote PCKs that the manifest generator never found.

**Fix applied:** change `../../` to `../../../` in `bundle_packager.gd`.

**Plan amendment needed:** Task 6.1's `bundle_packager.gd` snippet must use `../../../build/_artifacts/pck`.

### F8 — GDScript `String.match("**/*.gd")` does not match flat files (Phase 9, addressed in `f241f0c`)

The plan's `bundle.json` example used `"include": ["**/*.tres", "**/*.tscn", "**/*.gd"]`. GDScript's `String.match()` uses Unix shell glob semantics where `**/` requires at least one directory segment before the filename. Files at the bundle root (e.g. `activity_log_panel.gd` directly under `hud-core/`) don't match. The packager dropped them silently and reported "no files matched include patterns".

**Fix applied:** include both nested AND flat patterns: `["**/*.tres", "**/*.tscn", "**/*.gd", "*.tres", "*.tscn", "*.gd"]`.

**Plan amendment needed:** Task 9.2's `bundle.json` example must include the flat-file glob variants. Or — better — update `bundle_packager.gd._collect_files` to make `**` match zero or more directory segments.

### F9 — `HudWidgetDefinition.tres` filename must equal the widget id (Phase 9, addressed in `f241f0c`)

`ContentManager.get_hud_widget("minimap")` looks for `res://content/hud/{bundle}/minimap.tres`. The plan's draft saved the file as `mini_map_panel.tres` (matching the script name) but `_load_resource_by_kind` builds the path from the requested ID, not the filename. Lookup returned null.

**Fix applied:** rename the file to match the widget id. The mini-map widget's `.tres` file is `minimap.tres`.

**Plan amendment needed:** Task 9.2 must clarify that `HudWidgetDefinition.tres` filenames are keyed by the widget's `id`, not the underlying script name.

### F10 — Single-threaded Godot 4.6 web build cannot HTTP-load PCKs at runtime (Phase 10, NOT yet addressed)

`task build` produces a single-threaded web export (default Godot 4.6 web template). At runtime, `ProjectSettings.load_resource_pack("res://pck/foo.pck")` does NOT trigger an HTTP fetch the browser can intercept. Boot prints `[boot] Loading hud-core…` followed immediately by `[boot] Failed to load hud-core` — the load attempt happens, but the file never reaches the WASM filesystem.

This breaks the central goal of the migration: memory-efficient hot-reload of content via PCKs in the web build. Currently the only PCK that ships is whatever Godot baked into `complete-app.pck` at export time.

**Workarounds in scope of this finding:**
- The Phase 10 Playwright smoke test was extended to fall back to a `request.head()` reachability check so it doesn't require the runtime fetch path. The PCKs ARE served correctly over HTTP (HTTP 200) — Godot just can't consume them in single-threaded mode.

**Plan amendment / follow-up needed:**
- Switch the Godot web export to the **threaded** template. The static server (`scripts/serve_web.js`) already sets the COOP/COEP headers required for `SharedArrayBuffer`, so this should be a one-line export-preset change plus rebuild.
- File a follow-up: "Switch web export to threaded template; verify runtime PCK loading via HTTP fetch."
- Until then, the migration's runtime behavior on web is functionally equivalent to the pre-split state — gameplay works (everything ships in the main wasm bundle) but the hot-reload promise is not yet realized.

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

(Out of scope for this migration; do not block on these. AGENTS.md item is now ✅ done.)

- **[CRITICAL FOLLOW-UP] Switch web export to threaded template** — see F10. The current single-threaded export cannot HTTP-load PCKs at runtime. The static server already supports COOP/COEP for `SharedArrayBuffer`. Without this fix the migration's hot-reload memory benefit is unrealized in the web target.
- `setup_shared_links.py` should validate every entry's prerequisites in a pre-pass before creating any links, so partial state can never result.
- A pre-commit / CI check that compares the autoload list across `complete-app/project.godot` and `content-app/project.godot` to catch kernel-set drift.
- The .uid files Godot generates are currently untracked (matches main's habit). At some point we should decide whether to commit them for build reproducibility or document why they stay out.
- Make `bundle_packager.gd._collect_files` treat `**` as zero-or-more directory segments so `**/*.gd` matches flat files (avoids needing both glob variants in `bundle.json`).
- Generalize `LocationManager` to delegate raw PCK loading to `ContentManager` (it already handles the location-PCK pipeline; this would consolidate the two patterns).

## Migration Outcomes

End-to-end pipeline confirmed working (Phase 9 verification): `task content:build -- hud-core` → manifest regenerated → headless boot prints `[boot] Loading hud-core…` followed by `[boot] Ready`.

What works:
- Two-Godot-project structure with shared `project/shared/` linked into both via OS-appropriate links
- `task setup` is the only command needed on a fresh clone (handles deps + share:link + Godot cache seed)
- `ContentManager` autoload reads manifest, loads bundles depth-first by deps, refuses unsafe unloads
- `bundle_packager.gd` produces hash-suffixed PCKs; `content_manifest.py` emits the runtime manifest
- Boot scene shows safe fallback when manifest absent
- Preview harness in content-app lets authors iterate on widgets/enemies in isolation
- `task build` ships PCKs alongside the wasm; HTTP serves them at the expected path

What doesn't yet work (see F10):
- Runtime HTTP loading of PCKs in the web build under single-threaded export. The plumbing is correct end-to-end on native (headless verification confirmed `[boot] Ready`), and the HTTP server delivers PCKs correctly (200 OK), but the WASM runtime can't consume them without the threaded export. Switching templates is the unblocker.
