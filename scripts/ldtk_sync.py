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

# Allow sibling imports when the script is run from the repo root via Taskfile
# (python3 scripts/ldtk_sync.py ...). Safe to append even if already present.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

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

# IntGrid vocabularies for collision + terrain layers are shared with the
# zone layout renderer via scripts/ldtk_vocabulary. Re-exported here under
# the existing names so this module's public API is unchanged.
from ldtk_vocabulary import INTGRID_COLLISION, INTGRID_TERRAIN  # noqa: E402


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


def _zone_identifier(display_name: str) -> str:
    """Convert a zone display name into the LDtk identifier convention
    (Capitalize style): underscores between words, no apostrophes or dashes.
    """
    return display_name.replace(" ", "_").replace("'", "").replace("-", "_")


def _zone_dimensions_px(template_props: dict) -> tuple[int, int]:
    """Pull pixel dimensions from a zone entity's template_properties.
    Falls back to 20x16 tiles if grid_width/grid_height are missing.
    """
    grid_w = int(template_props.get("grid_width", 20))
    grid_h = int(template_props.get("grid_height", 16))
    return GRID_SIZE * grid_w, GRID_SIZE * grid_h


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
        identifier = _zone_identifier(display_name)

        # Zone dimensions come from the vault frontmatter's grid-width /
        # grid-height (normalized to grid_width / grid_height in the manifest
        # by vault_to_manifest._lift_mechanical_sections).
        template_props = entity.get("template_properties", {}) or {}
        px_wid, px_hei = _zone_dimensions_px(template_props)

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


def _populate_layer_instances(
    levels: list[dict],
    layer_defs: list[dict],
    level_layouts: dict,
    force: bool = False,
) -> None:
    """Populate layerInstances on levels.

    By default, only levels whose layerInstances is None are populated
    (preserving already-authored data). Pass force=True to overwrite
    all levels — used when rendering from vault layout specs, where the
    spec is the source of truth and the .ldtk is a derived artifact.

    Layer order in instances matches layer_defs order (top-first).
    """
    for level in levels:
        if not force and level.get("layerInstances") is not None:
            continue
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


def _vault_slug_from_path(vault_path: str) -> str:
    """Extract the slug from a manifest vault_path.

    'vault/world/characters/torbin.md' -> 'torbin'
    Works cross-platform (handles both / and \\ separators).
    """
    name = vault_path.replace("\\", "/").split("/")[-1]
    return name[:-3] if name.endswith(".md") else name


def _build_slug_lookup(manifest: dict) -> dict[str, dict]:
    """Index manifest entities by slug for entity-instance vault_ref resolution."""
    out: dict[str, dict] = {}
    for e in manifest.get("entities", []):
        slug = _vault_slug_from_path(e.get("vault_path", ""))
        if slug:
            out[slug] = e
    return out


