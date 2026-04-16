"""Shared IntGrid vocabulary for LDtk collision + terrain layers.

Exposes the canonical name↔value mappings for the four-value Collision
IntGrid and the 40-value Terrain IntGrid. Used by:

- scripts/ldtk_sync.py (layer def generation + baked-in layouts)
- scripts/zone_layout_render.py (symbolic-name → int resolution)
- tests/* (validation fixtures)

Keep this file behavior-free. No I/O, no parsing, just constants and
pure lookups. Anything that imports this can assume it won't raise on
import.
"""

from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────
# Collision layer: 4 values, shared across all biomes.
# value 0 = walkable; values 1-3 all block movement (LdtkLevelPlacer
# treats any nonzero as blocking via BLOCKING_VALUES = [1, 2, 3]).
# ──────────────────────────────────────────────────────────────────────
INTGRID_COLLISION: list[dict] = [
    {"value": 0, "identifier": "empty", "color": "#000000", "tile": None, "groupUid": 0},
    {"value": 1, "identifier": "solid", "color": "#FFFFFF", "tile": None, "groupUid": 0},
    {"value": 2, "identifier": "water", "color": "#4488CC", "tile": None, "groupUid": 0},
    {"value": 3, "identifier": "pit", "color": "#332222", "tile": None, "groupUid": 0},
]

# ──────────────────────────────────────────────────────────────────────
# Terrain layer: 40 values split into biome groups.
# Universal (0-9): always valid regardless of zone biome.
# Field (10-19), Dungeon (20-29), Town (30-39): only valid when the
# zone declares a matching biome.
#
# When a new tile type is needed, prefer extending the universal group
# if it makes sense in every biome; otherwise pick the biome-specific
# range. Keep values dense — the runtime uses `value % 16` / `value / 16`
# to compute tile-atlas coords, so gaps are fine but reordering breaks
# saved levels.
# ──────────────────────────────────────────────────────────────────────
INTGRID_TERRAIN: list[dict] = [
    # Universal (0-9)
    {"value": 0, "identifier": "void", "color": "#000000", "tile": None, "groupUid": 0},
    {"value": 1, "identifier": "ground", "color": "#8B7355", "tile": None, "groupUid": 0},
    {"value": 2, "identifier": "wall", "color": "#555555", "tile": None, "groupUid": 0},
    {"value": 3, "identifier": "water_shallow", "color": "#6699CC", "tile": None, "groupUid": 0},
    {"value": 4, "identifier": "water_deep", "color": "#334466", "tile": None, "groupUid": 0},
    {"value": 5, "identifier": "pit", "color": "#332222", "tile": None, "groupUid": 0},
    {"value": 6, "identifier": "door", "color": "#AA7744", "tile": None, "groupUid": 0},
    {"value": 7, "identifier": "stairs_up", "color": "#CCAA66", "tile": None, "groupUid": 0},
    {"value": 8, "identifier": "stairs_down", "color": "#997744", "tile": None, "groupUid": 0},
    {"value": 9, "identifier": "bridge", "color": "#AA8855", "tile": None, "groupUid": 0},
    # Field biome (10-19)
    {"value": 10, "identifier": "tall_grass", "color": "#55AA44", "tile": None, "groupUid": 0},
    {"value": 11, "identifier": "bush", "color": "#337722", "tile": None, "groupUid": 0},
    {"value": 12, "identifier": "tree_trunk", "color": "#553311", "tile": None, "groupUid": 0},
    {"value": 13, "identifier": "fallen_log", "color": "#664422", "tile": None, "groupUid": 0},
    {"value": 14, "identifier": "cliff_edge", "color": "#887766", "tile": None, "groupUid": 0},
    {"value": 15, "identifier": "path_dirt", "color": "#AA8844", "tile": None, "groupUid": 0},
    {"value": 16, "identifier": "path_stone", "color": "#999988", "tile": None, "groupUid": 0},
    {"value": 17, "identifier": "stream_crossing", "color": "#77AACC", "tile": None, "groupUid": 0},
    {"value": 18, "identifier": "undergrowth", "color": "#448833", "tile": None, "groupUid": 0},
    {"value": 19, "identifier": "hollow", "color": "#2A3A1A", "tile": None, "groupUid": 0},
    # Dungeon biome (20-29)
    {"value": 20, "identifier": "cave_floor", "color": "#666655", "tile": None, "groupUid": 0},
    {"value": 21, "identifier": "cave_wall", "color": "#444433", "tile": None, "groupUid": 0},
    {"value": 22, "identifier": "lava", "color": "#CC4411", "tile": None, "groupUid": 0},
    {"value": 23, "identifier": "mine_track", "color": "#886644", "tile": None, "groupUid": 0},
    {"value": 24, "identifier": "cracked_floor", "color": "#777766", "tile": None, "groupUid": 0},
    {"value": 25, "identifier": "ore_vein", "color": "#99AA77", "tile": None, "groupUid": 0},
    {"value": 26, "identifier": "rubble", "color": "#555544", "tile": None, "groupUid": 0},
    {"value": 27, "identifier": "crystal", "color": "#88CCDD", "tile": None, "groupUid": 0},
    {"value": 28, "identifier": "ice_floor", "color": "#BBDDEE", "tile": None, "groupUid": 0},
    {"value": 29, "identifier": "dark_zone", "color": "#222222", "tile": None, "groupUid": 0},
    # Town biome (30-39)
    {"value": 30, "identifier": "cobblestone", "color": "#998877", "tile": None, "groupUid": 0},
    {"value": 31, "identifier": "fence", "color": "#775533", "tile": None, "groupUid": 0},
    {"value": 32, "identifier": "garden", "color": "#66AA55", "tile": None, "groupUid": 0},
    {"value": 33, "identifier": "market_stall", "color": "#CC9944", "tile": None, "groupUid": 0},
    {"value": 34, "identifier": "well_fountain", "color": "#5588AA", "tile": None, "groupUid": 0},
    {"value": 35, "identifier": "building_wall", "color": "#887766", "tile": None, "groupUid": 0},
    {"value": 36, "identifier": "interior_floor", "color": "#AA9977", "tile": None, "groupUid": 0},
    {"value": 37, "identifier": "counter", "color": "#776644", "tile": None, "groupUid": 0},
    {"value": 38, "identifier": "furniture", "color": "#665544", "tile": None, "groupUid": 0},
    {"value": 39, "identifier": "signpost_lamp", "color": "#CCBB44", "tile": None, "groupUid": 0},
]

