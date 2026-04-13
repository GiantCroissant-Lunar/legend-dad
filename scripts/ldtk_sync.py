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
    "faction": "Faction",
    "quest": "Quest",
    "item": "Item",
    "event": "Event",
    "lore": "Lore",
    "bestiary": "Creature",
}

# IntGrid values for collision layer
INTGRID_COLLISION = [
    {"value": 0, "identifier": "empty", "color": "#000000", "tile": None, "groupUid": 0},
    {"value": 1, "identifier": "solid", "color": "#FFFFFF", "tile": None, "groupUid": 0},
    {"value": 2, "identifier": "water", "color": "#4488CC", "tile": None, "groupUid": 0},
    {"value": 3, "identifier": "pit", "color": "#332222", "tile": None, "groupUid": 0},
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
    uid_alloc: UidAllocator, identifier: str, values: list[str], colors: list[str] | None = None,
) -> dict:
    """Create a minimal valid LDtk EnumDef."""
    if colors is None:
        colors = [0] * len(values)
    enum_values = []
    for i, val in enumerate(values):
        enum_values.append({
            "id": val,
            "tileRect": None,
            "color": colors[i] if i < len(colors) else 0,
        })
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
        _make_layer_def(uid, "Collision", "IntGrid", intGridValues=INTGRID_COLLISION),
        _make_layer_def(uid, "Terrain", "IntGrid"),
    ]

    return {
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
        "worldGridWidth": 256,
        "worldGridHeight": 256,
        "defaultLevelWidth": 256,
        "defaultLevelHeight": 256,
        "defaultGridSize": GRID_SIZE,
        "defaultEntityWidth": GRID_SIZE,
        "defaultEntityHeight": GRID_SIZE,
        "defaultPivotX": 0.0,
        "defaultPivotY": 0.0,
        "defaultLevelBgColor": "#696A79",
        "bgColor": "#40465B",
        "externalLevels": False,
        "exportTiled": False,
        "exportLevelBg": True,
        "simplifiedExport": False,
        "minifyJson": False,
        "imageExportMode": "None",
        "levelNamePattern": "Level_%idx",
        "backupOnSave": False,
        "backupLimit": 10,
        "backupRelPath": None,
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
        "levels": [],
    }


def merge_ldtk_project(existing: dict, new_defs: dict) -> dict:
    """Merge new definitions into an existing LDtk project, preserving levels."""
    existing["defs"]["enums"] = new_defs["defs"]["enums"]
    existing["defs"]["entities"] = new_defs["defs"]["entities"]
    existing["defs"]["layers"] = new_defs["defs"]["layers"]
    existing["nextUid"] = new_defs["nextUid"]
    # levels, worlds, toc are preserved from existing
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
