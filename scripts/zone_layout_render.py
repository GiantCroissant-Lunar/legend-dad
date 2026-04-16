"""Render a zone layout spec into LDtk IntGrid arrays + entity instances.

The layout spec is authored in each zone's vault markdown page under a
`## Layout Spec` fenced YAML block, lifted into the manifest as
`template_properties.layout` by vault_to_manifest, and consumed here.

Primitives:

- **base**: default fill for the whole grid (Collision + Terrain).
- **raw**: optional escape hatch — paste a pre-computed flat CSV per
  layer. Runs after `base`, before `regions`. Useful for porting
  hand-authored grids or output from external tools. Most specs should
  stay at the primitives level (base/regions/paths) for reviewability.
- **regions**: named rectangles / circles that overwrite cells.
- **paths**: polyline strokes that stamp a terrain tile between
  waypoints (collision inherits from base unless explicitly set).
- **era_overlays**: era-specific diffs layered onto Terrain_Father and
  Terrain_Son on top of the base-plus-regions-plus-paths Terrain.
- **entities**: Entity-layer instances (Character, Creature, etc).

The renderer is pure: given the same spec + grid_width + grid_height +
biome, it returns the same output. No I/O. All validation raises
LayoutSpecError with a human-readable message.

The output format is intentionally the same shape as
`ldtk_sync._make_layer_instance` consumes so the integration is a
one-liner: hand the dict to _make_layer_instance per layer name.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Shared with scripts/ldtk_sync.py — same sys.path trick because scripts
# are invoked from repo root by Taskfile.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from ldtk_vocabulary import collision_value, terrain_value  # noqa: E402


class LayoutSpecError(ValueError):
    """Raised when a layout spec is malformed, references unknown symbols,
    places operations out of bounds, or otherwise can't be rendered."""


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────


def render(
    spec: dict | None,
    grid_width: int,
    grid_height: int,
    biome: str,
    zone_id: str = "<unknown>",
) -> dict[str, Any]:
    """Render a layout spec into CSV arrays + entity instances.

    Args:
        spec: the parsed YAML dict from the zone page's Layout Spec section,
            or None if the zone has no spec (in which case all layers are
            filled with zeros and no entities are emitted).
        grid_width: zone width in tiles.
        grid_height: zone height in tiles.
        biome: zone biome ('field', 'dungeon', 'town'); used for
            biome-scoped terrain symbol validation.
        zone_id: the zone identifier (used only for error messages).

    Returns:
        {
            "Collision": [int, ...]       # flat row-major, len = w*h
            "Terrain": [int, ...]
            "Terrain_Father": [int, ...]
            "Terrain_Son": [int, ...]
            "entities": [ { "type": str, "vault_ref": str, "at": [c, r], "era": str }, ... ]
        }

    Raises:
        LayoutSpecError: on any validation failure.
    """
    total = grid_width * grid_height

    if spec is None:
        return _empty_output(total)

    if not isinstance(spec, dict):
        raise LayoutSpecError(f"zone {zone_id!r}: layout spec must be a dict, got {type(spec).__name__}")

    try:
        ctx = _RenderContext(grid_width, grid_height, biome, zone_id)
        base = spec.get("base", {}) or {}
        ctx.apply_base(base)

        raw = spec.get("raw")
        if raw is not None:
            ctx.apply_raw(raw)

        for i, region in enumerate(spec.get("regions", []) or []):
            ctx.apply_region(region, index=i)

        for i, path in enumerate(spec.get("paths", []) or []):
            ctx.apply_path(path, index=i)

        # Father / Son start as a copy of the base terrain, then era_overlays
        # stamp their differences on top. If the raw block supplied its own
        # Terrain_Father / Terrain_Son, use those as the starting grids.
        terrain_father = ctx.raw_terrain_father if ctx.raw_terrain_father is not None else list(ctx.terrain)
        terrain_son = ctx.raw_terrain_son if ctx.raw_terrain_son is not None else list(ctx.terrain)

        overlays = spec.get("era_overlays", {}) or {}
        if not isinstance(overlays, dict):
            raise LayoutSpecError(
                f"zone {zone_id!r}: era_overlays must be a dict with optional "
                f"'father' and 'son' keys"
            )
        father_ops = overlays.get("father", []) or []
        son_ops = overlays.get("son", []) or []
        ctx.apply_era_overlay(terrain_father, father_ops, era="father")
        ctx.apply_era_overlay(terrain_son, son_ops, era="son")

        entities = ctx.build_entities(spec.get("entities", []) or [])

        return {
            "Collision": list(ctx.collision),
            "Terrain": list(ctx.terrain),
            "Terrain_Father": terrain_father,
            "Terrain_Son": terrain_son,
            "entities": entities,
        }
    except LayoutSpecError as exc:
        # Propagate zone context into the message if an inner layer hasn't
        # already prefixed it. Keeps call sites like _resolve_terrain free
        # of zone_id plumbing.
        msg = str(exc)
        if f"zone {zone_id!r}" in msg:
            raise
        raise LayoutSpecError(f"zone {zone_id!r}: {msg}") from exc
    except KeyError as exc:
        raise LayoutSpecError(f"zone {zone_id!r}: {exc}") from exc


