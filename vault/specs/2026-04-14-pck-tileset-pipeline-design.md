---
date: 2026-04-14
status: approved
tags: [tileset, pck, pipeline, godot, comfyui, spec]
---

# PCK Tileset Pipeline Design

## Overview

End-to-end pipeline from ComfyUI-generated grayscale tilesets to runtime Godot rendering via dynamically loaded PCK files, with palette shader era swapping and graceful fallback to programmatic tiles.

## Architecture: Hybrid Python + Godot Headless (Approach C)

Python handles image processing and data extraction (slicing tiles, reading LDtk). Godot headless creates its own TileSet resources natively (guaranteed format compatibility) and packs them into PCK files. All Godot headless commands route through `run_godot_checked.py` to catch false-green exits.

## Pipeline Flow

```
ComfyUI output (512×512 grayscale PNG)
  ↓
[task tileset:preprocess]  Python — slice into 32px tiles, reassemble clean atlas
  ↓
Clean atlas PNG (512×512, guaranteed grid alignment)
  ↓
[task pck:build]  Two-stage:
  Stage 1: Python — reads LDtk level JSON, extracts IntGrid tile properties,
           generates manifest.json (atlas path, tile properties, palette paths)
  Stage 2: Godot headless (via run_godot_checked.py) — reads manifest,
           creates TileSet resource + packs into .pck
  ↓
build/_artifacts/pck/{location-name}.pck
  ↓
[Godot runtime]  LocationManager autoload — load/unload PCK, apply palette shader,
                 fallback to TilesetFactory if PCK unavailable
```

## Component Details

### 1. Preprocessing Script

**File:** `scripts/tileset_preprocess.py`

**Input:** `build/tilesets/{biome}/grayscale_tileset_*.png` (512×512)
**Output:** `build/tilesets/{biome}/atlas_32x32.png` (512×512, clean grid)

Behavior:
1. Load the 512×512 source image
2. Slice into a 16×16 grid of 32px cells
3. For each cell: crop to exact 32×32 boundaries (eliminates sub-pixel bleeding)
4. Reassemble into a new 512×512 image with guaranteed pixel-perfect grid
5. Optionally validate: reject cells that are entirely blank or entirely uniform (bad generation)
6. Save as `atlas_32x32.png`

**Taskfile command:**

```yaml
tileset:preprocess:
  desc: Slice and reassemble clean 32x32 tile atlas from ComfyUI output
  cmds:
    - python3 scripts/tileset_preprocess.py --biome={{.CLI_ARGS}} --tile-size=32
```

Usage: `task tileset:preprocess -- field`

### 2. PCK Build Pipeline

#### Stage 1: Python Manifest Generator

**File:** `scripts/pck_manifest.py`

Reads LDtk project JSON + biome IntGrid vocabulary, outputs a manifest.json for Godot to consume.

**Input:**
- LDtk project file (`project/ldtk/legend-dad.ldtk`)
- Location name (e.g. `whispering-woods`)
- Atlas PNG path (from preprocessing step)
- Palette `.hex` files → converted to 16×1 PNGs (father era + son era)

**Output:** `build/_artifacts/pck/{location}/manifest.json`

```json
{
  "location": "whispering-woods",
  "biome": "field",
  "atlas_path": "build/tilesets/field/atlas_32x32.png",
  "tile_size": 32,
  "grid_columns": 16,
  "grid_rows": 16,
  "palettes": {
    "father": "build/_artifacts/pck/whispering-woods/palette_father.png",
    "son": "build/_artifacts/pck/whispering-woods/palette_son.png"
  },
  "tiles": [
    { "atlas_x": 0, "atlas_y": 0, "intgrid": 10, "type": "grass", "walkable": true },
    { "atlas_x": 1, "atlas_y": 0, "intgrid": 11, "type": "path", "walkable": true },
    { "atlas_x": 2, "atlas_y": 0, "intgrid": 12, "type": "building_wall", "walkable": false }
  ]
}
```

The `tiles` array maps atlas grid coordinates to IntGrid IDs and walkability. Tiles not listed in the IntGrid vocabulary default to walkable (decoration tiles).

#### Stage 2: Godot Headless PCK Builder

**File:** `project/hosts/complete-app/scripts/pck_builder.gd`

A GDScript tool script run via `run_godot_checked.py` in headless mode. It:
1. Reads `manifest.json`
2. Creates a `TileSet` resource with:
   - One `TileSetAtlasSource` from the atlas PNG
   - Custom data layer `"walkable"` (bool) per tile
   - Custom data layer `"tile_type"` (String) per tile
3. Saves as `res://locations/{location}/tileset.tres`
4. Copies atlas PNG and palette PNGs into `res://locations/{location}/`
5. Sets import settings: nearest filter, no mipmaps (critical for pixel art)
6. Packs the `locations/{location}/` directory into `{location}.pck`

**Taskfile commands:**

```yaml
pck:manifest:
  desc: Generate PCK manifest from LDtk data
  cmds:
    - python3 scripts/pck_manifest.py --location={{.CLI_ARGS}}

pck:build:
  desc: Build location PCK (manifest + Godot headless pack)
  cmds:
    - task: pck:manifest
      vars: { CLI_ARGS: "{{.CLI_ARGS}}" }
    - >-
      python3 scripts/run_godot_checked.py
      {{.GODOT_PATH}} --headless
      --path {{.GODOT_PROJECT_DIR}}
      --script scripts/pck_builder.gd
      -- --location={{.CLI_ARGS}}
```

