---
name: articy-prep
description: "Run the full vault → articy → Godot pipeline: generate manifest, build + deploy MDK plugin, prompt user to import/export in articy:draft, writeback IDs, generate .tres resources."
category: 05-world
layer: world
related_skills:
  - "@world-writer"
  - "@lore-checker"
---

# Articy Prep

Full pipeline for syncing vault content (narrative + mechanical) into articy:draft and generating Godot .tres resources.

## Pipeline Steps

### 1. Generate manifest from vault

```bash
task articy:prep
```

Runs `vault_to_manifest.py` which:
- Scans `vault/world/` for all entity types (character, location, zone, faction, quest, item, event, lore, bestiary, curve)
- Lifts narrative sections (H2 headings) into `template_properties` as strings
- Lifts mechanical frontmatter (`battle_stats`, `actions`, `encounter_table`, `difficulty_tier`, `curve_kind`, `data_points`, etc.) into `template_properties` as structured data
- Diffs against previous manifest to set status (new/updated/unchanged)
- Validates against `project/articy/schemas/import-manifest.schema.json`
- Outputs `project/articy/import-manifest.json`

### 2. Build and deploy MDK plugin

```bash
task articy:build
```

Compiles the C# MDK plugin and copies DLL + assets to articy's local plugins directory. The plugin handles:
- **TemplateProvisioner**: Creates/verifies articy templates with narrative + mechanical features (BattleStats, EncounterData, DifficultyData, CurveData)
- **EntityImporter**: Creates/updates entities, routes narrative fields to NarrativeProps and mechanical fields (serialized as JSON) to their specific features
- **ConnectionResolver**: Resolves vault wikilinks to articy entity relationships
- **ManifestWriteback**: Writes articy IDs back to the manifest JSON

### 3. Import in articy:draft (manual)

Open articy:draft and run **"Import from Manifest"** from the plugin menu. This creates/updates all entities with their templates populated.

If templates have changed (new features added), run **"Clean Up Imports"** first to delete old templates, then re-import. After cleanup, regenerate the manifest **without `--previous`** to clear stale articy IDs:

```bash
python scripts/vault_to_manifest.py vault/world project/articy/import-manifest.json --schema project/articy/schemas/import-manifest.schema.json
```

Then clear any leftover articy_id values before re-importing.

### 4. Export from articy:draft (manual)

In articy:draft, export the project as JSON. This writes to `project/articy/export/`.

### 5. Writeback articy IDs to vault

```bash
task articy:writeback
```

Updates vault page frontmatter with `articy-id:` values from the manifest.

### 6. Generate Godot .tres resources

```bash
task content:generate:tres
```

Runs `scripts/adapters/canonical_to_godot.py` which reads `import-manifest.json` and emits:
- **EnemyDefinition .tres** files from bestiary entities (to `project/shared/content/enemies/enemies-core/`)
- **EncounterTable .tres** files from zone entities with encounter tables (to `project/shared/content/encounters/encounters-core/`)
- Updates `bundle.json` provides lists

## Entity Types and Their Mechanical Features

| Entity Type | Template | Mechanical Feature | Fields |
|---|---|---|---|
| bestiary | LD_Creature | BattleStats | battle_stats (JSON), actions (JSON), group_size_min/max, zone_affinity |
| zone | LD_Zone | EncounterData | encounter_table (JSON), encounter_rate, difficulty_tier |
| location | LD_Location | DifficultyData | recommended_level_min/max, difficulty_tier |
| curve | LD_Curve | CurveData | curve_kind, applies_to, data_points (JSON) |

## Quick Reference

```bash
# Full pipeline (after vault edits)
task articy:prep           # 1. vault → manifest
task articy:build          # 2. build MDK plugin
# → Import in articy:draft # 3. manual
# → Export in articy:draft # 4. manual
task articy:writeback      # 5. IDs → vault
task content:generate:tres # 6. manifest → .tres

# Validate only
task articy:validate       # Check manifest against schema

# Regenerate typed code (after schema changes)
task articy:types          # quicktype → Python + C# classes
```

## Rules

- Always run `task articy:prep` before importing — stale manifests cause data loss.
- Always run `task articy:build` before importing — stale plugin DLL misses new features.
- After `Clean Up Imports`, regenerate manifest without `--previous` to clear stale articy IDs.
- The adapter only generates .tres for bestiary entries with `battle_stats` and zones with `encounter_table`. Entities without mechanical data are narrative-only in articy.
- Status effects referenced in bestiary actions must have a matching case in `BattleManager._apply_status_effect`. Current set: `sleep`, `poison`, `paralysis`, `stopspell`.
