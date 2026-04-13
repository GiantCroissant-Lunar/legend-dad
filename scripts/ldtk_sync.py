"""Sync vault entity definitions into an LDtk project file.

Reads import-manifest.json and generates/updates a .ldtk project file with
entity definitions, enum definitions, and layer definitions. Preserves
existing levels and entity instances when updating.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

# LDtk JSON format version (matches the schema we target)
LDTK_JSON_VERSION = "1.5.3"

# Default grid size for the pixel-art tile-based game
GRID_SIZE = 16

# Entity type colors (LDtk hex colors for visual distinction in editor)
ENTITY_COLORS = {
    "Character": "#BE4A2F",
    "Location": "#3B7D4F",
    "Faction": "#7B5EA7",
    "Quest": "#D4A03C",
    "Item": "#C97B3D",
    "Event": "#5B8EBE",
    "Lore": "#8B7355",
    "Creature": "#9B3B3B",
}

# Maps manifest type names to LDtk entity identifiers
TYPE_TO_ENTITY = {
    "character": "Character",
    "location": "Location",
    "zone": "Zone",
    "faction": "Faction",
    "quest": "Quest",
    "item": "Item",
    "event": "Event",
    "lore": "Lore",
    "bestiary": "Creature",
}

# Entity colors for Zone type
ENTITY_COLORS["Zone"] = "#4A8B6F"

# IntGrid values for collision layer
INTGRID_COLLISION = [
    {"value": 0, "identifier": "empty", "color": "#000000", "tile": None, "groupUid": 0},
    {"value": 1, "identifier": "solid", "color": "#FFFFFF", "tile": None, "groupUid": 0},
    {"value": 2, "identifier": "water", "color": "#4488CC", "tile": None, "groupUid": 0},
    {"value": 3, "identifier": "pit", "color": "#332222", "tile": None, "groupUid": 0},
]

# IntGrid values for terrain layers (universal + all biomes)
# Colors chosen for visual distinction in LDtk editor
INTGRID_TERRAIN = [
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


class UidAllocator:
    """Tracks and allocates unique integer IDs for LDtk objects."""

    def __init__(self, start: int = 1):
        self._next = start

    def next(self) -> int:
        uid = self._next
        self._next += 1
        return uid

    @property
    def next_uid(self) -> int:
        return self._next


def _make_iid() -> str:
    """Generate a UUID-style instance ID for LDtk."""
    return str(uuid.uuid4())


def _make_field_def(uid_alloc: UidAllocator, identifier: str, field_type: str, **kwargs) -> dict:
    """Create a minimal valid LDtk FieldDef."""
    fd = {
        "uid": uid_alloc.next(),
        "identifier": identifier,
        "type": field_type,
        "__type": _human_type(field_type),
        "isArray": False,
        "canBeNull": True,
        "allowOutOfLevelRef": True,
        "allowedRefTags": [],
        "allowedRefs": "Any",
        "autoChainRef": True,
        "editorAlwaysShow": False,
        "editorCutLongValues": True,
        "editorDisplayMode": "ValueOnly",
        "editorDisplayPos": "Above",
        "editorDisplayScale": 1.0,
        "editorLinkStyle": "StraightArrow",
        "editorShowInWorld": True,
        "exportToToc": False,
        "searchable": True,
        "symmetricalRef": False,
        "useForSmartColor": False,
        "defaultOverride": None,
        "doc": None,
        "min": None,
        "max": None,
        "regex": None,
        "textLanguageMode": None,
        "arrayMinLength": None,
        "arrayMaxLength": None,
        "acceptFileTypes": None,
        "tilesetUid": None,
    }
    fd.update(kwargs)
    return fd


def _human_type(field_type: str) -> str:
    """Convert LDtk field type to human-readable __type string."""
    mapping = {
        "F_String": "String",
        "F_Text": "String",
        "F_Int": "Int",
        "F_Float": "Float",
        "F_Bool": "Bool",
    }
    if field_type in mapping:
        return mapping[field_type]
    if field_type.startswith("F_Enum("):
        enum_name = field_type[7:-1]
        return f"LocalEnum.{enum_name}"
    return field_type


def _make_entity_def(uid_alloc: UidAllocator, identifier: str, color: str, field_defs: list[dict]) -> dict:
    """Create a minimal valid LDtk EntityDef."""
    return {
        "uid": uid_alloc.next(),
        "identifier": identifier,
        "width": GRID_SIZE,
        "height": GRID_SIZE,
        "color": color,
        "renderMode": "Rectangle",
        "tileRenderMode": "FitInside",
        "pivotX": 0.5,
        "pivotY": 1.0,
        "nineSliceBorders": [],
        "fieldDefs": field_defs,
        "fillOpacity": 0.08,
        "hollow": False,
        "keepAspectRatio": False,
        "limitBehavior": "MoveLastOne",
        "limitScope": "PerLevel",
        "lineOpacity": 1.0,
        "maxCount": 0,
        "resizableX": False,
        "resizableY": False,
        "showName": True,
        "tags": ["vault_entity"],
        "tileOpacity": 1.0,
        "allowOutOfBounds": False,
        "exportToToc": True,
        "tilesetId": None,
        "tileId": None,
        "tileRect": None,
        "doc": None,
        "uiTileRect": None,
        "minWidth": None,
        "maxWidth": None,
        "minHeight": None,
        "maxHeight": None,
    }


def _make_layer_def(uid_alloc: UidAllocator, identifier: str, layer_type: str, **kwargs) -> dict:
    """Create a minimal valid LDtk LayerDef."""
    ld = {
        "uid": uid_alloc.next(),
        "identifier": identifier,
        "type": layer_type,
        "__type": layer_type,
        "gridSize": GRID_SIZE,
        "displayOpacity": 1.0,
        "inactiveOpacity": 0.6,
        "pxOffsetX": 0,
        "pxOffsetY": 0,
        "parallaxFactorX": 0.0,
        "parallaxFactorY": 0.0,
        "parallaxScaling": True,
        "intGridValues": [],
        "intGridValuesGroups": [],
        "autoRuleGroups": [],
        "canSelectWhenInactive": True,
        "excludedTags": [],
        "guideGridHei": 0,
        "guideGridWid": 0,
        "hideFieldsWhenInactive": True,
        "hideInList": False,
        "renderInWorldView": True,
        "requiredTags": [],
        "tilePivotX": 0.0,
        "tilePivotY": 0.0,
        "tilesetDefUid": None,
        "uiFilterTags": [],
        "useAsyncRender": False,
        "biomeFieldUid": None,
        "autoSourceLayerDefUid": None,
        "autoTilesetDefUid": None,
        "doc": None,
        "uiColor": None,
    }
    ld.update(kwargs)
    return ld


def _make_enum_def(
    uid_alloc: UidAllocator,
    identifier: str,
    values: list[str],
    colors: list[str] | None = None,
) -> dict:
    """Create a minimal valid LDtk EnumDef."""
    if colors is None:
        colors = [0] * len(values)
    enum_values = []
    for i, val in enumerate(values):
        enum_values.append(
            {
                "id": val,
                "tileRect": None,
                "color": colors[i] if i < len(colors) else 0,
            }
        )
    return {
        "uid": uid_alloc.next(),
        "identifier": identifier,
        "tags": [],
        "values": enum_values,
        "iconTilesetUid": None,
        "externalRelPath": None,
        "externalFileChecksum": None,
    }


def build_entity_field_defs(uid_alloc: UidAllocator) -> list[dict]:
    """Create the standard field definitions shared by all vault entity types."""
    return [
        _make_field_def(uid_alloc, "display_name", "F_String", editorDisplayMode="NameAndValue", editorAlwaysShow=True),
        _make_field_def(uid_alloc, "vault_path", "F_String", editorDisplayMode="Hidden"),
        _make_field_def(uid_alloc, "era", "F_Enum(Era)", editorAlwaysShow=True),
        _make_field_def(uid_alloc, "articy_id", "F_String", editorDisplayMode="Hidden"),
    ]


def _make_levels_from_zones(uid_alloc: UidAllocator, manifest: dict) -> list[dict]:
    """Create LDtk levels from zone entities in the manifest."""
    levels = []
    # Space levels out horizontally in the LDtk world view
    x_offset = 0
    spacing = 32  # pixels between levels

    for entity in manifest.get("entities", []):
        if entity.get("type") != "zone":
            continue

        display_name = entity.get("display_name", "Zone")
        # Convert display name to a valid LDtk identifier (PascalCase, no spaces)
        identifier = display_name.replace(" ", "_").replace("'", "").replace("-", "_")

        # Read zone dimensions from frontmatter (passed through template_properties)
        # Default to 16x16 tiles if not specified
        # Note: grid-width/grid-height are in the vault frontmatter but not in template_properties
        # For now use a default; the designer adjusts in LDtk
        px_wid = GRID_SIZE * 20
        px_hei = GRID_SIZE * 16

        level = {
            "identifier": identifier,
            "iid": _make_iid(),
            "uid": uid_alloc.next(),
            "worldX": x_offset,
            "worldY": 0,
            "worldDepth": 0,
            "pxWid": px_wid,
            "pxHei": px_hei,
            "__bgColor": "#696A79",
            "bgColor": None,
            "useAutoIdentifier": False,
            "bgRelPath": None,
            "bgPos": None,
            "bgPivotX": 0.5,
            "bgPivotY": 0.5,
            "__smartColor": "#ADADB5",
            "__bgPos": None,
            "externalRelPath": None,
            "fieldInstances": [],
            "layerInstances": None,
            "__neighbours": [],
        }
        levels.append(level)
        x_offset += px_wid + spacing

    return levels


def _make_layer_instance(
    layer_def: dict,
    level: dict,
    intgrid_csv: list[int] | None = None,
) -> dict:
    """Create a layer instance for a level from its layer definition."""
    c_wid = level["pxWid"] // layer_def["gridSize"]
    c_hei = level["pxHei"] // layer_def["gridSize"]
    total_cells = c_wid * c_hei

    layer_type = layer_def["type"]

    if intgrid_csv is None and layer_type == "IntGrid":
        intgrid_csv = [0] * total_cells

    return {
        "__identifier": layer_def["identifier"],
        "__type": layer_type,
        "__gridSize": layer_def["gridSize"],
        "__cWid": c_wid,
        "__cHei": c_hei,
        "__opacity": 1.0,
        "__pxTotalOffsetX": 0,
        "__pxTotalOffsetY": 0,
        "__tilesetDefUid": layer_def.get("tilesetDefUid"),
        "__tilesetRelPath": None,
        "iid": _make_iid(),
        "layerDefUid": layer_def["uid"],
        "levelId": level["uid"],
        "visible": True,
        "intGridCsv": intgrid_csv if intgrid_csv else [],
        "autoLayerTiles": [],
        "entityInstances": [],
        "gridTiles": [],
        "pxOffsetX": 0,
        "pxOffsetY": 0,
        "overrideTilesetUid": None,
        "optionalRules": [],
        "seed": level["uid"] * 1000 + layer_def["uid"],
    }


def _populate_layer_instances(levels: list[dict], layer_defs: list[dict], level_layouts: dict) -> None:
    """Populate layerInstances on levels that have None."""
    # Layer order in instances matches layer_defs order (top-first)
    for level in levels:
        if level.get("layerInstances") is not None:
            continue
        # Skip stub levels that lack required dimensions
        if "pxWid" not in level or "pxHei" not in level:
            continue

        identifier = level["identifier"]
        layouts = level_layouts.get(identifier, {})

        instances = []
        for layer_def in layer_defs:
            layer_name = layer_def["identifier"]
            csv = layouts.get(layer_name)
            instances.append(_make_layer_instance(layer_def, level, csv))

        level["layerInstances"] = instances


# ── Hand-designed level layouts ──────────────────────────────────────────────
# Each layout is a dict of layer_name -> intGridCsv (flat, row-major, 20 cols x 16 rows = 320 cells)
# Only layers with non-default data need entries; missing layers get all-zeros.

# fmt: off
# Whispering Woods Edge: 20x16 field biome
# Collision: 0=empty(walkable), 1=solid, 2=water, 3=pit
_WWE_COLLISION = [
    1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,1,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,1,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,1,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
    1,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,1,
    1,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
    1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,
    1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,
    1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,
    1,1,1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1,1,
]

# Terrain: uses field IntGrid values
# 0=void, 1=ground, 10=tall_grass, 11=bush, 12=tree_trunk, 15=path_dirt, 3=water_shallow, 18=undergrowth
_WWE_TERRAIN = [
    12,12,12,12,1,1,10,10,10,1,1,10,10,10,1,1,12,12,12,12,
    12,1,10,10,10,1,1,10,10,10,1,1,10,1,1,10,10,10,1,12,
    11,1,1,10,10,10,1,1,10,10,10,1,1,10,10,10,1,1,10,11,
    12,10,1,1,15,15,15,15,15,15,15,15,15,15,1,1,10,1,3,12,
    11,10,10,1,15,1,1,1,1,1,1,1,1,15,10,10,1,1,3,12,
    1,1,10,10,15,1,1,1,1,1,1,1,1,15,10,10,10,1,3,11,
    1,1,10,10,15,1,1,1,1,1,1,1,1,15,10,10,10,1,3,11,
    1,1,10,10,15,15,15,15,15,15,15,15,15,15,10,10,10,1,1,12,
    12,1,1,10,10,18,18,1,1,1,1,18,18,10,10,10,1,1,10,12,
    12,10,1,1,18,18,12,12,18,18,18,18,12,12,18,18,1,1,10,11,
    11,10,10,1,18,18,12,12,18,18,18,18,12,12,18,18,1,1,10,12,
    12,10,10,1,1,18,18,18,18,1,1,18,18,18,18,1,1,10,10,12,
    12,12,1,1,10,10,18,18,1,1,1,1,18,18,10,10,1,1,12,12,
    12,12,12,1,1,10,10,10,10,1,1,10,10,10,10,1,1,12,12,12,
    12,12,12,12,1,1,10,10,10,1,1,10,10,10,1,1,12,12,12,12,
    12,12,12,12,12,12,12,12,1,1,1,1,12,12,12,12,12,12,12,12,
]
# fmt: on

LEVEL_LAYOUTS = {
    "Whispering_Woods_Edge": {
        "Collision": _WWE_COLLISION,
        "Terrain": _WWE_TERRAIN,
    },
}


def _make_default_level(uid_alloc: UidAllocator) -> dict:
    """Create a default empty level so LDtk has something to load."""
    return {
        "identifier": "Level_0",
        "iid": _make_iid(),
        "uid": uid_alloc.next(),
        "worldX": 0,
        "worldY": 0,
        "worldDepth": 0,
        "pxWid": 256,
        "pxHei": 256,
        "__bgColor": "#696A79",
        "bgColor": None,
        "useAutoIdentifier": True,
        "bgRelPath": None,
        "bgPos": None,
        "bgPivotX": 0.5,
        "bgPivotY": 0.5,
        "__smartColor": "#ADADB5",
        "__bgPos": None,
        "externalRelPath": None,
        "fieldInstances": [],
        "layerInstances": None,
        "__neighbours": [],
    }


def generate_ldtk_project(manifest: dict) -> dict:
    """Generate a complete LDtk project structure from an import manifest."""
    uid = UidAllocator(1)

    # Enum definitions
    entity_type_values = list(TYPE_TO_ENTITY.values())
    era_values = ["Father", "Son", "Both"]

    enums = [
        _make_enum_def(uid, "EntityType", entity_type_values),
        _make_enum_def(uid, "Era", era_values),
    ]

    # Entity definitions — one per vault entity type
    entity_defs = []
    for _manifest_type, ldtk_name in TYPE_TO_ENTITY.items():
        color = ENTITY_COLORS.get(ldtk_name, "#888888")
        fields = build_entity_field_defs(uid)
        entity_defs.append(_make_entity_def(uid, ldtk_name, color, fields))

    # Layer definitions (order matters — first in list = top in editor)
    layers = [
        _make_layer_def(uid, "Entities", "Entities"),
        _make_layer_def(uid, "Terrain_Son", "IntGrid", intGridValues=INTGRID_TERRAIN),
        _make_layer_def(uid, "Terrain_Father", "IntGrid", intGridValues=INTGRID_TERRAIN),
        _make_layer_def(uid, "Terrain", "IntGrid", intGridValues=INTGRID_TERRAIN),
        _make_layer_def(uid, "Collision", "IntGrid", intGridValues=INTGRID_COLLISION),
    ]

    # Create levels from zone entities in the manifest
    levels = _make_levels_from_zones(uid, manifest)

    project = {
        "__header__": {
            "fileType": "LDtk Project JSON",
            "app": "LDtk",
            "doc": "https://ldtk.io/json",
            "schema": "https://ldtk.io/files/JSON_SCHEMA.json",
            "appAuthor": "Sebastien 'deepnight' Benard",
            "appVersion": "1.5.3",
            "url": "https://ldtk.io",
        },
        "iid": _make_iid(),
        "jsonVersion": LDTK_JSON_VERSION,
        "appBuildId": 0,
        "nextUid": uid.next_uid,
        "identifierStyle": "Capitalize",
        "worldLayout": "Free",
        "worldGridWidth": None,
        "worldGridHeight": None,
        "defaultLevelWidth": 256,
        "defaultLevelHeight": 256,
        "defaultGridSize": GRID_SIZE,
        "defaultEntityWidth": GRID_SIZE,
        "defaultEntityHeight": GRID_SIZE,
        "defaultPivotX": 0.5,
        "defaultPivotY": 1.0,
        "defaultLevelBgColor": "#696A79",
        "bgColor": "#40465B",
        "externalLevels": False,
        "exportTiled": False,
        "exportLevelBg": True,
        "simplifiedExport": False,
        "minifyJson": False,
        "imageExportMode": "None",
        "pngFilePattern": None,
        "levelNamePattern": "Level_%idx",
        "backupOnSave": False,
        "backupLimit": 10,
        "backupRelPath": None,
        "tutorialDesc": None,
        "customCommands": [],
        "flags": [],
        "dummyWorldIid": _make_iid(),
        "toc": [],
        "worlds": [],
        "defs": {
            "layers": layers,
            "entities": entity_defs,
            "tilesets": [],
            "enums": enums,
            "externalEnums": [],
            "levelFields": [],
        },
        "levels": levels if levels else [_make_default_level(uid)],
    }

    # Populate layer instances on freshly created levels
    _populate_layer_instances(project["levels"], layers, LEVEL_LAYOUTS)

    return project


def merge_ldtk_project(existing: dict, new_defs: dict) -> dict:
    """Merge new definitions into an existing LDtk project, preserving levels."""
    existing["defs"]["enums"] = new_defs["defs"]["enums"]
    existing["defs"]["entities"] = new_defs["defs"]["entities"]
    existing["defs"]["layers"] = new_defs["defs"]["layers"]
    existing["nextUid"] = new_defs["nextUid"]

    # Populate layerInstances on levels that have None
    _populate_layer_instances(
        existing.get("levels", []),
        existing["defs"]["layers"],
        LEVEL_LAYOUTS,
    )

    return existing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync vault entities into LDtk project file")
    parser.add_argument("manifest", type=Path, help="Path to import-manifest.json")
    parser.add_argument("output", type=Path, help="Output path for .ldtk file")
    args = parser.parse_args(argv)

    if not args.manifest.exists():
        print(f"Error: manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    with open(args.manifest, encoding="utf-8") as f:
        manifest = json.load(f)

    new_project = generate_ldtk_project(manifest)

    if args.output.exists():
        with open(args.output, encoding="utf-8") as f:
            existing = json.load(f)
        result = merge_ldtk_project(existing, new_project)
        print(f"Updated existing LDtk project: {args.output}")
    else:
        result = new_project
        print(f"Created new LDtk project: {args.output}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    entity_count = len(result["defs"]["entities"])
    level_count = len(result.get("levels", []))
    print(f"  {entity_count} entity defs, {level_count} levels preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