def _empty_output(total: int) -> dict[str, Any]:
    return {
        "Collision": [0] * total,
        "Terrain": [0] * total,
        "Terrain_Father": [0] * total,
        "Terrain_Son": [0] * total,
        "entities": [],
    }


# ──────────────────────────────────────────────────────────────────────
# Rendering internals
# ──────────────────────────────────────────────────────────────────────


class _RenderContext:
    """Mutable grid state used during a single render pass.

    All cell mutations go through set_cell() which bounds-checks against
    the declared grid dimensions. This catches spec errors early with a
    message that names the offending operation.
    """

    def __init__(self, grid_width: int, grid_height: int, biome: str, zone_id: str):
        self.w = grid_width
        self.h = grid_height
        self.biome = biome
        self.zone_id = zone_id
        total = grid_width * grid_height
        self.collision: list[int] = [0] * total
        self.terrain: list[int] = [0] * total
        # If the spec's raw block supplies Terrain_Father / Terrain_Son,
        # they're stored here and picked up by the render() driver as the
        # starting grids for era overlays. None means "start from Terrain".
        self.raw_terrain_father: list[int] | None = None
        self.raw_terrain_son: list[int] | None = None

    # --- cell-level helpers ---

    def _idx(self, col: int, row: int) -> int:
        return row * self.w + col

    def _in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.w and 0 <= row < self.h

    def _set_cell(
        self,
        grid: list[int],
        col: int,
        row: int,
        value: int,
        context: str,
    ) -> None:
        if not self._in_bounds(col, row):
            raise LayoutSpecError(
                f"zone {self.zone_id!r}: {context} touches out-of-bounds cell "
                f"({col}, {row}); grid is {self.w}x{self.h}"
            )
        grid[self._idx(col, row)] = value

    # --- raw (escape hatch) ---

    def apply_raw(self, raw: dict) -> None:
        """Overwrite layer CSV arrays from a raw dict.

        `raw` is any subset of {"Collision", "Terrain", "Terrain_Father",
        "Terrain_Son"}; missing layers fall through to the primitive
        pipeline. Arrays must have length == grid_width * grid_height.
        Values are assumed pre-validated (integers within the
        collision/terrain vocabularies); the renderer does a length check
        but doesn't re-resolve symbols.
        """
        total = self.w * self.h
        if not isinstance(raw, dict):
            raise LayoutSpecError(
                f"zone {self.zone_id!r}: raw must be a dict of layer-name to flat int array"
            )
        for layer_name in ("Collision", "Terrain", "Terrain_Father", "Terrain_Son"):
            if layer_name not in raw:
                continue
            arr = raw[layer_name]
            if not isinstance(arr, list) or len(arr) != total:
                raise LayoutSpecError(
                    f"zone {self.zone_id!r}: raw.{layer_name} must be a list of "
                    f"{total} ints (got {type(arr).__name__} "
                    f"len={len(arr) if isinstance(arr, list) else 'n/a'})"
                )
            if any(not isinstance(v, int) for v in arr):
                raise LayoutSpecError(
                    f"zone {self.zone_id!r}: raw.{layer_name} must contain only int values"
                )
            if layer_name == "Collision":
                self.collision = list(arr)
            elif layer_name == "Terrain":
                self.terrain = list(arr)
            elif layer_name == "Terrain_Father":
                self.raw_terrain_father = list(arr)
            elif layer_name == "Terrain_Son":
                self.raw_terrain_son = list(arr)

    # --- base ---

    def apply_base(self, base: dict) -> None:
        col_name = base.get("collision", "empty")
        ter_name = base.get("terrain", "ground")
        c = _resolve_collision(col_name)
        t = _resolve_terrain(ter_name, self.biome)
        for i in range(len(self.collision)):
            self.collision[i] = c
            self.terrain[i] = t

    # --- region (rect / circle) ---

    def apply_region(self, region: dict, index: int) -> None:
        rid = region.get("id", f"region[{index}]")
        shape = region.get("shape")
        if shape not in ("rect", "circle"):
            raise LayoutSpecError(
                f"zone {self.zone_id!r}: region {rid!r} has invalid shape "
                f"{shape!r}; expected 'rect' or 'circle'"
            )

        col_name = region.get("collision")
        ter_name = region.get("terrain")
        c = _resolve_collision(col_name) if col_name is not None else None
        t = _resolve_terrain(ter_name, self.biome) if ter_name is not None else None

        cells = (
            _rect_cells(region, rid, self.zone_id)
            if shape == "rect"
            else _circle_cells(region, rid, self.zone_id)
        )

        ctx_label = f"region {rid!r}"
        for col, row in cells:
            if c is not None:
                self._set_cell(self.collision, col, row, c, ctx_label)
            if t is not None:
                self._set_cell(self.terrain, col, row, t, ctx_label)

        # Openings let you punch doorways into wall regions without having
        # to draw them as two separate regions.
        for opening in region.get("openings", []) or []:
            at = opening.get("at")
            if not isinstance(at, list) or len(at) != 2:
                raise LayoutSpecError(
                    f"zone {self.zone_id!r}: region {rid!r} opening must have 'at: [col, row]'"
                )
            oc, orow = int(at[0]), int(at[1])
            o_col_name = opening.get("collision")
            o_ter_name = opening.get("terrain")
            if o_col_name is not None:
                self._set_cell(
                    self.collision,
                    oc,
                    orow,
                    _resolve_collision(o_col_name),
                    f"region {rid!r} opening",
                )
            if o_ter_name is not None:
                self._set_cell(
                    self.terrain,
                    oc,
                    orow,
                    _resolve_terrain(o_ter_name, self.biome),
                    f"region {rid!r} opening",
                )

    # --- path (polyline) ---

    def apply_path(self, path: dict, index: int) -> None:
        pid = path.get("id", f"path[{index}]")
        points = path.get("points")
        if not isinstance(points, list) or len(points) < 2:
            raise LayoutSpecError(
                f"zone {self.zone_id!r}: path {pid!r} must have 'points' "
                f"with at least two [col, row] pairs"
            )

        col_name = path.get("collision")
        ter_name = path.get("terrain")
        c = _resolve_collision(col_name) if col_name is not None else None
        t = _resolve_terrain(ter_name, self.biome) if ter_name is not None else None
        if c is None and t is None:
            raise LayoutSpecError(
                f"zone {self.zone_id!r}: path {pid!r} must set 'collision', "
                f"'terrain', or both"
            )

        ctx_label = f"path {pid!r}"
        all_cells: list[tuple[int, int]] = []
        for a, b in zip(points, points[1:]):
            all_cells.extend(_line_cells(a, b, pid, self.zone_id))
        # De-duplicate cells where segments meet so we don't re-stamp.
        seen: set[tuple[int, int]] = set()
        for col, row in all_cells:
            if (col, row) in seen:
                continue
            seen.add((col, row))
            if c is not None:
                self._set_cell(self.collision, col, row, c, ctx_label)
            if t is not None:
                self._set_cell(self.terrain, col, row, t, ctx_label)

    # --- era overlay ---

    def apply_era_overlay(self, grid: list[int], ops: list[dict], era: str) -> None:
        for i, op in enumerate(ops):
            label = f"era_overlays.{era}[{i}]"
            # Shape-based overlays (rect/circle) — same vocab as regions.
            shape = op.get("shape")
            ter_name = op.get("terrain")
            if ter_name is None:
                raise LayoutSpecError(
                    f"zone {self.zone_id!r}: {label} must set 'terrain'"
                )
            t = _resolve_terrain(ter_name, self.biome)

            if shape is None:
                at = op.get("at")
                if not isinstance(at, list) or len(at) != 2:
                    raise LayoutSpecError(
                        f"zone {self.zone_id!r}: {label} must have 'at: [col, row]' "
                        f"when shape is omitted"
                    )
                self._set_cell(grid, int(at[0]), int(at[1]), t, label)
            elif shape == "rect":
                for col, row in _rect_cells(op, label, self.zone_id):
                    self._set_cell(grid, col, row, t, label)
            elif shape == "circle":
                for col, row in _circle_cells(op, label, self.zone_id):
                    self._set_cell(grid, col, row, t, label)
            else:
                raise LayoutSpecError(
                    f"zone {self.zone_id!r}: {label} has invalid shape {shape!r}"
                )

    # --- entities ---

    def build_entities(self, entity_specs: list[dict]) -> list[dict]:
        out = []
        for i, e in enumerate(entity_specs):
            etype = e.get("type")
            if not etype:
                raise LayoutSpecError(
                    f"zone {self.zone_id!r}: entities[{i}] must set 'type' "
                    f"(e.g. 'Character', 'Creature')"
                )
            vault_ref = e.get("vault_ref")
            if not vault_ref:
                raise LayoutSpecError(
                    f"zone {self.zone_id!r}: entities[{i}] must set 'vault_ref'"
                )
            at = e.get("at")
            if not isinstance(at, list) or len(at) != 2:
                raise LayoutSpecError(
                    f"zone {self.zone_id!r}: entities[{i}] must set 'at: [col, row]'"
                )
            col, row = int(at[0]), int(at[1])
            if not self._in_bounds(col, row):
                raise LayoutSpecError(
                    f"zone {self.zone_id!r}: entities[{i}] placed at ({col}, {row}) "
                    f"which is outside grid {self.w}x{self.h}"
                )
            era = e.get("era", "Both")
            if era not in ("Father", "Son", "Both"):
                raise LayoutSpecError(
                    f"zone {self.zone_id!r}: entities[{i}] era must be "
                    f"'Father', 'Son', or 'Both', got {era!r}"
                )
            out.append(
                {
                    "type": etype,
                    "vault_ref": vault_ref,
                    "at": [col, row],
                    "era": era,
                }
            )
        return out


