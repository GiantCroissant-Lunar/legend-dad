---
type: dev-log
date: 2026-04-13
agent: claude-opus-4.6
tags: [handover, comfyui, mac, tileset, pipeline]
---

# Handover: ComfyUI Tileset Generation on Mac Mini M4

## Goal for Next Session (Mac)

Generate the first grayscale tilesets using ComfyUI on the Mac Mini M4. The pipeline infrastructure, workflows, biome prompts, and palettes are all ready. The Mac session should:

1. Install required ComfyUI custom nodes
2. Create the grayscale-16 palette swatch PNG
3. Load and test the tileset workflow in ComfyUI browser UI
4. Generate tilesets for all 3 biomes (field, dungeon, town)
5. Optionally refine tiles in Krita with AI Diffusion

---

## Current State

### Vault (36 entities — single source of truth)

| Type | Count | Details |
|---|---|---|
| Characters | 5 | Sera, Aldric, Kaelen, Aric, Maren |
| Locations | 4 | Thornwall, Iron Peaks, Starlight Academy, Whispering Woods |
| Zones | 7 | 3 Thornwall + 2 Woods + 2 Peaks |
| Items | 3 | Iron Dawn, Kaelen's Journal, Starweaver Lens |
| Factions | 2 | Iron Vanguard, Starlight Scholars |
| Bestiary | 5 | Thornbriar Stalker, Moss Lurker, Crystal Crawler, Shade Wisp, Iron Borer |
| Quests | 4 | Father's Departure, Whispers in the Woods, Sealed Observatory, Vanguard Checkpoint |
| Lore | 3 | The Starweavers, Sealed Caverns, Whispering Enchantment |
| Events | 3 | Observatory Disaster, Kaelen's Last Letter, First Tremor |

All entities have creative prompts suitable for ComfyUI art generation.

### Articy (Windows — completed)

- 29 entities imported (36 minus 7 zones which are LDtk-only)
- 9 templates: LD_Character, LD_Location, LD_Zone, LD_Faction, LD_Quest, LD_Item, LD_Event, LD_Lore, LD_Creature
- Export at `project/articy/export/` (hierarchy, objects, definitions)

### Biome System

3 biomes defined in `vault/world/biomes/`:

| Biome | IntGrid Range | Palette (lospec) | Location |
|---|---|---|---|
| Field | 10-19 | Deep Forest 16 | Whispering Woods |
| Dungeon | 20-29 | Damage Dice 10 & 6 | Iron Peaks |
| Town | 30-39 | Fantasy RPG | Thornwall |

Universal palette: DawnBringer 16 (for characters, UI, cross-biome assets)

### Key Architecture Decision: Grayscale + Palette Shader

- **Tiles are grayscale** (16 levels, 0-255 mapped to 16 palette indices)
- **Color applied at runtime** via Godot shader (`shaders/palette_swap.gdshader`)
- **Era swap** = just change the 16x1 palette texture (father=vibrant, son=muted)
- ComfyUI generates grayscale tiles, no color consistency concerns

---

## ComfyUI Setup Steps (Mac)

### 1. Install Custom Nodes

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/dimtoneff/ComfyUI-PixelArt-Detector
# Restart ComfyUI after installing
```

### 2. Create Grayscale Palette Swatch

The workflow needs a `grayscale-16.png` (16x1 pixel image) in the PixelArt-Detector palettes folder.

16 evenly-spaced grays from the hex file at `project/comfyui/palettes/grayscale-16.hex`:
```
#000000 #111111 #222222 #333333
#444444 #555555 #666666 #777777
#888888 #999999 #aaaaaa #bbbbbb
#cccccc #dddddd #eeeeee #ffffff
```

Create this PNG and copy to:
```
ComfyUI/custom_nodes/ComfyUI-PixelArt-Detector/palettes/grayscale-16.png
```

### 3. Load Workflow in ComfyUI

Drag & drop `project/comfyui/workflows/tileset-grayscale.json` into ComfyUI browser UI.

**Update these nodes to match local models:**
- Node 1 (Checkpoint): set to your SDXL checkpoint filename
- Node 2 (LoRA): set to your pixel art LoRA filename

### 4. Generate Tilesets

**Via ComfyUI UI**: Change the positive prompt (Node 3) per biome and click Queue.

**Via headless runner**:
```bash
# Dry run (no ComfyUI needed)
task comfyui:tileset:dry-run -- --biome=field