def _apply_entity_instances(
    levels: list[dict],
    layer_defs: list[dict],
    rendered_layouts: dict,
    manifest: dict,
) -> None:
    """Write agent-authored entity placements into each level's Entities layer.

    `rendered_layouts[level_id]["__entities__"]` is a list of entity specs
    produced by zone_layout_render:

        [{ "type": "Character", "vault_ref": "torbin", "at": [3, 4], "era": "Both" }, ...]

    This function resolves vault_ref → manifest entity, then builds the
    LDtk `entityInstances` array with fieldInstances populated from the
    manifest's articy_id / display_name / vault_path plus the spec's era.
    """
    # Find the Entities layer def and its field defs (display_name,
    # vault_path, era, articy_id). Field defs are per-entity-def, so we
    # build a lookup table keyed by entity-def identifier.
    entities_layer_def = next((ld for ld in layer_defs if ld.get("type") == "Entities"), None)
    if entities_layer_def is None:
        return  # nothing to write into

    slug_lookup = _build_slug_lookup(manifest)

    # Entity-def field UID lookup by entity identifier (Character, Creature, ...).
    # We need the LDtk field-def UIDs because entityInstances.fieldInstances
    # reference them, not the field names directly.
    entity_defs = manifest.get("_entity_defs_cache")  # set by caller if available
    # Otherwise walk the entity defs ourselves from the project layers/defs;
    # this gets called with a project dict whose defs.entities is accessible.
    # For now, fish them out of the layer_defs' sibling structure by convention
    # — the caller (generate/merge) passes the full layer_defs list which is
    # already aligned with the project's defs.entities. To keep the API clean,
    # entity-def UIDs are obtained via a pass over all levels' pre-existing
    # entityInstances, falling back to None (which writes unresolved refs).
    #
    # A cleaner future refactor: pass the entity_defs list explicitly.

    for level in levels:
        level_id = level.get("identifier", "")
        layout = rendered_layouts.get(level_id)
        if not layout:
            continue
        entity_specs = layout.get("__entities__", []) or []
        if not entity_specs:
            continue

        # Find the Entities layerInstance for this level.
        ent_instance = next(
            (li for li in (level.get("layerInstances") or []) if li.get("__type") == "Entities"),
            None,
        )
        if ent_instance is None:
            continue

        # Replace per the authoring policy: vault spec is source of truth.
        ent_instance["entityInstances"] = []
        grid_size = GRID_SIZE

        for spec in entity_specs:
            etype = spec["type"]
            vault_ref = spec["vault_ref"]
            col, row = spec["at"]
            era = spec.get("era", "Both")

            vault_entity = slug_lookup.get(vault_ref)
            if vault_entity is None:
                # Unknown slug — fail loudly so typos don't silently
                # produce invisible entity instances.
                raise SystemExit(
                    f"ERROR: zone {level_id!r} entity spec references unknown "
                    f"vault slug {vault_ref!r}; ensure the .md page exists and "
                    f"`task articy:prep` has been run."
                )

            display_name = vault_entity.get("display_name", vault_ref)
            vault_path = vault_entity.get("vault_path", "")
            articy_id = vault_entity.get("articy_id", "") or ""

            ent_instance["entityInstances"].append(
                _make_entity_instance(
                    entity_type=etype,
                    col=col,
                    row=row,
                    grid_size=grid_size,
                    level_uid=level["uid"],
                    display_name=display_name,
                    vault_path=vault_path,
                    era=era,
                    articy_id=articy_id,
                )
            )


def _make_entity_instance(
    entity_type: str,
    col: int,
    row: int,
    grid_size: int,
    level_uid: int,
    display_name: str,
    vault_path: str,
    era: str,
    articy_id: str,
) -> dict:
    """Build a minimal valid LDtk entityInstance dict.

    The defUid is set to -1 as a placeholder — LDtk will resolve it when
    the file is opened in the editor because __identifier matches an
    existing entity def. Field values are written as __value (engine-facing)
    with the name in __identifier; LDtk re-derives defUid references on load.
    """
    px_x = col * grid_size + grid_size // 2
    px_y = row * grid_size + grid_size  # bottom pivot (matches defaultPivotY=1.0)
    return {
        "__identifier": entity_type,
        "__grid": [col, row],
        "__pivot": [0.5, 1.0],
        "__tags": ["vault_entity"],
        "__tile": None,
        "__smartColor": "#A0A0A0",
        "__worldX": px_x,
        "__worldY": px_y,
        "iid": _make_iid(),
        "width": grid_size,
        "height": grid_size,
        "defUid": -1,
        "px": [px_x, px_y],
        "fieldInstances": [
            _make_field_instance("display_name", "String", display_name),
            _make_field_instance("vault_path", "String", vault_path),
            _make_field_instance("era", "LocalEnum.Era", era),
            _make_field_instance("articy_id", "String", articy_id),
        ],
    }


def _make_field_instance(name: str, type_name: str, value) -> dict:
    return {
        "__identifier": name,
        "__type": type_name,
        "__value": value,
        "__tile": None,
        "defUid": -1,
        "realEditorValues": [{"id": "V_String" if type_name == "String" else "V_String", "params": [value]}],
    }