# Which terrain values are valid for which biome. "universal" names are
# valid everywhere. Biome-specific names only resolve when the zone's
# biome field matches.
_BIOME_VALUE_RANGES: dict[str, range] = {
    "universal": range(0, 10),
    "field": range(10, 20),
    "dungeon": range(20, 30),
    "town": range(30, 40),
}


# Precomputed lookup maps for fast validation.
_COLLISION_NAME_TO_VALUE: dict[str, int] = {e["identifier"]: e["value"] for e in INTGRID_COLLISION}
_COLLISION_VALUE_TO_NAME: dict[int, str] = {e["value"]: e["identifier"] for e in INTGRID_COLLISION}
_TERRAIN_NAME_TO_VALUE: dict[str, int] = {e["identifier"]: e["value"] for e in INTGRID_TERRAIN}
_TERRAIN_VALUE_TO_NAME: dict[int, str] = {e["value"]: e["identifier"] for e in INTGRID_TERRAIN}


def collision_value(name: str) -> int:
    """Resolve a collision-layer symbol (e.g. 'solid') to its IntGrid value.

    Raises KeyError with a helpful message if the name isn't defined.
    """
    if name not in _COLLISION_NAME_TO_VALUE:
        valid = ", ".join(sorted(_COLLISION_NAME_TO_VALUE))
        raise KeyError(f"unknown collision symbol {name!r}; expected one of: {valid}")
    return _COLLISION_NAME_TO_VALUE[name]


def collision_name(value: int) -> str:
    """Resolve an IntGrid value back to its collision symbol."""
    if value not in _COLLISION_VALUE_TO_NAME:
        raise KeyError(f"collision value {value} is not defined in INTGRID_COLLISION")
    return _COLLISION_VALUE_TO_NAME[value]


def terrain_value(name: str, biome: str | None = None) -> int:
    """Resolve a terrain symbol (e.g. 'path_stone') to its IntGrid value.

    If `biome` is supplied, validates that the symbol is either universal
    (values 0-9) or belongs to that biome's range. This catches a 'field'
    zone trying to paint 'crystal' (a dungeon-only symbol) at validation
    time rather than letting it silently render the wrong tile.

    Passing biome=None skips the biome check — useful for tests and
    tooling that doesn't care about biome scoping.
    """
    if name not in _TERRAIN_NAME_TO_VALUE:
        valid = ", ".join(sorted(_TERRAIN_NAME_TO_VALUE))
        raise KeyError(f"unknown terrain symbol {name!r}; expected one of: {valid}")
    value = _TERRAIN_NAME_TO_VALUE[name]
    if biome is not None:
        universal = _BIOME_VALUE_RANGES["universal"]
        biome_range = _BIOME_VALUE_RANGES.get(biome)
        if biome_range is None:
            raise KeyError(
                f"unknown biome {biome!r}; expected one of: "
                + ", ".join(sorted(b for b in _BIOME_VALUE_RANGES if b != 'universal'))
            )
        if value not in universal and value not in biome_range:
            biome_names = sorted(
                n
                for n, v in _TERRAIN_NAME_TO_VALUE.items()
                if v in universal or v in biome_range
            )
            raise KeyError(
                f"terrain symbol {name!r} (value {value}) is not valid in biome "
                f"{biome!r}; valid symbols in this biome: {', '.join(biome_names)}"
            )
    return value


def terrain_name(value: int) -> str:
    """Resolve an IntGrid value back to its terrain symbol."""
    if value not in _TERRAIN_VALUE_TO_NAME:
        raise KeyError(f"terrain value {value} is not defined in INTGRID_TERRAIN")
    return _TERRAIN_VALUE_TO_NAME[value]


def biome_terrain_symbols(biome: str) -> list[str]:
    """Return the sorted list of terrain symbols valid for `biome`
    (universal + biome-specific).
    """
    universal = _BIOME_VALUE_RANGES["universal"]
    biome_range = _BIOME_VALUE_RANGES.get(biome)
    if biome_range is None:
        raise KeyError(f"unknown biome {biome!r}")
    return sorted(
        n for n, v in _TERRAIN_NAME_TO_VALUE.items() if v in universal or v in biome_range
    )