Usage: `task pck:build -- whispering-woods`

### 3. Runtime LocationManager

**File:** `project/hosts/complete-app/scripts/location_manager.gd`
**Type:** Autoload singleton (registered in `project.godot`)

**API:**

```gdscript
# Signals
signal location_loaded(location_name: String)
signal location_unloaded(location_name: String)

# Methods
func load_location(location_name: String) -> void
func unload_location() -> void
func swap_era(era: int) -> void  # C_TimelineEra.Era.FATHER or SON
func get_current_location() -> String
func is_location_loaded() -> bool
```

**Load flow:**
1. `load_location("whispering-woods")` called
2. Unload current location if any
3. Try `ProjectSettings.load_resource_pack("res://locations/whispering-woods.pck")`
4. If PCK loads successfully:
   - Load TileSet from `res://locations/whispering-woods/tileset.tres`
   - Load palette textures (`palette_father.png`, `palette_son.png`)
   - Create TileMapLayer, assign TileSet
   - Apply `palette_swap.gdshader` via `PaletteManager.apply_palette()`
5. If PCK missing/empty/corrupt:
   - Emit warning
   - Fall back to `TilesetFactory.create_tileset()` for that biome
   - Game still runs with colored rectangle tiles
6. Emit `location_loaded`

**Unload flow:**
1. Remove TileMapLayer from scene tree
2. Free TileSet and palette textures
3. Emit `location_unloaded`

**Era swap flow:**
1. `GameActions.action_switch_era` signal triggers `swap_era()`
2. `PaletteManager.swap_palette(tilemap_layer, new_era_palette)`
3. Just a texture swap on the shader uniform — instant, no reload needed

### 4. PCK Resource Layout

Each location PCK contains a self-contained directory under `res://locations/`:

```
locations/whispering-woods/
├── tileset.tres              # TileSet resource (atlas source + custom data)
├── atlas_32x32.png           # Grayscale tileset atlas (512×512)
├── atlas_32x32.png.import    # Godot import settings (nearest filter, no mipmaps)
├── palette_father.png        # 16×1 palette texture (vibrant era)
├── palette_son.png           # 16×1 palette texture (muted era)
└── manifest.json             # Build metadata (packed for debugging)
```

**Location registry:** `project/hosts/complete-app/data/locations.json`

```json
{
  "whispering-woods": { "biome": "field", "pck": "whispering-woods.pck" },
  "thornwall-market": { "biome": "town", "pck": "thornwall-market.pck" },
  "iron-peaks-mine": { "biome": "dungeon", "pck": "iron-peaks-mine.pck" }
}
```

`LocationManager` reads this at startup to know what locations are available.

### 5. Integration with Existing Systems

**`main.gd`** — replace TilesetFactory usage with LocationManager:
- Remove `tileset_factory.gd` calls in `_build_game_view()`
- Call `LocationManager.load_location()`, get TileMapLayer from LocationManager, add to SubViewport
- `_switch_active_era()` calls `LocationManager.swap_era(era)`

**`S_ActionProcessor`** — walkability check unchanged:
- Reads custom data `"walkable"` from TileMapLayer via `get_cell_tile_data()`
- PCK-packed TileSet has the same custom data layer — works as-is

**`ws_client.gd`** — state snapshots unchanged:
- Map data in state snapshots still comes from TileMapLayer

**`tileset_factory.gd`** — kept as permanent default:
- Not deleted. LocationManager uses it as fallback when PCK is unavailable.
- Game always runs even without generated tilesets.

**`project.godot`** — add LocationManager autoload:
```
LocationManager="*res://scripts/location_manager.gd"
```

**`run_godot_checked.py`** — vendored into repo:
- Copy from `project-agent-union/scripts/` to `scripts/run_godot_checked.py`
- All Godot headless Taskfile commands route through it

### 6. Taskfile Commands Summary

```yaml
tileset:preprocess:    # Slice + reassemble clean atlas from ComfyUI output
pck:manifest:          # Generate manifest.json from LDtk IntGrid data
pck:build:             # Full PCK build (manifest + Godot headless pack)
```

Full developer workflow:
```bash
task comfyui:tileset -- --biome=field          # Generate grayscale tiles
task tileset:preprocess -- field               # Clean atlas
task pck:build -- whispering-woods             # LDtk → TileSet → PCK
```

## Out of Scope

- LDtk level layout import (tile placement) — this spec covers tile properties only
- Location transition animations / loading screens
- Multiplayer location syncing
- CI/CD automation of the pipeline
- Krita AI Diffusion refinement step

## Dependencies

| Component | Source |
|---|---|
| Pillow (Python) | pip — image processing for preprocessing |
| LDtk JSON | `project/ldtk/legend-dad.ldtk` — must exist with IntGrid layers |
| run_godot_checked.py | Vendored from `project-agent-union/scripts/` |
| palette_swap.gdshader | Already exists in project |
| PaletteManager | Already exists in project |
| TilesetFactory | Already exists in project (fallback) |
