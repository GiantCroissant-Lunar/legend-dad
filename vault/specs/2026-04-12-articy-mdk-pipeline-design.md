---
type: spec
status: draft
date: 2026-04-12
tags: [articy, mdk, pipeline, world-building, architecture]
---

# Articy MDK Pipeline Design

## Overview

A schema-driven pipeline that keeps Obsidian vault as the narrative source of truth, articy:draft as the structural game database, and exports canonical JSON consumed by Godot, ComfyUI, LDtk, and potentially Blender.

**Core principle:** Put intelligence where iteration is cheap. Agent skills and Python scripts handle complexity. The MDK plugin stays thin.

## Layered Source of Truth

| Layer | Tool | Owns | Editable by |
|---|---|---|---|
| Narrative | Obsidian vault (`vault/world/`) | Prose, lore, backstories, creative prompts | Agents + humans |
| Structural | articy:draft (Windows-only) | Entity relationships, dialogue trees, quest flows, global variables | Humans (visual editor) |
| Game-ready | Canonical JSON export | Everything combined | Nobody (generated only) |

**Sync direction:** One-way. Vault → articy only. articy content never flows back to vault (except articy IDs for linking).

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  MAC or WIN (agent workspace)                           │
│                                                         │
│  vault/world/*.md                                       │
│       │  (agents write/edit via @world-writer)          │
│       ▼                                                 │
│  scripts/vault-to-manifest.py                           │
│       │  (parses markdown, validates against schema)    │
│       ▼                                                 │
│  project/articy/import-manifest.json                    │
│       │                                                 │
│       │  git push                                       │
├───────┼─────────────────────────────────────────────────┤
│  WIN  │  (articy:draft — Windows only)                  │
│       ▼                                                 │
│  MDK Plugin: "Import Manifest"                          │
│       │  (thin C# — reads JSON, creates/updates)        │
│       ▼                                                 │
│  articy:draft project                                   │
│       │  (dialogue authoring, flow editing by human)    │
│       ▼                                                 │
│  MDK Plugin: "Export Canonical JSON"                     │
│       │                                                 │
│       ▼                                                 │
│  project/articy/export/canonical.json                   │
│       │                                                 │
│       │  git push                                       │
├───────┼─────────────────────────────────────────────────┤
│  MAC or WIN (agent workspace)                           │
│       ▼                                                 │
│  Adapter scripts (scripts/adapters/)                    │
│       ├→ comfyui-adapter → ComfyUI workflow inputs      │
│       ├→ ldtk-adapter → LDtk entity definitions        │
│       └→ godot-adapter → Godot-ready resource files     │
│                                                         │
│  Godot (runs on both Mac + Win) imports:                │
│    - canonical.json (dialogue, quests, entities)        │
│    - ComfyUI outputs (images, audio)                    │
│    - LDtk maps (world/region structure)                 │
└─────────────────────────────────────────────────────────┘
```

**Environment notes:**
- Both Mac and Windows have full dev setup (Godot, Claude Code, scripts, adapters)
- articy:draft is the only Windows-exclusive tool
- Git is the bridge between machines

## Entity Types

These map 1:1 between vault page types, import manifest entries, and articy templates.

| Type | Vault path | Articy template | Holds |
|---|---|---|---|
| character | `vault/world/characters/` | Character | Name, backstory, relationships, personality, creative prompts |
| location | `vault/world/locations/` | Location | Description, atmosphere, connections, history |
| faction | `vault/world/factions/` | Faction | Purpose, hierarchy, relationships, territory |
| quest | `vault/world/quests/` | Quest (Flow) | Narrative arc, objectives, stakes, branching notes |
| item | `vault/world/items/` | Item | Description, lore, purpose |
| event | `vault/world/history/` | Event | Timeline events, causes, consequences |
| lore | `vault/world/lore/` | Lore | Cultural notes, traditions, world rules |
| bestiary | `vault/world/bestiary/` | Creature | Ecology, behavior, lore |

This mapping is experimental and may evolve as the articy project takes shape.

## Vault Structure

```
vault/world/
  ├── _meta/
  │   ├── conventions.md          # Frontmatter schema, section requirements per type
  │   └── prompts/                # Prompt templates for @world-writer (one per type)
  │       ├── character-backstory.md
  │       ├── location-history.md
  │       ├── faction-profile.md
  │       ├── quest-narrative.md
  │       ├── bestiary-entry.md
  │       └── timeline-event.md
  ├── characters/
  ├── locations/
  ├── factions/
  ├── quests/
  ├── items/
  ├── history/
  │   └── timeline.md             # Master timeline — @lore-checker validates against this
  ├── lore/
  └── bestiary/
```

**Standard vault page frontmatter:**

```yaml
---
type: character | location | faction | quest | item | event | lore | bestiary
status: draft                # draft → reviewed (human promotes)
articy-id: ""                # filled after first articy import
tags: []
connections: []              # [[links]] to related pages
era: ""
last-agent-pass: "2026-04-12"
---
```

**What vault owns vs what articy adds:**
- Vault: narrative prose, creative prompts, lore context, backstories — the "writer's room"
- Articy: dialogue trees, flow diagrams, quest state machines, entity relationship graph, global variables — the "production database"

## Schema-Driven Contract (quicktype)

JSON Schema is the single source of truth for data contracts. quicktype generates typed code for every consumer.

### Project structure

```
project/articy/
  ├── schemas/
  │   ├── import-manifest.schema.json    # vault → articy contract
  │   └── canonical-export.schema.json   # articy → downstream contract
  ├── generated/
  │   ├── csharp/          # quicktype output → for MDK plugin
  │   └── python/          # quicktype output → for scripts/adapters
  ├── import-manifest.json # output of vault-to-manifest.py
  └── export/
      └── canonical.json   # output of MDK exporter
```

### Type generation

quicktype reads the JSON Schema files and generates:
- **C# classes** — consumed by the MDK plugin for type-safe import/export
- **Python dataclasses** — consumed by `vault-to-manifest.py` and adapter scripts
- **GDScript/JSON typing** — for Godot resource loading (if needed later)

### Taskfile integration

```yaml
articy:prep       # Run vault-to-manifest.py → generate import-manifest.json
articy:types      # Run quicktype on schemas → regenerate C#/Python types
articy:validate   # Validate existing manifest/export against schemas
```

## Import Manifest Schema

The contract between agent skills / vault parser and the MDK plugin.

```json
{
  "version": "0.1.0",
  "generated": "2026-04-12T10:30:00Z",
  "generated_by": "articy-prep",
  "entities": [
    {
      "vault_path": "vault/world/characters/sera.md",
      "articy_id": "",
      "type": "character",
      "status": "new",
      "display_name": "Sera",
      "template_properties": {
        "backstory": "Studied at the Academy of Starlight...",
        "personality": "Curious, cautious, fiercely loyal",
        "role": "protagonist"
      },
      "connections": [
        {
          "target_vault_path": "vault/world/factions/starlight-academy.md",
          "relation": "member_of"
        }
      ],
      "creative_prompts": {
        "portrait": "16-bit pixel art, grayscale base...",
        "voice": "Soft-spoken, measured cadence...",
        "theme_music": "Melancholic piano melody..."
      },
      "dialogue_hooks": [
        "First meeting — introduces herself reluctantly",
        "After Act 1 — reveals connection to the Academy"
      ],
      "flow_notes": "Sera's quest line branches at the Academy confrontation"
    }
  ]
}
```

### Field semantics

| Field | Purpose |
|---|---|
| `vault_path` | Source vault page. Used as stable key for diffing. |
| `articy_id` | Empty on first run. MDK plugin fills it after creation. Written back to vault frontmatter via git. |
| `type` | Maps to articy template name. |
| `status` | `new` / `updated` / `unchanged`. MDK plugin skips `unchanged`. Computed by diffing current vault against last manifest. |
| `display_name` | Entity name in articy. |
| `template_properties` | Flat key-value map. Must match articy template field names. |
| `connections` | Relationships to other entities. Uses vault paths (not articy IDs) as keys. MDK plugin resolves via manifest. |
| `creative_prompts` | Passed through to articy entity properties. Exported in canonical JSON for ComfyUI adapter. |
| `dialogue_hooks` | Hints for human dialogue authoring in articy. Stored as entity notes. |
| `flow_notes` | Hints for quest flow design. Stored as entity description. |

### MDK plugin import logic (pseudocode)

```
for each entity in manifest where status != "unchanged":
    if articy_id is empty:
        create new entity with template matching entity.type
    else:
        find existing entity by articy_id
    set template properties from entity.template_properties
    store creative_prompts as template properties
    store dialogue_hooks in entity notes
    store flow_notes in entity description
    write assigned articy_id back to manifest

for each entity in manifest:
    for each connection in entity.connections:
        resolve target_vault_path to articy_id via manifest
        create or update articy connection
```

## Canonical Export Format

> **TBD** — To be defined after the articy:draft project is created and initial templates are set up. The export schema will be designed to serve all downstream consumers (Godot, ComfyUI adapters, LDtk adapters) from a single JSON file.

The export schema will be added to `project/articy/schemas/canonical-export.schema.json` and quicktype will generate types for all consumers.

## Adapter Scripts

> **TBD** — Detailed adapter designs depend on the canonical export format and downstream tool requirements.

Planned adapters in `scripts/adapters/`:

| Adapter | Input | Output | Consumer |
|---|---|---|---|
| `comfyui_adapter.py` | canonical.json | ComfyUI workflow input JSONs (per-entity prompts) | ComfyUI |
| `ldtk_adapter.py` | canonical.json | LDtk entity definitions / tileset metadata | LDtk |
| `godot_adapter.py` | canonical.json | Godot-ready resource files (`.tres` / `.json`) | Godot |

## Component Responsibilities

| Component | Language | Intelligence | Iteration speed |
|---|---|---|---|
| `@world-writer` skill | Agent skill | High — generates narrative content | Fast (edit markdown) |
| `@articy-prep` skill | Agent skill | Medium — orchestrates, reviews output | Fast (edit markdown) |
| `vault-to-manifest.py` | Python | Medium — parses vault, diffs, validates | Fast (edit Python). Runnable standalone via `task articy:prep` or by agents via `@articy-prep`. |
| MDK import plugin | C# | Low — reads JSON, creates entities | Slow (Windows + articy + rebuild) |
| MDK export plugin | C# | Low — dumps articy DB to JSON | Slow (Windows + articy + rebuild) |
| Adapter scripts | Python | Low — transform JSON shapes | Fast (edit Python) |

## Skill Updates Needed

Existing 05-world skills need updates to align with this pipeline:

| Skill | Current state | Needed change |
|---|---|---|
| `@articy-prep` | Outputs YAML summary for manual import | Enhance to call `vault-to-manifest.py`, validate output, handle articy-id writeback |
| `@world-writer` | References paths that don't exist yet | Update paths, create `_meta/conventions.md` and prompt templates |
| `@lore-checker` | References `world/history/timeline.md` | Create the timeline file, update paths |
| `@world-refiner` | Fully functional design | Update paths to match new vault structure |
| `@lore-extractor` | References old RFC paths | Update source paths for legend-dad project |

## Open Questions

1. **articy template design** — Exact template fields depend on the articy project structure, to be defined when the project is created
2. **Canonical export format** — Depends on articy templates and downstream tool needs
3. **ComfyUI workflow integration** — How creative prompts map to specific ComfyUI nodes/workflows
4. **LDtk integration details** — How articy entity IDs map to LDtk entity definitions and tile placement
5. **Blender pipeline** — If added, how 3D models get converted to spritesheets and integrated
6. **articy global variables** — How game state variables are defined and exported for Godot
7. **Version compatibility** — articy:draft X MDK tracks .NET 8 for version 4.1+; need to confirm target version
