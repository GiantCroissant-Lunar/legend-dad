# Dev Log: LDtk Tile Placement + Tileset Pipeline Fix

**Date:** 2026-04-14
**Focus:** Replace hardcoded tile arrays with LDtk-driven placement, fix tileset generation pipeline end-to-end

## What Was Done

### LDtk Tile Placement Pipeline (8 tasks)
- `LdtkImporter` — added `autoLayerTiles` parsing with px→grid and src→atlas coordinate conversion
- `LdtkLevelPlacer` — new static utility class for tile placement + collision grid building
- `LocationManager` — added LDtk project loading, collision grid storage, web PCK fetch via HTTPRequest
- `s_action_processor` — walkability now reads from LocationManager collision grid instead of TileSet custom data
- `main.gd` — removed hardcoded `FATHER_MAP`/`SON_MAP`, uses LDtk-driven placement with era overlays (base Terrain + Terrain_Father/Terrain_Son)
- Fallback layout for when LDtk levels are unpainted
- LDtk symlink into Godot project (`project/hosts/complete-app/ldtk → ../../ldtk`)
- Dynamic camera zoom (`viewport_height / map_pixel_height`) so tiles stay readable at any resolution

### LDtk Content Population
- Extended `ldtk_sync.py` with Terrain_Father and Terrain_Son layer definitions (40 IntGrid values each)
- All 7 levels populated with valid `layerInstances` (5 layers each)
- Hand-designed `Whispering_Woods_Edge` collision + terrain layout (20x16 tiles)

### Tileset Generation
- Generated all 3 biome tilesets via ComfyUI (field, dungeon, town)
- Fixed LoRA filename (`pixel-art-xl-v1.1` → `pixel-art-xl`)

### Grayscale + Palette Fixes
- Fixed warm-tone contamination: `.convert("L")` in tileset_preprocess.py
- Fixed 2-color palette issue: PixelArt-Detector's grayscale quantizer was crushing 182 gray levels to 3. Now reads from pixelated stage (pre-palette-conversion) and requantizes to exactly 16 evenly-spaced levels so all palette colors are used
- All 3 atlases now produce 16 distinct gray values for full palette shader utilization

### Tile Classifier
- New `tile_classifier.py` script: analyzes each 32x32 cell by brightness, edge density, and variance, then rearranges atlas so position N contains art matching IntGrid value N
- Per-biome visual profiles for all 40 IntGrid values
- Taskfile command: `task tileset:classify -- field`

### PCK Web Loading
- `/pck/` HTTP endpoint on game server (port 3000) serves PCK files from build artifacts
- `LocationManager._fetch_pck_web()` — HTTPRequest → `user://` save → `load_resource_pack()`
- `*.ldtk` added to web export include filter
- IntGrid CSV → atlas coord mapping as fallback when auto-layer rules aren't configured

### Direct IntGrid-to-Atlas Mapping
- When LDtk auto-layer rules aren't configured, `intgrid_to_tiles()` maps IntGrid value N directly to atlas coords (N%16, N/16)
- This matches pck_manifest.py convention and enables real PCK tiles without auto-layer rules

## Full Tileset Pipeline Command

```bash
task comfyui:tileset -- --biome=field    # Generate raw sheet via SDXL
task tileset:preprocess -- field          # Grayscale + 16-level requantization
task tileset:classify -- field            # Rearrange to semantic IntGrid order
task pck:build -- whispering-woods        # Build PCK with ordered atlas
task build                                # Web export
```

## Test Results
- 8 GUT tests pass (3 scripts)
- 70 pytest pass
- 6 vitest pass (1 skipped)

## Files Created/Modified

| File | Change |
|------|--------|
| `scripts/ldtk_importer.gd` | autoLayerTiles parsing, null layerInstances guard |
| `scripts/ldtk_level_placer.gd` | NEW: tile placement + collision grid + intgrid_to_tiles |
| `scripts/main.gd` | LDtk-driven placement, camera zoom, fallback layout |
| `scripts/location_manager.gd` | LDtk project loading, collision grid, web PCK fetch, force_fallback |
| `ecs/systems/s_action_processor.gd` | LocationManager.is_walkable() for walkability |
| `scripts/tile_classifier.py` | NEW: automated atlas rearrangement |
| `scripts/tileset_preprocess.py` | Pixelated stage input, 16-level requantization |
| `scripts/ldtk_sync.py` | Terrain_Father/Son layers, IntGrid vocabulary, layerInstance generation |
| `tests/test_ldtk_importer.gd` | NEW: 3 GUT tests |
| `tests/test_ldtk_level_placer.gd` | NEW: 4 GUT tests |
| `tests/test_tileset_preprocess.py` | Updated for requantization behavior |
| `export_presets.cfg` | Include *.ldtk in web export |
| `Taskfile.yml` | Added tileset:classify command |
| `project/ldtk/legend-dad.ldtk` | Populated with layers and level data |

## 19 commits this session