# Actual generation
task comfyui:tileset -- --biome=field
task comfyui:tileset -- --biome=all

# With fixed seed for reproducibility
task comfyui:tileset -- --biome=field --seed=42

# Override model via env
COMFYUI_CHECKPOINT=mymodel.safetensors COMFYUI_LORA=mypixelart.safetensors \
  task comfyui:tileset -- --biome=field
```

Output goes to `build/tilesets/<biome>/`.

### 5. Krita AI Diffusion (Optional Refinement)

If tiles need fixing:
1. Open generated tileset in Krita
2. Connect AI Diffusion plugin to same ComfyUI server (127.0.0.1:8188)
3. Select tile region → Inpaint to fix
4. Export final grayscale tileset

---

## File Map

### ComfyUI Pipeline
```
project/comfyui/
  workflows/tileset-grayscale.json   # Editor-format workflow (drag & drop)
  lib/
    comfyui-client.mjs               # HTTP client (queue, poll, download)
    workflow-loader.mjs              # Editor→API format bridge
    tileset-runner.mjs               # Biome→prompt→queue orchestrator
    palette-generator.mjs            # Vault hex→palette files
  palettes/
    grayscale-16.hex                 # 16 gray levels (generation target)
    dawnbringer-16.hex               # Universal palette
    fantasy-rpg.hex                  # Thornwall palette
    deep-forest-16.hex              # Whispering Woods palette
    damage-dice-10-6.hex            # Iron Peaks palette
```

### Biome Docs
```
vault/world/biomes/
  _conventions.md                    # IntGrid 0-9, palette table, LDtk architecture
  _art-pipeline.md                   # Grayscale+shader pipeline, tool chain
  _comfyui-workflows.md             # Workflow docs, biome prompts, required nodes
  field.md                           # IntGrid 10-19, Deep Forest 16 palette
  dungeon.md                         # IntGrid 20-29, Damage Dice palette
  town.md                            # IntGrid 30-39, Fantasy RPG palette
```

### Godot Shader
```
project/hosts/complete-app/
  shaders/palette_swap.gdshader      # Grayscale→palette lookup shader
  scripts/palette_manager.gd         # Static helper (apply/swap/remove palette)
```

---

## Biome Prompts Quick Reference

**Field** (change Node 3 positive prompt to):
```
16-bit pixel art tileset sheet, top-down 3/4 perspective, 16x16 tile grid layout,
JRPG style, grayscale, monochrome, black and white tonal values only,
old-growth forest biome, grass tiles, dirt path tiles, tree trunk tiles,
bush tiles, water stream tiles, stone path tiles, fallen log, wildflowers,
seamless tile edges, clean pixel edges, no anti-aliasing, flat background
```

**Dungeon**:
```
16-bit pixel art tileset sheet, top-down 3/4 perspective, 16x16 tile grid layout,
JRPG style, grayscale, monochrome, black and white tonal values only,
underground cave mine biome, cave floor tiles, cave wall tiles, mine track tiles,
ore vein tiles, crystal tiles, lava pool tiles, rubble tiles, torch bracket,
seamless tile edges, clean pixel edges, no anti-aliasing, flat background,
dark ambient lighting with localized light sources
```

**Town**:
```
16-bit pixel art tileset sheet, top-down 3/4 perspective, 16x16 tile grid layout,
JRPG style, grayscale, monochrome, black and white tonal values only,
medieval village biome with open-top buildings interiors visible,
cobblestone tiles, building wall tiles, wood floor tiles, furniture tiles,
fence tiles, market stall, well, door frame, window, roof edge,
seamless tile edges, clean pixel edges, no anti-aliasing, flat background,
warm ambient lighting
```

---

## What NOT to Do on Mac

- Don't modify vault content without syncing back (vault is single source of truth)
- Don't run articy tasks (Windows only)
- Don't modify the articy export files
- Generated tilesets go in `build/tilesets/` (gitignored) — commit finals to `project/ldtk/tilesets/` when ready

## After Tileset Generation

1. Commit final grayscale tilesets to `project/ldtk/tilesets/`
2. Back on Windows: import tilesets into LDtk, set up auto-rules
3. Create 16x1 palette PNGs for Godot (from the .hex files)
4. Test palette shader in Godot with tileset + palette
