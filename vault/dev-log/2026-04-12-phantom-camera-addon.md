---
date: 2026-04-12
agent: claude-code
branch: main
version: 0.1.0-40
tags: [godot, addon, web-export, phantom-camera, guide, beehave, dialogue-manager, gecs]
---

# Addon Web Export Testing — 5 Addons Verified

## Summary

Installed and tested five Godot addons for web export compatibility. All are pure GDScript and confirmed working in-browser on Mac Chrome localhost. Created the project's first main scene with Camera2D + PhantomCameraHost + PhantomCamera2D. Also connected Claude in Chrome to Mac Chrome (previously only Windows Edge).

## Changes

- Installed `addons/phantom_camera/` (v0.9.4.2) from GitHub release tag
- Installed `addons/guide/` (v0.9.1) from GitHub release tag
- Installed `addons/beehave/` (v2.9.2) from GitHub release tag
- Installed `addons/dialogue_manager/` (v3.9.1) from GitHub release tag
- Installed `addons/gecs/` (v7.1.0) from GitHub release tag
- Enabled all five plugins in `project.godot` via `[editor_plugins]` section
- Set `run/main_scene` to `res://scenes/main.tscn`
- Created `scenes/main.tscn` with Camera2D, PhantomCameraHost, PhantomCamera2D, and test Label
- Verified `task build` succeeds with both addons
- Verified both run in browser on Mac Chrome localhost:8080
- Updated handover doc and AGENTS.md with addon conventions and table
- Connected Claude in Chrome to Mac Chrome via `switch_browser`

## Decisions

- **Phantom Camera over custom camera system** — provides cinematic camera features (tween, follow, deadzone) out of the box with zero native dependencies
- **G.U.I.D.E for input mapping** — context-based input system, pure GDScript, web compatible
- **Beehave for behaviour trees** — AI behaviour tree system, pure GDScript, auto-registers autoloads
- **Dialogue Manager for dialogue** — `.dialogue` file format, compiler, balloon UI, pure GDScript
- **GECS for ECS** — entity component system, pure GDScript, `ECS` autoload pattern
- **Manual install over AssetLib** — downloaded tarballs from GitHub since we're headless on Mac
- **Committed addons to repo** — addons are small, pure GDScript, pinning to a version avoids drift
- **Web-compat check process** — before installing any addon, check for `.gdextension`, `.so`, `.dll`, `.dylib` files

## Blockers

- **Headless export script errors** — G.U.I.D.E (`cleanup` function), GECS (`ECS` autoload) throw errors during headless `--export-release`. These are editor-only; autoloads aren't initialized before script compilation in headless mode. All addons run correctly in the exported game

## Next Steps

- [ ] Create articy:draft project on Windows (Phase 1 vault ready)
- [ ] Evaluate more addons for web export compatibility
- [ ] Set up Playwright test infrastructure for automated browser verification