def _render_zone_layouts(manifest: dict) -> dict[str, dict[str, list[int]]]:
    """Walk zone entities in the manifest; render their layout specs into
    per-level CSV arrays keyed by LDtk level identifier.

    Zones without a `template_properties.layout` contribute nothing to
    the output (their level stays at empty-grid defaults). Zones with a
    layout spec render through scripts.zone_layout_render.render() using
    the grid dimensions + biome from their frontmatter.
    """
    from zone_layout_render import LayoutSpecError, render as _render

    out: dict[str, dict[str, list[int]]] = {}
    for entity in manifest.get("entities", []):
        if entity.get("type") != "zone":
            continue
        tp = entity.get("template_properties", {}) or {}
        spec = tp.get("layout")
        if spec is None:
            continue

        grid_w = int(tp.get("grid_width", 20))
        grid_h = int(tp.get("grid_height", 16))
        biome = str(tp.get("biome", "field"))
        identifier = _zone_identifier(entity.get("display_name", "Zone"))

        try:
            rendered = _render(spec, grid_w, grid_h, biome, zone_id=identifier)
        except LayoutSpecError as exc:
            # Surface the error with zone identifier so the designer
            # can find the bad page instantly.
            raise SystemExit(f"ERROR: {exc}") from exc

        # ldtk_sync's LEVEL_LAYOUTS dict is "identifier -> {layer_name: csv, ...}".
        # entities (the Entities layer) is built separately — it's a list of
        # entity-instance dicts, not a CSV. Stashing it under a reserved key
        # so _populate_layer_instances can pick it up in a follow-up pass.
        out[identifier] = {
            "Collision": rendered["Collision"],
            "Terrain": rendered["Terrain"],
            "Terrain_Father": rendered["Terrain_Father"],
            "Terrain_Son": rendered["Terrain_Son"],
            "__entities__": rendered["entities"],
        }
    return out


# Legacy hardcoded layouts have moved. Zone tile data now lives in each
# zone's vault page under a '## Layout Spec' fenced YAML block, lifted
# through vault_to_manifest → template_properties.layout → zone_layout_render.
# See vault/world/_meta/zone-schema.md for the spec grammar.
#
# This empty LEVEL_LAYOUTS is retained only as the fallback target for
# merge_ldtk_project(manifest=None) calls, which older callers use when
# they don't have a manifest in scope. New code paths should always pass
# the manifest so the vault spec drives the render.
LEVEL_LAYOUTS: dict = {}


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

    # Render zone layout specs (if any). Always force=True per authoring
    # policy: vault zone pages are the source of truth for tile data,
    # the LDtk editor is a preview.
    rendered_layouts = _render_zone_layouts(manifest)
    _populate_layer_instances(project["levels"], layers, rendered_layouts, force=True)
    _apply_entity_instances(project["levels"], layers, rendered_layouts, manifest)

    return project


def merge_ldtk_project(existing: dict, new_defs: dict, manifest: dict | None = None) -> dict:
    """Merge new definitions into an existing LDtk project.

    Behavior depending on whether a `manifest` is provided:

    * manifest=None (legacy): preserves existing level layerInstances;
      only populates None layerInstances from LEVEL_LAYOUTS. This matches
      the original behavior for tools that don't have a manifest in hand.
    * manifest=<dict>: renders zone layout specs from the manifest and
      OVERWRITES every level's layerInstances. Per authoring policy, the
      vault spec is the source of truth and the .ldtk is derived.

    In both cases, zones that appeared in new_defs but weren't in
    existing are appended as new levels with offset worldX so they don't
    overlap existing levels in the LDtk world view.
    """
    existing["defs"]["enums"] = new_defs["defs"]["enums"]
    existing["defs"]["entities"] = new_defs["defs"]["entities"]
    existing["defs"]["layers"] = new_defs["defs"]["layers"]
    existing["nextUid"] = new_defs["nextUid"]

    # Append levels from new_defs that aren't in existing yet (new zones).
    existing_ids = {L["identifier"] for L in existing.get("levels", [])}
    new_levels = [L for L in new_defs.get("levels", []) if L["identifier"] not in existing_ids]
    if new_levels:
        max_world_x = max((L.get("worldX", 0) + L.get("pxWid", 0) for L in existing.get("levels", [])), default=0)
        spacing = 32
        cursor = max_world_x + spacing if max_world_x else 0
        for L in new_levels:
            L["worldX"] = cursor
            cursor += L.get("pxWid", 0) + spacing
        existing.setdefault("levels", []).extend(new_levels)

    if manifest is not None:
        rendered_layouts = _render_zone_layouts(manifest)
        _populate_layer_instances(
            existing["levels"],
            existing["defs"]["layers"],
            rendered_layouts,
            force=True,
        )
        _apply_entity_instances(existing["levels"], existing["defs"]["layers"], rendered_layouts, manifest)
    else:
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
        result = merge_ldtk_project(existing, new_project, manifest=manifest)
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
