# PCK Tileset Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an end-to-end pipeline from ComfyUI grayscale tilesets to Godot runtime rendering via dynamically loaded PCK files, with palette shader era swapping and graceful fallback.

**Architecture:** Python scripts handle image preprocessing and LDtk data extraction. Godot headless creates TileSet resources natively and packs them into PCK files. A LocationManager autoload handles runtime load/unload with palette shader application and TilesetFactory fallback.

**Tech Stack:** Python (Pillow), Godot 4.6.2 (GDScript), LDtk JSON, go-task Taskfile

**Spec:** `vault/specs/2026-04-14-pck-tileset-pipeline-design.md`

---

## File Map

### New files

| File | Responsibility |
|---|---|
| `scripts/run_godot_checked.py` | Vendored Godot CLI wrapper — catches false-green exits |
| `scripts/tileset_preprocess.py` | Slice 512×512 ComfyUI output into clean 32px tile atlas |
| `scripts/pck_manifest.py` | Read LDtk IntGrid data, generate manifest.json for Godot |
| `project/hosts/complete-app/scripts/pck_builder.gd` | Godot tool script — reads manifest, creates TileSet, packs PCK |
| `project/hosts/complete-app/scripts/location_manager.gd` | Autoload — runtime PCK load/unload, palette shader, fallback |
| `project/hosts/complete-app/data/locations.json` | Location registry (name → biome + PCK filename) |
| `tests/test_tileset_preprocess.py` | Pytest tests for preprocessing script |
| `tests/test_pck_manifest.py` | Pytest tests for manifest generator |

### Modified files

| File | Change |
|---|---|
| `project/hosts/complete-app/project.godot` | Add LocationManager autoload |
| `project/hosts/complete-app/scripts/main.gd` | Use LocationManager instead of direct TilesetFactory calls |
| `Taskfile.yml` | Add tileset:preprocess, pck:manifest, pck:build commands |

---

## Task 1: Vendor run_godot_checked.py

**Files:**
- Create: `scripts/run_godot_checked.py`

- [ ] **Step 1: Copy the checked runner from project-agent-union**

```bash
cp /Users/apprenticegc/Work/project-agent-union/scripts/run_godot_checked.py scripts/run_godot_checked.py
chmod +x scripts/run_godot_checked.py
```

- [ ] **Step 2: Verify it works with GUT**

```bash
python3 scripts/run_godot_checked.py \
  /Users/apprenticegc/Work/lunar-horse/tools/Godot.app/Contents/MacOS/Godot \
  --headless --path project/hosts/complete-app \
  -s addons/gut/gut_cmdln.gd -gexit
```

Expected: GUT runs, 1 test passes, script exits 0.

- [ ] **Step 3: Commit**

```bash
git add scripts/run_godot_checked.py
git commit -m "chore: vendor run_godot_checked.py from project-agent-union"
```

---

## Task 2: Tileset preprocessing script + tests

**Files:**
- Create: `scripts/tileset_preprocess.py`
- Create: `tests/test_tileset_preprocess.py`

- [ ] **Step 1: Write the test**

Create `tests/test_tileset_preprocess.py`:

```python
"""Tests for tileset_preprocess.py — slice and reassemble tile atlas."""
from pathlib import Path
import pytest
from PIL import Image


@pytest.fixture
def sample_512(tmp_path: Path) -> Path:
    """Create a 512x512 test image with a 16x16 grid of 32px cells.
    Each cell has a unique gray value so we can verify slicing."""
    img = Image.new("L", (512, 512), 0)
    for row in range(16):
        for col in range(16):
            gray = (row * 16 + col) % 256
            for y in range(row * 32, (row + 1) * 32):
                for x in range(col * 32, (col + 1) * 32):
                    img.putpixel((x, y), gray)
    path = tmp_path / "grayscale_tileset_00001_.png"
    img.save(path)
    return tmp_path


def test_preprocess_creates_atlas(sample_512: Path):
    from scripts.tileset_preprocess import preprocess_atlas

    output = preprocess_atlas(
        input_dir=sample_512,
        biome="test",
        tile_size=32,
    )
    assert output.exists()
    assert output.name == "atlas_32x32.png"
    img = Image.open(output)
    assert img.size == (512, 512)


def test_preprocess_preserves_cell_values(sample_512: Path):
    from scripts.tileset_preprocess import preprocess_atlas

    output = preprocess_atlas(
        input_dir=sample_512,
        biome="test",
        tile_size=32,
    )
    img = Image.open(output)
    # Check cell (0,0) center pixel
    assert img.getpixel((16, 16)) == 0
    # Check cell (1,0) center pixel — should be gray=1
    assert img.getpixel((32 + 16, 16)) == 1
    # Check cell (0,1) center pixel — should be gray=16
    assert img.getpixel((16, 32 + 16)) == 16


def test_preprocess_rejects_missing_input(tmp_path: Path):
    from scripts.tileset_preprocess import preprocess_atlas

    with pytest.raises(FileNotFoundError):
        preprocess_atlas(input_dir=tmp_path, biome="nonexistent", tile_size=32)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_tileset_preprocess.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.tileset_preprocess'`