# ──────────────────────────────────────────────────────────────────────
# Shape cell generators — pure functions so they're trivially testable.
# ──────────────────────────────────────────────────────────────────────


def _rect_cells(spec: dict, label: str, zone_id: str) -> list[tuple[int, int]]:
    at = spec.get("at")
    size = spec.get("size")
    if not (isinstance(at, list) and len(at) == 2):
        raise LayoutSpecError(
            f"zone {zone_id!r}: {label} rect requires 'at: [col, row]'"
        )
    if not (isinstance(size, list) and len(size) == 2):
        raise LayoutSpecError(
            f"zone {zone_id!r}: {label} rect requires 'size: [width, height]'"
        )
    col0, row0 = int(at[0]), int(at[1])
    w, h = int(size[0]), int(size[1])
    if w <= 0 or h <= 0:
        raise LayoutSpecError(
            f"zone {zone_id!r}: {label} rect size must be positive, got [{w}, {h}]"
        )
    cells = []
    for dr in range(h):
        for dc in range(w):
            cells.append((col0 + dc, row0 + dr))
    return cells


def _circle_cells(spec: dict, label: str, zone_id: str) -> list[tuple[int, int]]:
    """Cells inside a discrete circle of given center + radius.

    Uses squared-distance (<=) to produce a filled disc. Radius 0 is
    accepted and yields a single center cell — useful for placing a 1-cell
    feature (a well, a brazier) with symmetric semantics.
    """
    center = spec.get("center")
    radius = spec.get("radius", 1)
    if not (isinstance(center, list) and len(center) == 2):
        raise LayoutSpecError(
            f"zone {zone_id!r}: {label} circle requires 'center: [col, row]'"
        )
    r = int(radius)
    if r < 0:
        raise LayoutSpecError(
            f"zone {zone_id!r}: {label} circle radius must be >= 0, got {r}"
        )
    col0, row0 = int(center[0]), int(center[1])
    cells = []
    r2 = r * r
    for dr in range(-r, r + 1):
        for dc in range(-r, r + 1):
            if dc * dc + dr * dr <= r2:
                cells.append((col0 + dc, row0 + dr))
    return cells


def _line_cells(a: list, b: list, label: str, zone_id: str) -> list[tuple[int, int]]:
    """Bresenham line between two [col, row] waypoints, inclusive endpoints."""
    if not (isinstance(a, list) and len(a) == 2):
        raise LayoutSpecError(f"zone {zone_id!r}: path {label!r} point must be [col, row]")
    if not (isinstance(b, list) and len(b) == 2):
        raise LayoutSpecError(f"zone {zone_id!r}: path {label!r} point must be [col, row]")
    x0, y0 = int(a[0]), int(a[1])
    x1, y1 = int(b[0]), int(b[1])

    cells: list[tuple[int, int]] = []
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        cells.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return cells


# ──────────────────────────────────────────────────────────────────────
# Symbol resolution — thin wrappers so we can translate library KeyErrors
# into LayoutSpecErrors with richer context.
# ──────────────────────────────────────────────────────────────────────


def _resolve_collision(name: str) -> int:
    try:
        return collision_value(name)
    except KeyError as exc:
        raise LayoutSpecError(str(exc)) from exc


def _resolve_terrain(name: str, biome: str) -> int:
    try:
        return terrain_value(name, biome)
    except KeyError as exc:
        raise LayoutSpecError(str(exc)) from exc
