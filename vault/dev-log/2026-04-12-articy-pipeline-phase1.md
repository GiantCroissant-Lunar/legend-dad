---
date: 2026-04-12
agent: claude-code
branch: main
version: 0.1.0-39
tags: [articy, pipeline, world-building, infrastructure]
---

# Session: Articy Pipeline Phase 1 — 2026-04-12

## Summary

Designed and implemented the vault-side infrastructure for an articy:draft import pipeline. The pipeline uses Obsidian vault as the narrative source of truth, articy:draft as the structural game database, and exports canonical JSON for Godot, ComfyUI, LDtk.

## Key Decisions

- **Layered source of truth:** vault (narrative) → articy (structural) → JSON (game-ready)
- **One-way sync:** vault → articy only, no reverse flow
- **Approach C:** agent skills + Python scripts handle complexity, MDK plugin stays thin
- **Schema-driven contracts:** JSON Schema + quicktype generates C#/Python types
- **One canonical export + adapters:** single JSON from articy, tool-specific adapters for ComfyUI/LDtk/Godot
- **Articy MDK is free** even in articy:draft X FREE — confirmed from articy's own docs

## Commits (15 on feature branch, merged to main)

- Vault directory scaffold (8 entity type dirs + timeline stub)
- Conventions document (frontmatter schema, section requirements)
- Import manifest JSON Schema (vault → articy contract)
- vault_to_manifest.py with TDD (20 tests, 232 lines)
- Taskfile tasks (articy:prep, articy:types, articy:validate)
- quicktype-generated C# and Python types
- Sample character page (Sera) with E2E verification
- Updated all 5 world-building agent skills for legend-dad
- Design spec + implementation plan

## Files Created/Modified

- `vault/specs/2026-04-12-articy-mdk-pipeline-design.md` — design spec
- `vault/plans/2026-04-12-articy-pipeline-phase1.md` — implementation plan
- `vault/world/` — full directory scaffold with conventions
- `project/articy/` — schemas, generated types, import manifest
- `scripts/vault_to_manifest.py` — core parser
- `tests/` — conftest + 20 tests
- `Taskfile.yml` — 3 new tasks
- `.agent/skills/05-world/` — 5 skills updated

## Blockers

None for Phase 1.

## Next Steps

1. **Create articy:draft project on Windows** — define entity templates matching vault types
2. **Phase 2: MDK plugin** — thin C# import/export plugin
3. **Phase 2: Canonical export schema** — depends on articy templates
4. **Phase 2: Adapter scripts** — ComfyUI, LDtk, Godot adapters
5. **Content authoring** — populate vault/world/ with actual game content