- [ ] **Step 3: Write the preprocessing script**

Create `scripts/tileset_preprocess.py`:

```python
#!/usr/bin/env python3
"""Slice a ComfyUI grayscale tileset into clean 32px cells and reassemble.

Usage:
    python3 scripts/tileset_preprocess.py --biome=field --tile-size=32

Input:  build/tilesets/{biome}/grayscale_tileset_*.png (512x512)
Output: build/tilesets/{biome}/atlas_32x32.png (512x512, clean grid)
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "build" / "tilesets"


def preprocess_atlas(
    input_dir: Path,
    biome: str,
    tile_size: int = 32,
) -> Path:
    """Slice source image into grid cells and reassemble a clean atlas.

    Args:
        input_dir: Directory containing grayscale_tileset_*.png files.
                   If a biome subdirectory exists, it's used automatically.
        biome: Biome name (used for subdirectory lookup).
        tile_size: Size of each tile in pixels.

    Returns:
        Path to the output atlas PNG.

    Raises:
        FileNotFoundError: If no source image is found.
    """
    biome_dir = input_dir / biome if (input_dir / biome).is_dir() else input_dir
    candidates = sorted(biome_dir.glob("grayscale_tileset_*.png"))
    if not candidates:
        raise FileNotFoundError(
            f"No grayscale_tileset_*.png found in {biome_dir}"
        )

    source_path = candidates[-1]  # Use the latest
    source = Image.open(source_path)
    width, height = source.size
    cols = width // tile_size
    rows = height // tile_size

    # Create clean output image
    output = Image.new(source.mode, (cols * tile_size, rows * tile_size), 0)

    for row in range(rows):
        for col in range(cols):
            left = col * tile_size
            upper = row * tile_size
            cell = source.crop((left, upper, left + tile_size, upper + tile_size))
            output.paste(cell, (left, upper))

    output_path = biome_dir / f"atlas_{tile_size}x{tile_size}.png"
    output.save(output_path)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Preprocess ComfyUI tileset into clean atlas")
    parser.add_argument("--biome", required=True, help="Biome name (field, dungeon, town)")
    parser.add_argument("--tile-size", type=int, default=32, help="Tile size in pixels (default: 32)")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR, help="Input directory")
    args = parser.parse_args()

    try:
        output = preprocess_atlas(
            input_dir=args.input_dir,
            biome=args.biome,
            tile_size=args.tile_size,
        )
        print(f"Atlas written to {output}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests**

```bash
python3 -m pytest tests/test_tileset_preprocess.py -v
```

Expected: All 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/tileset_preprocess.py tests/test_tileset_preprocess.py
git commit -m "feat: add tileset preprocessing script with tests"
```

---

## Task 3: PCK manifest generator + tests

**Files:**
- Create: `scripts/pck_manifest.py`
- Create: `tests/test_pck_manifest.py`

- [ ] **Step 1: Write the test**

Create `tests/test_pck_manifest.py`:

