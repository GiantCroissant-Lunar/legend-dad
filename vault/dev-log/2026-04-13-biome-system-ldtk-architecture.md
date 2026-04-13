---
type: dev-log
date: 2026-04-13
agent: claude-opus-4.6
version: 0.1.0
tags: [biome, ldtk, tileset, architecture, comfyui, town]
---

# Biome System & LDtk Multi-File Architecture

## Summary

Designed and documented the biome/tileset system that connects vault, articy, LDtk, and ComfyUI. Also completed the articy import of all 21 entities and wrote back articy IDs to vault.

## Commits

- `4598438` feat: import 21 entities into articy and write back IDs to vault
- (this commit) feat: add biome system — field, dungeon, town definitions with IntGrid vocabulary

## What Was Done

### Articy Import (completed)
- Fixed stale quicktype types — added `zone` to TypeEnum in generated C#/Python
- Rebuilt MDK plugin, imported all 21 entities into articy
- Wrote articy IDs back to 14 vault pages via `task articy:writeback`
- Re-ran `task articy:prep` — all entities now show `status: unchanged`

### Biome System (new)
- Created `vault/world/biomes/` with 4 files:
  - `_conventions.md` — universal IntGrid 0-9, LDtk architecture, pipeline overview
  - `field.md` — IntGrid 10-19 for forest/wilderness (Whispering Woods)
  - `dungeon.md` — IntGrid 20-29 for caves/mines (Iron Peaks)
  - `town.md` — IntGrid 30-39 for settlements + building interiors (Thornwall)
- Added `biome`, `palette`, `palette-source`, `ldtk-file` to all 4 location frontmatter files
- Added `biome` field to all 7 zone frontmatter files

### Architecture Decisions
1. **LDtk multi-file**: One world-overview.ldtk + one .ldtk per location (zones as levels within)
2. **Open-top buildings**: Town interiors visible directly on the map, no screen transitions. Buildings = wall tiles forming rooms with interior floor inside. Inspired by Eastward / CrossCode.
3. **Vault as single source of truth**: Biome defs, palettes, IntGrid values all defined in vault. Articy, LDtk, ComfyUI derive from it.
4. **Lospec palettes**: Each location gets a palette from lospec.com, recorded in vault frontmatter.
5. **64-128 tiles per biome**: Minimal viable tileset for first pass.

### IntGrid Design
- Universal (0-9): void, ground, wall, water, pit, door, stairs, bridge
- Field (10-19): tall grass, bush, tree, cliff, paths, stream, undergrowth
- Dungeon (20-29): cave floor/wall, lava, mine track, cracked floor, ore, crystal, ice, dark
- Town (30-39): cobblestone, fence, garden, stall, well, building wall, interior floor, counter, furniture

## Decisions & Rationale

| Decision | Why |
|---|---|
| Multiple .ldtk files | JRPGs grow to 30-100+ zones; one file gets unwieldy. Per-location files enable parallel work and independent Godot loading |
| Open-top buildings | Simpler than roof-hide mechanic, no interior screen transitions, modern indie JRPG feel |
| Merged town + interior biome | Open-top buildings mean no separate interior maps, so one biome covers both |
| Detailed IntGrid slots | 10 values per biome gives enough functional vocabulary without being overwhelming |

## Blockers / Open Items

1. **Palette selection** — all locations have `palette: ""`. Need to browse lospec.com and pick palettes
2. **LDtk restructure** — `ldtk_sync.py` currently generates one file. Needs updating for multi-file architecture
3. **ComfyUI integration** — biome prompt templates written but no workflow yet
4. **Era tile variants** — father vs son era needs palette swaps + some dedicated variant tiles (boarded stalls, dead trees, etc.)

## Next Steps

1. Select lospec palettes for each location
2. Update `ldtk_sync.py` to generate per-location .ldtk files with biome IntGrid values
3. Generate first tileset with ComfyUI (field biome as easiest starting point)
4. Set up auto-rules in LDtk mapping IntGrid values to themed tiles
