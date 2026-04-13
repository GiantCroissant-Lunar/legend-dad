---
type: dev-log
date: 2026-04-13
agent: claude-opus-4.6
tags: [handover, articy, ldtk, pipeline, zones, world-building]
---

# Handover: Articy + LDtk Pipeline — Ready for Content Import

## Goal for Next Session

Import vault content into articy:draft X and LDtk. The pipeline infrastructure is built and tested. The next session should:

1. Run the articy import (all 21 entities including 7 zones)
2. Verify entities appear correctly in articy with populated template fields
3. Open the LDtk project and verify 7 zone levels + 9 entity types
4. Begin level design in LDtk (place entities on zone maps)

---

## Current State

### Vault Content (21 entities)

| Type | Count | Pages |
|---|---|---|
| character | 5 | sera, aldric, kaelen, aric, maren |
| location | 4 | thornwall, iron-peaks, starlight-academy, whispering-woods |
| zone | 7 | thornwall-market, thornwall-north-gate, thornwall-elder-quarter, whispering-woods-edge, whispering-woods-deep, iron-peaks-trail, iron-peaks-upper-mines |
| item | 3 | kaelens-journal, starweaver-lens, iron-dawn-sword |
| faction | 2 | starlight-academy-faction, iron-vanguard |

All pages are in `vault/world/{type}/` with full creative prompts for art/audio generation.

### Articy State

- **articy:draft X** (v4.3.6) project at `project/articy/legend-dad/`
- **MDK plugin** deployed at `%APPDATA%/Articy Software/articy/4.x/Plugins/Local/LegendDad.MdkPlugin/0.1.0/`
- **Templates exist in articy** (created during debugging): 8 `LD_*` templates (LD_Character, LD_Location, LD_Faction, LD_Quest, LD_Item, LD_Event, LD_Lore, LD_Creature)
- **LD_Zone template does NOT exist yet** — it was added after the last articy import. The plugin will create it on next "Import from Manifest"
- **Sera entity exists** in articy from test imports, but template fields may not be populated (the import ran before all bugs were fixed)
- **Orphaned features cleaned up** — 3 generic ones ("Creative Prompts", "Narrative Properties", "Pipeline Metadata") were deleted manually by the user

### LDtk State

- **LDtk project** at `project/ldtk/legend-dad.ldtk`
- **9 entity defs**: Character, Location, Zone, Faction, Quest, Item, Event, Lore, Creature
- **7 levels** auto-generated from zone entities: Iron_Peaks_Trail, Iron_Peaks_Upper_Mines, Thornwall_Elder_Quarter, Thornwall_Market, Thornwall_North_Gate, Whispering_Woods_Deep, Whispering_Woods_Edge
- **3 layer defs**: Entities, Collision (IntGrid), Terrain
- **2 enums**: EntityType, Era (Father/Son/Both)
- Each entity def has fields: display_name, vault_path, era, articy_id
- **No tilesets yet** — levels have no visual tiles, only the grid structure

### Manifest State

- `project/articy/import-manifest.json` has 21 entities
- Sera has `articy_id: ""` and `status: "new"` (reset for clean import)
- All other entities have `articy_id: ""` and `status: "new"`

---

## Pipeline Commands

```bash
# Step 1: Generate manifest from vault (with diffing)
task articy:prep

# Step 2: Sync entity defs + zone levels into LDtk
task ldtk:sync

# Step 3: Build and deploy MDK plugin (CLOSE ARTICY FIRST)
task articy:build

# Step 4: Open articy → ribbon menu → "Import from Manifest"
# This creates/updates entities and writes articy_ids back to manifest

# Step 5: Write articy IDs back to vault frontmatter
task articy:writeback

# Other useful commands
task articy:validate    # Validate manifest against JSON schema
task articy:types       # Regenerate C#/Python types from schemas
```

### Critical: articy:build Requires Closing articy

The MDK plugin DLL is locked by articy while running. You **must close articy:draft X** before running `task articy:build`. The deploy copies files to `%APPDATA%/Articy Software/articy/4.x/Plugins/Local/LegendDad.MdkPlugin/0.1.0/`.

---

## What to Do in Next Session

### 1. Articy Import

```bash
task articy:prep          # Regenerate manifest (all 21 entities, status: new)
```

Then open articy:draft X, load the legend-dad project, and click **"Import from Manifest"** from the ribbon. Expected result:

- LD_Zone template created (new)
- 8 other templates: "0 created, 8 existing"
- 21 entities created (all new)
- articy IDs written back to `import-manifest.json`

After import, run:

```bash
task articy:writeback     # Patch articy-id into vault page frontmatter
task articy:prep          # Re-run to pick up articy IDs, entities should show "unchanged"
```

### 2. Verify Articy Content

In articy, check that Sera (or any character) has:
- **Template tab** showing populated fields (overview, backstory, personality)
- **Creative Prompts** fields populated (portrait, voice, theme-music)
- **Pipeline Metadata** fields (vault_path, dialogue_hooks)