```python
"""Tests for pck_manifest.py — generate PCK build manifest from LDtk data."""
from pathlib import Path
import json
import pytest
from PIL import Image


@pytest.fixture
def mock_ldtk(tmp_path: Path) -> Path:
    """Create a minimal LDtk project file with IntGrid values."""
    ldtk = {
        "levels": [
            {
                "identifier": "Whispering_Woods_Edge",
                "uid": 100,
                "iid": "aaa-bbb",
                "worldX": 0,
                "worldY": 0,
                "pxWid": 320,
                "pxHei": 256,
                "layerInstances": [
                    {
                        "__identifier": "Collision",
                        "__type": "IntGrid",
                        "__gridSize": 32,
                        "__cWid": 10,
                        "__cHei": 8,
                        "layerDefUid": 1,
                        "intGridCsv": [1, 1, 0, 0, 0, 0, 0, 0, 0, 0] * 8,
                    }
                ],
            }
        ],
        "defs": {
            "layers": [
                {
                    "uid": 1,
                    "identifier": "Collision",
                    "__type": "IntGrid",
                    "intGridValues": [
                        {"value": 0, "identifier": "empty"},
                        {"value": 1, "identifier": "solid"},
                    ],
                }
            ]
        },
    }
    path = tmp_path / "test.ldtk"
    path.write_text(json.dumps(ldtk))
    return path


@pytest.fixture
def mock_atlas(tmp_path: Path) -> Path:
    """Create a dummy atlas image."""
    img = Image.new("L", (512, 512), 128)
    path = tmp_path / "atlas_32x32.png"
    img.save(path)
    return path


@pytest.fixture
def mock_hex(tmp_path: Path) -> Path:
    """Create a dummy palette hex file."""
    path = tmp_path / "test.hex"
    colors = [f"#{i:02x}{i:02x}{i:02x}" for i in range(0, 256, 16)]
    path.write_text("\n".join(colors) + "\n")
    return path


def test_generate_manifest(mock_ldtk: Path, mock_atlas: Path, mock_hex: Path, tmp_path: Path):
    from scripts.pck_manifest import generate_manifest

    manifest = generate_manifest(
        ldtk_path=mock_ldtk,
        location="whispering-woods",
        biome="field",
        atlas_path=mock_atlas,
        father_hex=mock_hex,
        son_hex=mock_hex,
        output_dir=tmp_path / "output",
    )
    assert manifest["location"] == "whispering-woods"
    assert manifest["biome"] == "field"
    assert manifest["tile_size"] == 32
    assert manifest["grid_columns"] == 16
    assert manifest["grid_rows"] == 16
    assert Path(manifest["palettes"]["father"]).exists()
    assert Path(manifest["palettes"]["son"]).exists()
    # Manifest JSON file should exist
    assert (tmp_path / "output" / "manifest.json").exists()


def test_hex_to_palette_png(mock_hex: Path, tmp_path: Path):
    from scripts.pck_manifest import hex_to_palette_png

    output = hex_to_palette_png(mock_hex, tmp_path / "palette.png")
    assert output.exists()
    img = Image.open(output)
    assert img.size[1] == 1  # 1 pixel tall
    assert img.size[0] == 16  # 16 colors
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_pck_manifest.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write the manifest generator**

Create `scripts/pck_manifest.py`:

```python
#!/usr/bin/env python3
"""Generate PCK build manifest from LDtk data and biome IntGrid vocabulary.

Usage:
    python3 scripts/pck_manifest.py --location=whispering-woods

Reads:
  - project/ldtk/legend-dad.ldtk (IntGrid layer data)
  - vault/world/biomes/_conventions.md + {biome}.md (IntGrid vocabulary)
  - build/tilesets/{biome}/atlas_32x32.png
  - project/comfyui/palettes/{palette-name}.hex

Writes:
  - build/_artifacts/pck/{location}/manifest.json
  - build/_artifacts/pck/{location}/palette_father.png (16x1)
  - build/_artifacts/pck/{location}/palette_son.png (16x1)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Location → biome + palette mapping
# Matches project/hosts/complete-app/data/locations.json
LOCATION_CONFIG = {
    "whispering-woods": {
        "biome": "field",
        "father_palette": "deep-forest-16",
        "son_palette": "deep-forest-16",  # Same palette, different shader mapping in future
        "ldtk_levels": ["Whispering_Woods_Edge", "Whispering_Woods_Deep"],
    },
    "thornwall-market": {
        "biome": "town",
        "father_palette": "fantasy-rpg",
        "son_palette": "fantasy-rpg",
        "ldtk_levels": ["Thornwall_Market", "Thornwall_North_Gate", "Thornwall_Elder_Quarter"],
    },
    "iron-peaks-mine": {
        "biome": "dungeon",
        "father_palette": "damage-dice-10-6",
        "son_palette": "damage-dice-10-6",
        "ldtk_levels": ["Iron_Peaks_Trail", "Iron_Peaks_Upper_Mines"],
    },
}

# Universal IntGrid values (0-9) — shared across all biomes
UNIVERSAL_INTGRID = {
    0: {"name": "void", "walkable": False},
    1: {"name": "ground", "walkable": True},
    2: {"name": "wall", "walkable": False},
    3: {"name": "water_shallow", "walkable": True},
    4: {"name": "water_deep", "walkable": False},
    5: {"name": "pit", "walkable": False},
    6: {"name": "door", "walkable": True},
    7: {"name": "stairs_up", "walkable": True},
    8: {"name": "stairs_down", "walkable": True},
    9: {"name": "bridge", "walkable": True},
}

# Biome-specific IntGrid values
BIOME_INTGRID = {
    "field": {
        10: {"name": "tall_grass", "walkable": True},
        11: {"name": "bush", "walkable": False},
        12: {"name": "tree_trunk", "walkable": False},
        13: {"name": "fallen_log", "walkable": False},
        14: {"name": "cliff_edge", "walkable": False},
        15: {"name": "path_dirt", "walkable": True},
        16: {"name": "path_stone", "walkable": True},
        17: {"name": "stream_crossing", "walkable": True},
        18: {"name": "undergrowth", "walkable": True},
        19: {"name": "hollow", "walkable": True},
    },
    "dungeon": {
        20: {"name": "cave_floor", "walkable": True},
        21: {"name": "cave_wall", "walkable": False},
        22: {"name": "lava", "walkable": False},
        23: {"name": "mine_track", "walkable": True},
        24: {"name": "cracked_floor", "walkable": True},
        25: {"name": "ore_vein", "walkable": False},
        26: {"name": "rubble", "walkable": False},
        27: {"name": "crystal", "walkable": False},
        28: {"name": "ice_floor", "walkable": True},
        29: {"name": "dark_zone", "walkable": True},
    },
    "town": {
        30: {"name": "cobblestone", "walkable": True},
        31: {"name": "fence", "walkable": False},
        32: {"name": "garden", "walkable": False},
        33: {"name": "market_stall", "walkable": False},
        34: {"name": "well_fountain", "walkable": False},
        35: {"name": "building_wall", "walkable": False},
        36: {"name": "interior_floor", "walkable": True},
        37: {"name": "counter", "walkable": False},
        38: {"name": "furniture", "walkable": False},
        39: {"name": "signpost_lamp", "walkable": False},
    },
}


def hex_to_palette_png(hex_path: Path, output_path: Path) -> Path:
    """Convert a .hex palette file to a 16x1 PNG image."""
    lines = hex_path.read_text().strip().splitlines()
    colors = []
    for line in lines:
        line = line.strip().lstrip("#")
        if len(line) == 6:
            r, g, b = int(line[0:2], 16), int(line[2:4], 16), int(line[4:6], 16)
            colors.append((r, g, b))
    if not colors:
        raise ValueError(f"No valid colors found in {hex_path}")
    img = Image.new("RGB", (len(colors), 1))
    for i, color in enumerate(colors):
        img.putpixel((i, 0), color)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path


def generate_manifest(
    ldtk_path: Path,
    location: str,
    biome: str,
    atlas_path: Path,
    father_hex: Path,
    son_hex: Path,
    output_dir: Path,
    tile_size: int = 32,
) -> dict:
    """Generate a PCK build manifest from LDtk data.

    Returns the manifest dict and writes it + palette PNGs to output_dir.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate palette PNGs
    father_png = hex_to_palette_png(father_hex, output_dir / "palette_father.png")
    son_png = hex_to_palette_png(son_hex, output_dir / "palette_son.png")

    # Read atlas dimensions to compute grid
    atlas_img = Image.open(atlas_path)
    grid_columns = atlas_img.size[0] // tile_size
    grid_rows = atlas_img.size[1] // tile_size

    # Build tile property list from IntGrid vocabulary
    intgrid = {**UNIVERSAL_INTGRID, **BIOME_INTGRID.get(biome, {})}
    tiles = []
    for row in range(grid_rows):
        for col in range(grid_columns):
            # Default tile: decoration, walkable
            tile_index = row * grid_columns + col
            # Map atlas position to IntGrid value if within known range
            intgrid_value = tile_index if tile_index in intgrid else -1
            if intgrid_value >= 0 and intgrid_value in intgrid:
                entry = intgrid[intgrid_value]
                tiles.append({
                    "atlas_x": col,
                    "atlas_y": row,
                    "intgrid": intgrid_value,
                    "type": entry["name"],
                    "walkable": entry["walkable"],
                })
            else:
                tiles.append({
                    "atlas_x": col,
                    "atlas_y": row,
                    "intgrid": -1,
                    "type": "decoration",
                    "walkable": True,
                })

    manifest = {
        "location": location,
        "biome": biome,
        "atlas_path": str(atlas_path.resolve()),
        "tile_size": tile_size,
        "grid_columns": grid_columns,
        "grid_rows": grid_rows,
        "palettes": {
            "father": str(father_png.resolve()),
            "son": str(son_png.resolve()),
        },
        "tiles": tiles,
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate PCK manifest from LDtk data")
    parser.add_argument("--location", required=True, help="Location name (e.g. whispering-woods)")
    parser.add_argument("--ldtk", type=Path, default=PROJECT_ROOT / "project" / "ldtk" / "legend-dad.ldtk")
    args = parser.parse_args()

    location = args.location
    if location not in LOCATION_CONFIG:
        print(f"Error: Unknown location '{location}'. Known: {list(LOCATION_CONFIG.keys())}", file=sys.stderr)
        return 1

    config = LOCATION_CONFIG[location]
    biome = config["biome"]
    palettes_dir = PROJECT_ROOT / "project" / "comfyui" / "palettes"
    atlas_path = PROJECT_ROOT / "build" / "tilesets" / biome / "atlas_32x32.png"

    if not atlas_path.exists():
        print(f"Error: Atlas not found at {atlas_path}. Run 'task tileset:preprocess -- {biome}' first.", file=sys.stderr)
        return 1

    output_dir = PROJECT_ROOT / "build" / "_artifacts" / "pck" / location

    manifest = generate_manifest(
        ldtk_path=args.ldtk,
        location=location,
        biome=biome,
        atlas_path=atlas_path,
        father_hex=palettes_dir / f"{config['father_palette']}.hex",
        son_hex=palettes_dir / f"{config['son_palette']}.hex",
        output_dir=output_dir,
    )

    print(f"Manifest written to {output_dir / 'manifest.json'}")
    print(f"  Location: {manifest['location']}")
    print(f"  Biome: {manifest['biome']}")
    print(f"  Tiles: {len(manifest['tiles'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests**

```bash
python3 -m pytest tests/test_pck_manifest.py -v
```

Expected: All 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/pck_manifest.py tests/test_pck_manifest.py
git commit -m "feat: add PCK manifest generator with LDtk IntGrid data"
```

---

## Task 4: Location registry JSON

**Files:**
- Create: `project/hosts/complete-app/data/locations.json`

- [ ] **Step 1: Create the locations registry**

Create `project/hosts/complete-app/data/locations.json`:

```json
{
	"whispering-woods": {
		"biome": "field",
		"pck": "whispering-woods.pck"
	},
	"thornwall-market": {
		"biome": "town",
		"pck": "thornwall-market.pck"
	},
	"iron-peaks-mine": {
		"biome": "dungeon",
		"pck": "iron-peaks-mine.pck"
	}
}
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/data/locations.json
git commit -m "feat: add location registry for PCK loading"
```

---

## Task 5: LocationManager autoload

**Files:**
- Create: `project/hosts/complete-app/scripts/location_manager.gd`
- Modify: `project/hosts/complete-app/project.godot`

- [ ] **Step 1: Create LocationManager**

Create `project/hosts/complete-app/scripts/location_manager.gd`:

```gdscript
class_name LocationManagerClass
extends Node

## Manages location PCK loading/unloading with palette shader support.
## Falls back to TilesetFactory when no PCK is available.
##
## Usage:
##   LocationManager.load_location("whispering-woods")
##   LocationManager.swap_era(C_TimelineEra.Era.SON)
##   LocationManager.unload_location()

signal location_loaded(location_name: String)
signal location_unloaded(location_name: String)

const LOCATIONS_PATH := "res://data/locations.json"
const PCK_BASE_DIR := "res://locations/"

var _current_location := ""
var _current_biome := ""
var _locations_registry := {}
var _father_tilemap: TileMapLayer
var _son_tilemap: TileMapLayer
var _father_palette: Texture2D
var _son_palette: Texture2D
var _tileset: TileSet
var _using_fallback := false


func _ready() -> void:
	_load_registry()


func _load_registry() -> void:
	if not FileAccess.file_exists(LOCATIONS_PATH):
		push_warning("LocationManager: locations.json not found at %s" % LOCATIONS_PATH)
		return
	var file := FileAccess.open(LOCATIONS_PATH, FileAccess.READ)
	var json := JSON.new()
	var err := json.parse(file.get_as_text())
	file.close()
	if err != OK:
		push_error("LocationManager: failed to parse locations.json: %s" % json.get_error_message())
		return
	_locations_registry = json.data


func load_location(location_name: String) -> void:
	if _current_location == location_name:
		return

	if not _current_location.is_empty():
		unload_location()

	if location_name not in _locations_registry:
		push_warning("LocationManager: unknown location '%s', using fallback" % location_name)
		_load_fallback(location_name)
		return

	var config: Dictionary = _locations_registry[location_name]
	var pck_filename: String = config.get("pck", "")
	var biome: String = config.get("biome", "")
	var pck_path := "res://%s" % pck_filename

	# Try loading PCK
	var pck_loaded := false
	if FileAccess.file_exists(pck_path):
		pck_loaded = ProjectSettings.load_resource_pack(pck_path)

	if pck_loaded:
		_load_from_pck(location_name, biome)
	else:
		push_warning("LocationManager: PCK not available for '%s', using fallback" % location_name)
		_load_fallback(location_name)


func _load_from_pck(location_name: String, biome: String) -> void:
	var loc_dir := PCK_BASE_DIR + location_name + "/"

	# Load TileSet
	_tileset = load(loc_dir + "tileset.tres") as TileSet
	if not _tileset:
		push_error("LocationManager: failed to load tileset from PCK for '%s'" % location_name)
		_load_fallback(location_name)
		return

	# Load palettes
	_father_palette = load(loc_dir + "palette_father.png") as Texture2D
	_son_palette = load(loc_dir + "palette_son.png") as Texture2D

	_current_location = location_name
	_current_biome = biome
	_using_fallback = false
	location_loaded.emit(location_name)


func _load_fallback(location_name: String) -> void:
	_tileset = TilesetFactory.create_tileset()
	_father_palette = null
	_son_palette = null
	_current_location = location_name
	_current_biome = _locations_registry.get(location_name, {}).get("biome", "")
	_using_fallback = true
	location_loaded.emit(location_name)


func unload_location() -> void:
	var old_name := _current_location
	_tileset = null
	_father_palette = null
	_son_palette = null
	_father_tilemap = null
	_son_tilemap = null
	_current_location = ""
	_current_biome = ""
	_using_fallback = false
	if not old_name.is_empty():
		location_unloaded.emit(old_name)


func create_tilemap_for_era(era: C_TimelineEra.Era) -> TileMapLayer:
	var tilemap := TileMapLayer.new()
	tilemap.name = "TileMapLayer"
	tilemap.tile_set = _tileset
	if era == C_TimelineEra.Era.FATHER:
		_father_tilemap = tilemap
	else:
		_son_tilemap = tilemap

	# Apply palette shader if we have palette textures (PCK mode)
	if not _using_fallback:
		var palette := _father_palette if era == C_TimelineEra.Era.FATHER else _son_palette
		if palette:
			PaletteManager.apply_palette(tilemap, palette)

	return tilemap


func swap_era(era: int) -> void:
	if _using_fallback:
		return  # Fallback tiles don't use palette shader
	var palette := _father_palette if era == C_TimelineEra.Era.FATHER else _son_palette
	if not palette:
		return
	if _father_tilemap:
		PaletteManager.swap_palette(_father_tilemap, palette)
	if _son_tilemap:
		PaletteManager.swap_palette(_son_tilemap, palette)


func get_current_location() -> String:
	return _current_location


func is_location_loaded() -> bool:
	return not _current_location.is_empty()


func is_using_fallback() -> bool:
	return _using_fallback


func get_tileset() -> TileSet:
	return _tileset
```

- [ ] **Step 2: Register as autoload in project.godot**

In `project/hosts/complete-app/project.godot`, add to the `[autoload]` section:

```
LocationManager="*res://scripts/location_manager.gd"
```

Add it after the existing `GameActions` entry.

- [ ] **Step 3: Verify Godot headless doesn't error**

```bash
python3 scripts/run_godot_checked.py \
  /Users/apprenticegc/Work/lunar-horse/tools/Godot.app/Contents/MacOS/Godot \
  --headless --path project/hosts/complete-app \
  -s addons/gut/gut_cmdln.gd -gexit
```

Expected: GUT still passes (1 test), no script errors from LocationManager.

- [ ] **Step 4: Commit**

```bash
git add project/hosts/complete-app/scripts/location_manager.gd project/hosts/complete-app/project.godot
git commit -m "feat: add LocationManager autoload with PCK loading and fallback"
```

---

## Task 6: Integrate LocationManager into main.gd

**Files:**
- Modify: `project/hosts/complete-app/scripts/main.gd`

- [ ] **Step 1: Update main.gd to use LocationManager**

Replace line 76 (`tileset = TilesetFactory.create_tileset()`) with:

```gdscript
	LocationManager.load_location("whispering-woods")
	tileset = LocationManager.get_tileset()
```

In `_switch_active_era()`, after the existing era swap logic (after `_update_layout()`), add:

```gdscript
	LocationManager.swap_era(active_era)
```

- [ ] **Step 2: Verify the game still runs**

```bash
python3 scripts/run_godot_checked.py \
  /Users/apprenticegc/Work/lunar-horse/tools/Godot.app/Contents/MacOS/Godot \
  --headless --path project/hosts/complete-app \
  -s addons/gut/gut_cmdln.gd -gexit
```

Expected: GUT still passes. LocationManager falls back to TilesetFactory (no PCK exists yet).

- [ ] **Step 3: Commit**

```bash
git add project/hosts/complete-app/scripts/main.gd
git commit -m "feat: integrate LocationManager into main.gd with fallback"
```

---

## Task 7: Godot PCK builder tool script

**Files:**
- Create: `project/hosts/complete-app/scripts/pck_builder.gd`

- [ ] **Step 1: Create the PCK builder script**

Create `project/hosts/complete-app/scripts/pck_builder.gd`:

```gdscript
extends SceneTree

## Headless tool script: reads a manifest.json and builds a location .pck file.
##
## Usage (via Taskfile):
##   python3 scripts/run_godot_checked.py \
##     $GODOT_PATH --headless --path project/hosts/complete-app \
##     --script scripts/pck_builder.gd -- --location=whispering-woods

const TILE_SIZE := 32


func _init() -> void:
	var location := _get_arg("--location")
	if location.is_empty():
		push_error("pck_builder: --location argument required")
		quit(1)
		return

	var project_root := _find_project_root()
	var manifest_path := project_root + "/build/_artifacts/pck/" + location + "/manifest.json"

	if not FileAccess.file_exists(manifest_path):
		push_error("pck_builder: manifest not found at %s" % manifest_path)
		quit(1)
		return

	var result := _build_pck(manifest_path, location, project_root)
	quit(0 if result else 1)


func _build_pck(manifest_path: String, location: String, project_root: String) -> bool:
	# Read manifest
	var file := FileAccess.open(manifest_path, FileAccess.READ)
	var json := JSON.new()
	var err := json.parse(file.get_as_text())
	file.close()
	if err != OK:
		push_error("pck_builder: failed to parse manifest: %s" % json.get_error_message())
		return false

	var manifest: Dictionary = json.data
	var tile_size: int = manifest.get("tile_size", TILE_SIZE)
	var grid_cols: int = manifest.get("grid_columns", 16)
	var grid_rows: int = manifest.get("grid_rows", 16)
	var tiles: Array = manifest.get("tiles", [])

	# Load atlas image
	var atlas_path: String = manifest.get("atlas_path", "")
	var atlas_image := Image.load_from_file(atlas_path)
	if atlas_image == null:
		push_error("pck_builder: failed to load atlas from %s" % atlas_path)
		return false

	var atlas_texture := ImageTexture.create_from_image(atlas_image)

	# Create TileSet
	var tileset := TileSet.new()
	tileset.tile_size = Vector2i(tile_size, tile_size)

	# Custom data layers
	tileset.add_custom_data_layer()
	tileset.set_custom_data_layer_name(0, "walkable")
	tileset.set_custom_data_layer_type(0, TYPE_BOOL)
	tileset.add_custom_data_layer()
	tileset.set_custom_data_layer_name(1, "tile_type")
	tileset.set_custom_data_layer_type(1, TYPE_STRING)

	# Atlas source
	var atlas_source := TileSetAtlasSource.new()
	atlas_source.texture = atlas_texture
	atlas_source.texture_region_size = Vector2i(tile_size, tile_size)
	tileset.add_source(atlas_source, 0)

	# Create tiles and assign properties
	for tile_data in tiles:
		var atlas_x: int = tile_data.get("atlas_x", 0)
		var atlas_y: int = tile_data.get("atlas_y", 0)
		var coords := Vector2i(atlas_x, atlas_y)
		atlas_source.create_tile(coords)
		var td := atlas_source.get_tile_data(coords, 0)
		td.set_custom_data("walkable", tile_data.get("walkable", true))
		td.set_custom_data("tile_type", tile_data.get("type", "decoration"))

	# Save TileSet resource
	var loc_dir := "res://locations/" + location + "/"
	DirAccess.make_dir_recursive_absolute(loc_dir)
	var save_err := ResourceSaver.save(tileset, loc_dir + "tileset.tres")
	if save_err != OK:
		push_error("pck_builder: failed to save tileset: %s" % error_string(save_err))
		return false

	# Copy atlas and palette PNGs into the location directory
	_copy_file(atlas_path, loc_dir + "atlas_32x32.png")
	var palettes: Dictionary = manifest.get("palettes", {})
	_copy_file(palettes.get("father", ""), loc_dir + "palette_father.png")
	_copy_file(palettes.get("son", ""), loc_dir + "palette_son.png")

	# Copy manifest for debugging
	_copy_file(manifest_path, loc_dir + "manifest.json")

	# Pack into PCK
	var pck_path := project_root + "/build/_artifacts/pck/" + location + ".pck"
	var packer := PCKPacker.new()
	var pck_err := packer.pck_start(pck_path)
	if pck_err != OK:
		push_error("pck_builder: failed to start PCK: %s" % error_string(pck_err))
		return false

	# Add all files in the location directory
	var dir := DirAccess.open(loc_dir)
	if dir:
		dir.list_dir_begin()
		var filename := dir.get_next()
		while filename != "":
			if not dir.current_is_dir():
				var full_path := loc_dir + filename
				var res_path := "res://locations/" + location + "/" + filename
				packer.add_file(res_path, full_path)
				print("  Packed: %s" % res_path)
			filename = dir.get_next()
		dir.list_dir_end()

	pck_err = packer.flush()
	if pck_err != OK:
		push_error("pck_builder: failed to flush PCK: %s" % error_string(pck_err))
		return false

	print("PCK written to %s" % pck_path)
	return true


func _copy_file(src: String, dst: String) -> void:
	if src.is_empty() or not FileAccess.file_exists(src):
		push_warning("pck_builder: source file not found: %s" % src)
		return
	var data := FileAccess.get_file_as_bytes(src)
	var out := FileAccess.open(dst, FileAccess.WRITE)
	out.store_buffer(data)
	out.close()


func _get_arg(prefix: String) -> String:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with(prefix + "="):
			return arg.substr(prefix.length() + 1)
		if arg.begins_with(prefix):
			return arg.substr(prefix.length())
	return ""


func _find_project_root() -> String:
	# Walk up from the Godot project dir to find the repo root (has Taskfile.yml)
	var dir := OS.get_executable_path().get_base_dir()
	# Use the project path (cwd when running --path)
	var project_path := ProjectSettings.globalize_path("res://")
	var current := project_path
	for i in range(10):
		if FileAccess.file_exists(current + "/Taskfile.yml"):
			return current.rstrip("/")
		current = current.get_base_dir()
	# Fallback: assume project/hosts/complete-app is 3 levels deep
	return ProjectSettings.globalize_path("res://").get_base_dir().get_base_dir().get_base_dir()
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/scripts/pck_builder.gd
git commit -m "feat: add Godot headless PCK builder tool script"
```

---

## Task 8: Taskfile commands

**Files:**
- Modify: `Taskfile.yml`

- [ ] **Step 1: Add tileset and PCK tasks to Taskfile.yml**

Add after the existing `test:e2e` task:

```yaml
  tileset:preprocess:
    desc: Slice and reassemble clean 32x32 tile atlas from ComfyUI output
    cmds:
      - python3 scripts/tileset_preprocess.py --biome={{.CLI_ARGS}} --tile-size=32

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

- [ ] **Step 2: Verify dry run works**

```bash
task tileset:preprocess -- field
```

Expected: If `build/tilesets/field/grayscale_tileset_*.png` exists from earlier ComfyUI run, creates `atlas_32x32.png`. If not, prints error about missing file.

- [ ] **Step 3: Commit**

```bash
git add Taskfile.yml
git commit -m "feat: add tileset:preprocess and pck:build taskfile commands"
```

---

## Task 9: Update Taskfile GUT command to use run_godot_checked.py

**Files:**
- Modify: `Taskfile.yml`

- [ ] **Step 1: Update test:godot to use the checked wrapper**

Replace the existing `test:godot` task:

```yaml
  test:godot:
    desc: Run Godot unit tests (GUT, headless)
    cmds:
      - >-
        python3 scripts/run_godot_checked.py
        {{.GODOT_PATH}} --headless
        --path {{.GODOT_PROJECT_DIR}}
        -s addons/gut/gut_cmdln.gd -gexit
```

- [ ] **Step 2: Verify it works**

```bash
task test:godot
```

Expected: GUT passes, exits cleanly via checked wrapper.

- [ ] **Step 3: Commit**

```bash
git add Taskfile.yml
git commit -m "fix: route test:godot through run_godot_checked.py"
```

---

## Task 10: End-to-end pipeline test

**Files:** None (verification only)

This task verifies the full pipeline works with the existing ComfyUI output from the earlier session.

- [ ] **Step 1: Preprocess the field tileset**

```bash
task tileset:preprocess -- field
```

Expected: `build/tilesets/field/atlas_32x32.png` created.

- [ ] **Step 2: Generate manifest**

```bash
task pck:manifest -- whispering-woods
```

Expected: `build/_artifacts/pck/whispering-woods/manifest.json` created with tile data.

- [ ] **Step 3: Build PCK**

```bash
task pck:build -- whispering-woods
```

Expected: `build/_artifacts/pck/whispering-woods.pck` created.

- [ ] **Step 4: Run all tests**

```bash
task test:python && task test:server && task test:godot
```

Expected: All tests pass including new preprocessing and manifest tests.

- [ ] **Step 5: Run the game to verify fallback works**

Build and serve the web game:

```bash
task build && task dev
```

Open `http://localhost:8080`. The game should still run using fallback tiles (colored rectangles) since the PCK isn't deployed yet.

---

## Task 11: Update AGENTS.md

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Add pipeline commands to Key Commands section**

After the test commands in the `## Key Commands` section, add:

```bash
task tileset:preprocess -- {biome}  # Slice ComfyUI output into clean atlas
task pck:manifest -- {location}     # Generate PCK manifest from LDtk data
task pck:build -- {location}        # Full PCK build (manifest + Godot pack)
```

- [ ] **Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: add tileset/PCK pipeline commands to AGENTS.md"
```
