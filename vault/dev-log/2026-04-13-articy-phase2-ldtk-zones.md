---
type: dev-log
date: 2026-04-13
agent: claude-opus-4.6
tags: [articy, mdk, ldtk, world-building, pipeline, zones]
---

# 2026-04-13 — Articy Phase 2 + LDtk Integration + World Content

## Summary

Implemented the articy MDK import plugin (Phase 2), created world content for the dual-timeline JRPG, built LDtk integration, and introduced the zone entity type that bridges vault content to LDtk levels.

## What Was Done

### 1. Articy MDK Import Plugin (Phase 2)

- Built C#/.NET 8 MDK plugin at `project/articy/mdk-plugin/LegendDad.MdkPlugin/`
- Plugin creates `LD_`-prefixed templates for all entity types (avoids collision with articy built-in names like "Character", "Entity")
- Features are per-template with display names like "Character - Narrative Properties"
- Three menu commands: "Import from Manifest", "Verify Templates", "Clean Up Imports"
- Plugin deployed via `task articy:build` to `%APPDATA%/Articy Software/articy/4.x/Plugins/Local/`
- **Must close articy before deploying** — the DLL is locked while articy runs

### 2. Manifest Diffing

- Added `--previous` flag to `vault_to_manifest.py`
- Content hashing (SHA-256) detects new/updated/unchanged entities
- Entities with empty `articy_id` are always treated as "new" (never imported yet)
- 14 tests for diffing logic

### 3. Vault Frontmatter Writeback

- `scripts/writeback_articy_ids.py` patches `articy-id` in vault page YAML frontmatter
- Runs after articy import via `task articy:writeback`
- 10 tests

### 4. World Content (21 entities total)

**Characters (5):** Sera, Elder Aldric, Kaelen (father), Aric (son), Maren (companion)
**Locations (4):** Thornwall, Iron Peaks, Starlight Academy, Whispering Woods
**Items (3):** Kaelen's Journal, Starweaver Lens, Iron Dawn sword
**Factions (2):** Starlight Scholars, Iron Vanguard
**Zones (7):** Thornwall Market/North Gate/Elder Quarter, Whispering Woods Edge/Deep, Iron Peaks Trail/Upper Mines

All entities include production-ready creative prompts for art/audio generation (ComfyUI, audio agents).

### 5. LDtk Integration

- `scripts/ldtk_sync.py` generates `.ldtk` project from import manifest
- 9 entity defs (Character, Location, Zone, Faction, Quest, Item, Event, Lore, Creature)
- Zone entities automatically become LDtk levels
- Entity fields: display_name, vault_path, era (Father/Son/Both), articy_id
- Layer defs: Entities, Collision (IntGrid), Terrain
- `project/hosts/complete-app/scripts/ldtk_importer.gd` reads LDtk JSON in Godot
- 20 LDtk tests

### 6. Zone Entity Type

- New vault entity type bridging narrative content to level design
- Zone-specific frontmatter: parent-location, zone-type, floor, grid-width, grid-height
- Required sections: Overview, Layout & Terrain, Entities & Encounters, Era Variants, Creative Prompts
- Each zone page describes dual-era variants (father/son timeline differences)
- Zones auto-generate LDtk levels via `task ldtk:sync`

## Pipeline Workflow

```
vault/world/*.md          → task articy:prep    → import-manifest.json
import-manifest.json      → task ldtk:sync      → project/ldtk/legend-dad.ldtk
import-manifest.json      → articy "Import"      → articy entities + ID writeback
                          → task articy:writeback → vault frontmatter updated
legend-dad.ldtk           → LDtk editor          → level design, entity placement
legend-dad.ldtk           → Godot ldtk_importer  → TileMap + entity nodes
```

## Issues Encountered

1. **articy MDK `GetObjectByTechName` collision** — names like "Character" match built-in articy objects, not our templates. Fixed by prefixing all template tech names with `LD_`.
2. **articy `GetObjectsByType(ObjectType.Feature)` returns 0** — features can't be found this way. Must use `GetObjectByTechName()` with exact names.
3. **Feature duplication** — multiple import runs created duplicate features. Fixed with `GetOrCreateFeature` pattern and brute-force cleanup command.
4. **LDtk `worldDepth` crash** — generated file missing required level fields. Fixed by adding default level with all required fields.
5. **Windows file locking** — articy locks plugin DLL while running. Must close articy before `task articy:build`.

## Commits

- `bc9d7a8` feat: add articy MDK import plugin with manifest diffing (Phase 2)
- `cf87162` feat: add world content — characters, locations, items, factions
- `f177b0c` feat: add LDtk integration — project sync + Godot importer
- `f828ba0` fix: add default level and missing fields to LDtk project
- `c6f7238` feat: add zone entity type with 7 zones, zones become LDtk levels

## Next Steps

1. **Content authoring in LDtk** — design tilemap layouts for each zone
2. **Articy import** — run "Import from Manifest" to bring all 21 entities into articy
3. **Tileset creation** — pixel art tilesets matching the creative prompts
4. **Godot integration test** — load LDtk levels in Godot via ldtk_importer.gd
5. **Canonical export** — articy MDK export plugin for downstream consumers
6. **ComfyUI adapter** — generate art/audio from creative prompts
