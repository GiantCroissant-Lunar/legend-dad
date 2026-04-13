# LDtk Tile Placement Design

## Summary

Replace hardcoded `FATHER_MAP` / `SON_MAP` tile arrays in `main.gd` with runtime LDtk level parsing. Tile layouts are authored in LDtk using IntGrid layers with auto-layer rules. Visual tiles and walkability are fully decoupled. Era switching uses a shared base layer with per-era overlay layers.

## Architecture

### Data Flow

```
LDtk (legend-dad.ldtk)
  ├─ Collision layer (IntGrid) ──────────────────→ walkability metadata
  ├─ Terrain layer (IntGrid + Auto-layer) ───────→ base visual tiles
  ├─ Terrain_Father layer (IntGrid + Auto-layer) → father-era overrides
  └─ Terrain_Son layer (IntGrid + Auto-layer) ──→ son-era overrides
        │
        ▼
  ldtk_importer.gd parses autoLayerTiles at runtime
        │
        ▼
  main.gd builds TileMapLayer:
    1. Place base Terrain auto-layer tiles
    2. Overlay era-specific tiles (Father or Son)
    3. Read Collision IntGrid for walkability
    4. Apply palette shader from PCK
```

### Separation of Concerns

| System | Owns | Format |
|--------|------|--------|
| LDtk | Level layout (which tile goes where) + auto-layer rules | `.ldtk` JSON |
| PCK pipeline | Art assets (atlas texture + palette PNGs) | `.pck` with `.tres` + `.png` |
| Runtime | Combining layout + art + shader | GDScript |

## LDtk Layer Structure

Layers per level (top to bottom):

| Layer | Type | Purpose |
|-------|------|---------|
| Entities | Entities | Characters, zones, locations |
| Terrain_Son | IntGrid + Auto-layer | Son-era overrides (empty = use base) |
| Terrain_Father | IntGrid + Auto-layer | Father-era overrides (empty = use base) |
| Terrain | IntGrid + Auto-layer | Shared base tiles (common to both eras) |
| Collision | IntGrid | Walkability (solid/empty/water/pit) |

### Auto-layer Rules

- Each Terrain layer references the biome's atlas PNG as its tileset in LDtk
- Auto-layer rules map IntGrid values to atlas tile regions
- LDtk resolves rules at save time and exports `autoLayerTiles` arrays with grid positions + atlas source rects

### IntGrid Vocabulary

Same values defined in `pck_manifest.py`, shared across all Terrain layers:

- **Universal (0-9):** void, ground, wall, water_shallow, water_deep, pit, door, stairs_up, stairs_down, bridge
- **Field (10-19):** tall_grass, bush, tree_trunk, fallen_log, cliff_edge, path_dirt, path_stone, stream_crossing, undergrowth, hollow
- **Dungeon (20-29):** cave_floor, cave_wall, lava, mine_track, cracked_floor, ore_vein, rubble, crystal, ice_floor, dark_zone
- **Town (30-39):** cobblestone, fence, garden, market_stall, well_fountain, building_wall, interior_floor, counter, furniture, signpost_lamp

### Collision IntGrid Values (separate layer)

- `0` = empty (walkable)
- `1` = solid (not walkable)
- `2` = water (not walkable)
- `3` = pit (not walkable)

## Runtime Integration

### Era Logic

- **Father era:** Base `Terrain` auto-layer tiles + overwrite with `Terrain_Father` non-empty cells
- **Son era:** Base `Terrain` auto-layer tiles + overwrite with `Terrain_Son` non-empty cells
- On `swap_era()`: clear tilemap, re-place base + new era overlay, swap palette texture

### ldtk_importer.gd Changes

Currently parses IntGrid CSV and entity layers. Needs to also extract `autoLayerTiles` arrays from each layer.

**New data returned per layer:**
- `autoLayerTiles`: array of `{position: Vector2i, atlas_coords: Vector2i}` — resolved tile placements from LDtk auto-layer rules
- Existing `intgrid_csv` data preserved for Collision layer walkability

**LDtk autoLayerTiles format** (from LDtk JSON export):
```json
{
  "px": [x_px, y_px],
  "src": [atlas_x_px, atlas_y_px],
  "t": tile_id,
  "f": flip_bits
}
```

Convert `px` to grid coords (`px / tile_size`) and `src` to atlas coords (`src / tile_size`).

### main.gd Changes

**Remove:**
- `FATHER_MAP` and `SON_MAP` constants
- Hardcoded tile placement in `_build_game_view`

**New flow:**
1. `LocationManager.load_location("whispering-woods")` — loads PCK (tileset + palettes)
2. Parse LDtk level via `ldtk_importer.gd` — extract auto-layer tiles for Terrain, Terrain_Father, Terrain_Son, and Collision IntGrid
3. Build `TileMapLayer` using PCK's tileset
4. Place base Terrain auto-layer tiles
5. Overlay era-specific tiles on top
6. Store Collision IntGrid data for walkability checks
7. Apply palette shader for current era

### Collision Handling

- Collision IntGrid stays as runtime metadata, not visual tiles
- Walkability checks read from Collision layer data, not from TileSet custom data
- Fully decoupled from visual tile selection

### Fallback (No PCK)

- LDtk layout still loads (independent of art assets)
- `TilesetFactory` provides placeholder tileset (colored rectangles)
- No palette shader applied
- Tiles placed in correct positions from LDtk, just with placeholder visuals

### Fallback (No Auto-layer Tiles)

- If `autoLayerTiles` is empty for a layer (auto-layer rules not yet authored in LDtk), that layer is silently skipped
- The game still runs — it just shows fewer tiles until rules are painted
- Collision IntGrid data is independent of auto-layers and always works

### Level-to-Location Mapping

Defined in `pck_manifest.py` and reused at runtime:

| Location | Biome | LDtk Levels |
|----------|-------|-------------|
| whispering-woods | field | Whispering_Woods_Edge, Whispering_Woods_Deep |
| thornwall-market | town | Thornwall_Market, Thornwall_North_Gate, Thornwall_Elder_Quarter |
| iron-peaks-mine | dungeon | Iron_Peaks_Trail, Iron_Peaks_Upper_Mines |

## Scope

### This Session

- Wire `ldtk_importer.gd` to parse `autoLayerTiles` from LDtk JSON
- Update `main.gd` to use LDtk-driven tile placement instead of hardcoded arrays
- Implement era overlay logic (base + Father/Son layer merging)
- Collision IntGrid as walkability metadata
- Fallback path when no PCK exists

### Deferred

- Painting actual levels in LDtk (requires atlas art from ComfyUI pipeline)
- Auto-layer rule authoring in LDtk editor (manual step, not code)
- Adding `Terrain_Father` and `Terrain_Son` layers to the `.ldtk` file (manual LDtk editor step)
- Grayscale palette fix (separate workstream)

## Files Affected

| File | Change |
|------|--------|
| `project/hosts/complete-app/scripts/ldtk_importer.gd` | Add `autoLayerTiles` parsing |
| `project/hosts/complete-app/scripts/main.gd` | Remove hardcoded maps, use LDtk-driven placement |
| `project/hosts/complete-app/scripts/location_manager.gd` | Minor: ensure LDtk path accessible alongside PCK |