If the Template tab is empty, the `EntityImporter.SetEntityProperties()` method may need debugging — check the property path format `{TemplateName}_{FeatureName}.{property_key}` (e.g. `LD_Character_NarrativeProps.overview`).

### 3. LDtk Level Design

Open `project/ldtk/legend-dad.ldtk` in LDtk. The 7 zones appear as levels. To design a level:

1. Select a level (e.g. Thornwall_Market)
2. Select the **Entities** layer
3. Click a Character entity type and place it on the map
4. In the field panel, set `display_name` to "Sera", `era` to "Both"
5. Switch to **Collision** layer to paint IntGrid values (solid, water, pit)

No tilesets exist yet — visual tile art needs to be created from the creative prompts.

### 4. If Something Goes Wrong

**articy "Import from Manifest" shows errors:**
- Use "Clean Up Imports" first to remove stale data, then re-import
- The cleanup deletes features by brute-force tech name lookup and all non-Default templates

**articy path discovery fails ("could not find project/articy/ directory"):**
- The plugin has a hardcoded fallback path: `C:\lunar-horse\yokan-projects\legend-dad\project\articy`
- If the project moves, update `FindProjectRoot()` in `Plugin.cs`

**LDtk won't open the .ldtk file:**
- Delete `project/ldtk/legend-dad.ldtk` and regenerate with `task ldtk:sync`
- The generator creates a fresh file with proper structure

---

## File Map

### Vault Content
```
vault/world/
  characters/   sera.md, aldric.md, kaelen.md, aric.md, maren.md
  locations/    thornwall.md, iron-peaks.md, starlight-academy.md, whispering-woods.md
  zones/        thornwall-market.md, thornwall-north-gate.md, thornwall-elder-quarter.md,
                whispering-woods-edge.md, whispering-woods-deep.md,
                iron-peaks-trail.md, iron-peaks-upper-mines.md
  items/        kaelens-journal.md, starweaver-lens.md, iron-dawn-sword.md
  factions/     starlight-academy-faction.md, iron-vanguard.md
  _meta/        conventions.md
```

### Pipeline Scripts
```
scripts/
  vault_to_manifest.py      # vault markdown → import-manifest.json
  writeback_articy_ids.py    # manifest articy_ids → vault frontmatter
  ldtk_sync.py               # manifest → .ldtk project file
```

### Articy MDK Plugin
```
project/articy/mdk-plugin/LegendDad.MdkPlugin/
  Plugin.cs                  # Main entry, menu commands, FindProjectRoot()
  TemplateProvisioner.cs     # Creates templates from template-definitions.json
  EntityImporter.cs          # Creates/updates entities from manifest
  ConnectionResolver.cs      # Resolves entity connections
  ManifestWriteback.cs       # Writes articy IDs back to manifest JSON
  PluginManifest.xml         # Plugin metadata
```

### Schemas & Generated Types
```
project/articy/schemas/
  import-manifest.schema.json      # Vault → articy contract
  template-definitions.json         # Template/feature/property definitions (9 types)

project/articy/generated/
  csharp/ImportManifest.cs          # quicktype-generated C# types
  python/import_manifest.py         # quicktype-generated Python types
```

### LDtk & Godot
```
project/ldtk/legend-dad.ldtk                              # LDtk project (9 entity defs, 7 levels)
project/hosts/complete-app/scripts/ldtk_importer.gd        # Godot LDtk reader
```

### Tests (65 passing)
```
tests/
  conftest.py                    # Shared fixtures
  test_vault_to_manifest.py      # 20 tests — vault parser
  test_manifest_diffing.py       # 15 tests — diffing logic
  test_writeback_articy_ids.py   # 10 tests — frontmatter writeback
  test_ldtk_sync.py              # 20 tests — LDtk generator
```

---

## Known Issues

1. **quicktype types are stale** — the `zone` type was added to the schema but `task articy:types` has not been re-run. The generated C#/Python types don't include `zone` in the TypeEnum. Run `task articy:types` to regenerate. (The MDK plugin still works because it reads the manifest JSON directly via Newtonsoft.Json, not through the generated types for entity type enumeration.)

2. **Zone grid dimensions not passed to LDtk** — the vault frontmatter has `grid-width` and `grid-height` but these are in the YAML frontmatter, not in `template_properties`. The LDtk sync script currently uses a default 320x256px (20x16 tiles). The designer adjusts in LDtk, or we can update `vault_to_manifest.py` to extract these frontmatter fields into template_properties.

3. **articy Sera entity from test runs** — Sera may exist in articy from earlier debugging with empty/incorrect template fields. The cleanup command or manual deletion in articy may be needed before a clean import.

4. **Creative prompt key normalization** — the manifest uses hyphenated keys like `theme-music` but articy template property names use underscores (`theme_music`). The `EntityImporter` normalizes hyphens to underscores. The LDtk side doesn't use creative prompts directly, so this only matters for articy.
