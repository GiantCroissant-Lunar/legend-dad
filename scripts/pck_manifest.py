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

# Location -> biome + palette mapping
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

# Universal IntGrid values (0-9) -- shared across all biomes
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
        msg = f"No valid colors found in {hex_path}"
        raise ValueError(msg)
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
                tiles.append(
                    {
                        "atlas_x": col,
                        "atlas_y": row,
                        "intgrid": intgrid_value,
                        "type": entry["name"],
                        "walkable": entry["walkable"],
                    }
                )
            else:
                tiles.append(
                    {
                        "atlas_x": col,
                        "atlas_y": row,
                        "intgrid": -1,
                        "type": "decoration",
                        "walkable": True,
                    }
                )

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
        print(
            f"Error: Atlas not found at {atlas_path}. Run 'task tileset:preprocess -- {biome}' first.",
            file=sys.stderr,
        )
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
