# Dual-Timeline Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a playable prototype that proves the dual-timeline split-view mechanic — two tile-based game views floating over a world map, with active era toggling, world map peek, and one cause-and-effect interaction between timelines.

**Architecture:** The prototype uses GECS (ECS addon) for all game logic. A single World node contains entities for both timelines, distinguished by a `C_TimelineEra` component. Two SubViewportContainer nodes render the father and son views as floating windows over a CanvasLayer world map. `main.gd` handles era toggling and window layout; `S_Interaction` handles cross-timeline cause-and-effect propagation. TileMapLayer nodes define the tile-based maps. Entities are added to the ECS world with `add_to_tree=false` and manually placed into their era's SubViewport.

**Tech Stack:** Godot 4.6 (GDScript), GECS v7.1.0 (ECS), Web export (WASM), TileMapLayer for tile rendering

**Design Reference:** `vault/design/dual-timeline-gameplay-brainstorm.md`

---

## File Structure

```
project/hosts/complete-app/
├── scenes/
│   └── main.tscn                          # Root scene (replaces current test scene)
├── scripts/
│   ├── main.gd                            # Root scene controller, builds views + map
│   └── tileset_factory.gd                 # Programmatic colored-tile tileset
├── ecs/
│   ├── components/
│   │   ├── c_timeline_era.gd              # Which era an entity belongs to
│   │   ├── c_grid_position.gd             # Tile grid position (col, row)
│   │   ├── c_player_controlled.gd         # Marks entity as player-controlled
│   │   ├── c_interactable.gd              # Can be interacted with (e.g. boulder)
│   │   └── c_timeline_linked.gd           # Links an object to its other-era counterpart
│   ├── entities/
│   │   ├── e_player.gd                    # Player entity (father or son)
│   │   └── e_interactable.gd              # Interactable object (boulder, switch)
│   └── systems/
│       ├── s_player_input.gd              # Reads input, updates grid position
│       ├── s_grid_movement.gd             # Animates Node2D position from grid position
│       └── s_interaction.gd               # Handle player interacting with objects
```

**Responsibility summary:**

| File | Purpose |
|------|---------|
| `main.gd` | Owns the World node, drives ECS.process(), builds views, manages layout and map toggle |
| `tileset_factory.gd` | Creates prototype TileSet with colored tiles and walkability data |
| `c_timeline_era.gd` | Tags entities as `:father` or `:son` era |
| `c_grid_position.gd` | Tile-based position (col, row) + collision flag |
| `c_player_controlled.gd` | Marker component for player entities |
| `c_interactable.gd` | Marks objects as interactable with type and state |
| `c_timeline_linked.gd` | Links paired objects across eras (boulder↔blocked path) |
| `e_player.gd` | Entity with position + player control + era tag |
| `e_interactable.gd` | Entity with position + interactable + era tag + link |
| `s_player_input.gd` | Reads WASD/arrows only for the active era's player, updates grid position |
| `s_grid_movement.gd` | Lerps Node2D position to match grid position (smooth tile movement) |
| `s_timeline_manager.gd` | Handles Tab key for era toggle, propagates cause-and-effect via linked components |
| `s_interaction.gd` | Detects when player faces an interactable, handles action key |

---

## Task 1: ECS Components

**Files:**
- Create: `project/hosts/complete-app/ecs/components/c_timeline_era.gd`
- Create: `project/hosts/complete-app/ecs/components/c_grid_position.gd`
- Create: `project/hosts/complete-app/ecs/components/c_player_controlled.gd`
- Create: `project/hosts/complete-app/ecs/components/c_interactable.gd`
- Create: `project/hosts/complete-app/ecs/components/c_timeline_linked.gd`

- [ ] **Step 1: Create c_timeline_era.gd**

```gdscript
# ecs/components/c_timeline_era.gd
class_name C_TimelineEra
extends Component

enum Era { FATHER, SON }

@export var era: Era = Era.FATHER

func _init(p_era: Era = Era.FATHER):
	era = p_era
```

- [ ] **Step 2: Create c_grid_position.gd**

```gdscript
# ecs/components/c_grid_position.gd
class_name C_GridPosition
extends Component

@export var col: int = 0
@export var row: int = 0
@export var facing: Vector2i = Vector2i.DOWN

func _init(p_col: int = 0, p_row: int = 0):
	col = p_col
	row = p_row
```

- [ ] **Step 3: Create c_player_controlled.gd**

```gdscript
# ecs/components/c_player_controlled.gd
class_name C_PlayerControlled
extends Component

@export var active: bool = true

func _init(p_active: bool = true):
	active = p_active
```

- [ ] **Step 4: Create c_interactable.gd**

```gdscript
# ecs/components/c_interactable.gd
class_name C_Interactable
extends Component

enum InteractType { BOULDER, SWITCH }
enum InteractState { DEFAULT, ACTIVATED }

@export var type: InteractType = InteractType.BOULDER
@export var state: InteractState = InteractState.DEFAULT

func _init(p_type: InteractType = InteractType.BOULDER):
	type = p_type
	state = InteractState.DEFAULT
```

- [ ] **Step 5: Create c_timeline_linked.gd**

```gdscript
# ecs/components/c_timeline_linked.gd
class_name C_TimelineLinked
extends Component

## The entity ID of the linked counterpart in the other era.
@export var linked_entity_id: String = ""

func _init(p_linked_id: String = ""):
	linked_entity_id = p_linked_id
```

- [ ] **Step 6: Commit**

```bash
git add project/hosts/complete-app/ecs/components/
git commit -m "feat: add ECS components for dual-timeline prototype

Components: C_TimelineEra, C_GridPosition, C_PlayerControlled,
C_Interactable, C_TimelineLinked"
```

---

## Task 2: Player Entity

**Files:**
- Create: `project/hosts/complete-app/ecs/entities/e_player.gd`

- [ ] **Step 1: Create e_player.gd**

```gdscript
# ecs/entities/e_player.gd
class_name E_Player
extends Entity

@export var era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER
@export var start_col: int = 0
@export var start_row: int = 0

func define_components() -> Array:
	return [
		C_TimelineEra.new(era),
		C_GridPosition.new(start_col, start_row),
		C_PlayerControlled.new(era == C_TimelineEra.Era.FATHER),
	]

func on_ready():
	var grid_pos = get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		position = Vector2(grid_pos.col * 32, grid_pos.row * 32)
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/ecs/entities/e_player.gd
git commit -m "feat: add E_Player entity with era, grid position, and player control"
```

---

## Task 3: Interactable Entity

**Files:**
- Create: `project/hosts/complete-app/ecs/entities/e_interactable.gd`

- [ ] **Step 1: Create e_interactable.gd**

```gdscript
# ecs/entities/e_interactable.gd
class_name E_Interactable
extends Entity

@export var era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER
@export var start_col: int = 0
@export var start_row: int = 0
@export var interact_type: C_Interactable.InteractType = C_Interactable.InteractType.BOULDER
@export var linked_id: String = ""

func define_components() -> Array:
	return [
		C_TimelineEra.new(era),
		C_GridPosition.new(start_col, start_row),
		C_Interactable.new(interact_type),
		C_TimelineLinked.new(linked_id),
	]

func on_ready():
	var grid_pos = get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		position = Vector2(grid_pos.col * 32, grid_pos.row * 32)
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/ecs/entities/e_interactable.gd
git commit -m "feat: add E_Interactable entity with timeline linking"
```

---

## Task 4: Player Input System

**Files:**
- Create: `project/hosts/complete-app/ecs/systems/s_player_input.gd`

- [ ] **Step 1: Create s_player_input.gd**

This system reads directional input and updates the active player's grid position. It only processes the player entity whose `C_PlayerControlled.active` is true.

```gdscript
# ecs/systems/s_player_input.gd
class_name S_PlayerInput
extends System

## Tile size in pixels for collision map lookup.
const TILE_SIZE := 32

## Cooldown between moves in seconds (tile-based movement pace).
var move_cooldown := 0.15
var _cooldown_timer := 0.0

func query() -> QueryBuilder:
	return q.with_all([C_PlayerControlled, C_GridPosition, C_TimelineEra])

func process(entities: Array[Entity], _components: Array, delta: float) -> void:
	_cooldown_timer -= delta
	if _cooldown_timer > 0.0:
		return

	var direction := Vector2i.ZERO
	if Input.is_action_pressed("ui_right"):
		direction = Vector2i.RIGHT
	elif Input.is_action_pressed("ui_left"):
		direction = Vector2i.LEFT
	elif Input.is_action_pressed("ui_down"):
		direction = Vector2i.DOWN
	elif Input.is_action_pressed("ui_up"):
		direction = Vector2i.UP

	if direction == Vector2i.ZERO:
		return

	for entity in entities:
		var pc = entity.get_component(C_PlayerControlled) as C_PlayerControlled
		if not pc or not pc.active:
			continue

		var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
		grid_pos.facing = direction

		var new_col = grid_pos.col + direction.x
		var new_row = grid_pos.row + direction.y

		# Check walkability via the tilemap. The tilemap reference is stored
		# on the entity's parent viewport scene. We look it up by era.
		var era_comp = entity.get_component(C_TimelineEra) as C_TimelineEra
		var tilemap = _get_tilemap_for_era(era_comp.era)
		if tilemap and _is_tile_walkable(tilemap, new_col, new_row):
			# Also check no other entity occupies the target tile in this era
			if not _is_tile_occupied(new_col, new_row, era_comp.era, entity):
				grid_pos.col = new_col
				grid_pos.row = new_row
				_cooldown_timer = move_cooldown

func _get_tilemap_for_era(era: C_TimelineEra.Era) -> TileMapLayer:
	# Tilemaps are stored as metadata on the World node by main.gd.
	var world_node = ECS.world as Node
	var meta_key = "father_tilemap" if era == C_TimelineEra.Era.FATHER else "son_tilemap"
	if world_node.has_meta(meta_key):
		return world_node.get_meta(meta_key) as TileMapLayer
	return null

func _is_tile_walkable(tilemap: TileMapLayer, col: int, row: int) -> bool:
	var cell_coords = Vector2i(col, row)
	var source_id = tilemap.get_cell_source_id(cell_coords)
	if source_id == -1:
		return false  # No tile = not walkable (out of bounds)
	# Use custom data layer "walkable" on the tileset.
	var tile_data = tilemap.get_cell_tile_data(cell_coords)
	if tile_data:
		return tile_data.get_custom_data("walkable") as bool
	return false

func _is_tile_occupied(col: int, row: int, era: C_TimelineEra.Era, exclude: Entity) -> bool:
	var all_entities = ECS.world.query.with_all([C_GridPosition, C_TimelineEra]).execute()
	for e in all_entities:
		if e == exclude:
			continue
		var e_era = e.get_component(C_TimelineEra) as C_TimelineEra
		if e_era.era != era:
			continue
		var e_pos = e.get_component(C_GridPosition) as C_GridPosition
		if e_pos.col == col and e_pos.row == row:
			return true
	return false
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/ecs/systems/s_player_input.gd
git commit -m "feat: add player input system with grid-based movement and collision"
```

---

## Task 5: Grid Movement System

**Files:**
- Create: `project/hosts/complete-app/ecs/systems/s_grid_movement.gd`

- [ ] **Step 1: Create s_grid_movement.gd**

This system smoothly lerps the Node2D position of entities to match their grid position. Purely visual — the grid position component is the source of truth.

```gdscript
# ecs/systems/s_grid_movement.gd
class_name S_GridMovement
extends System

const TILE_SIZE := 32
const MOVE_SPEED := 8.0  # Lerp weight per second

func query() -> QueryBuilder:
	return q.with_all([C_GridPosition])

func process(entities: Array[Entity], _components: Array, delta: float) -> void:
	for entity in entities:
		var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
		var target = Vector2(grid_pos.col * TILE_SIZE, grid_pos.row * TILE_SIZE)
		entity.position = entity.position.lerp(target, MOVE_SPEED * delta)
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/ecs/systems/s_grid_movement.gd
git commit -m "feat: add grid movement system with smooth lerp animation"
```

---

## Task 6: Interaction System

**Files:**
- Create: `project/hosts/complete-app/ecs/systems/s_interaction.gd`

- [ ] **Step 1: Create s_interaction.gd**

Handles the action key (Enter/Space). When the active player faces an interactable, activate it and propagate the effect to the linked entity in the other era.

```gdscript
# ecs/systems/s_interaction.gd
class_name S_Interaction
extends System

func query() -> QueryBuilder:
	return q.with_all([C_PlayerControlled, C_GridPosition, C_TimelineEra])

func process(entities: Array[Entity], _components: Array, _delta: float) -> void:
	if not Input.is_action_just_pressed("ui_accept"):
		return

	for entity in entities:
		var pc = entity.get_component(C_PlayerControlled) as C_PlayerControlled
		if not pc or not pc.active:
			continue

		var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
		var era_comp = entity.get_component(C_TimelineEra) as C_TimelineEra

		# Calculate the tile the player is facing
		var target_col = grid_pos.col + grid_pos.facing.x
		var target_row = grid_pos.row + grid_pos.facing.y

		# Find interactable at that position in the same era
		var interactables = ECS.world.query.with_all([
			C_Interactable, C_GridPosition, C_TimelineEra
		]).execute()

		for target_entity in interactables:
			var t_era = target_entity.get_component(C_TimelineEra) as C_TimelineEra
			if t_era.era != era_comp.era:
				continue
			var t_pos = target_entity.get_component(C_GridPosition) as C_GridPosition
			if t_pos.col != target_col or t_pos.row != target_row:
				continue

			# Found the interactable — activate it
			var interactable = target_entity.get_component(C_Interactable) as C_Interactable
			if interactable.state == C_Interactable.InteractState.DEFAULT:
				_activate(target_entity, interactable)
			break

func _activate(entity: Entity, interactable: C_Interactable) -> void:
	interactable.state = C_Interactable.InteractState.ACTIVATED

	# Visual feedback: hide the entity (boulder pushed away, switch flipped)
	entity.visible = false

	# Propagate to linked entity in other era
	var link = entity.get_component(C_TimelineLinked) as C_TimelineLinked
	if not link or link.linked_entity_id.is_empty():
		return

	var all_linked = ECS.world.query.with_all([C_TimelineLinked, C_Interactable]).execute()
	for linked_entity in all_linked:
		if linked_entity.id == link.linked_entity_id:
			var linked_interact = linked_entity.get_component(C_Interactable) as C_Interactable
			linked_interact.state = C_Interactable.InteractState.ACTIVATED
			# The linked entity becomes passable (e.g., blocked path opens)
			linked_entity.visible = false
			break
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/ecs/systems/s_interaction.gd
git commit -m "feat: add interaction system with cross-timeline cause-and-effect"
```

---

## Task 7: Prototype Tileset

**Files:**
- Create: Tileset via GDScript setup (no .tres file needed for prototype — define programmatically)

For the prototype, we use a simple tileset with colored rectangles. This avoids needing art assets. The tileset is created in code during scene setup.

- [ ] **Step 1: Create a tileset setup helper**

Create `project/hosts/complete-app/scripts/tileset_factory.gd`:

```gdscript
# scripts/tileset_factory.gd
class_name TilesetFactory

## Creates a simple prototype TileSet with colored tiles.
## Tile IDs:
##   Source 0 (father era):
##     Atlas coord (0,0) = grass (green)    - walkable
##     Atlas coord (1,0) = path (brown)     - walkable
##     Atlas coord (2,0) = building (dark)  - not walkable
##     Atlas coord (3,0) = water (blue)     - not walkable
##   Source 1 (son era):
##     Atlas coord (0,0) = dead grass (dark green) - walkable
##     Atlas coord (1,0) = path (brown)            - walkable
##     Atlas coord (2,0) = ruin (dark brown)       - not walkable
##     Atlas coord (3,0) = blocked (gray)          - not walkable

const TILE_SIZE := 32

static func create_tileset() -> TileSet:
	var tileset = TileSet.new()
	tileset.tile_size = Vector2i(TILE_SIZE, TILE_SIZE)

	# Add custom data layer for walkability
	tileset.add_custom_data_layer()
	tileset.set_custom_data_layer_name(0, "walkable")
	tileset.set_custom_data_layer_type(0, TYPE_BOOL)

	# Create father era source (source_id = 0)
	_add_colored_source(tileset, 0, [
		Color(0.23, 0.42, 0.12),  # grass
		Color(0.55, 0.45, 0.33),  # path
		Color(0.42, 0.35, 0.23),  # building
		Color(0.17, 0.35, 0.55),  # water
	], [true, true, false, false])

	# Create son era source (source_id = 1)
	_add_colored_source(tileset, 1, [
		Color(0.29, 0.29, 0.16),  # dead grass
		Color(0.55, 0.45, 0.33),  # path
		Color(0.29, 0.23, 0.17),  # ruin
		Color(0.33, 0.33, 0.33),  # blocked
	], [true, true, false, false])

	return tileset

static func _add_colored_source(
	tileset: TileSet,
	source_id: int,
	colors: Array,
	walkable_flags: Array
) -> void:
	# Create an image atlas with colored tiles side by side
	var atlas_width = colors.size() * TILE_SIZE
	var image = Image.create(atlas_width, TILE_SIZE, false, Image.FORMAT_RGBA8)

	for i in colors.size():
		var color: Color = colors[i]
		for x in range(i * TILE_SIZE, (i + 1) * TILE_SIZE):
			for y in range(TILE_SIZE):
				# Add subtle border for visibility
				if x == i * TILE_SIZE or x == (i + 1) * TILE_SIZE - 1 or y == 0 or y == TILE_SIZE - 1:
					image.set_pixel(x, y, color.darkened(0.3))
				else:
					image.set_pixel(x, y, color)

	var texture = ImageTexture.create_from_image(image)
	var atlas_source = TileSetAtlasSource.new()
	atlas_source.texture = texture
	atlas_source.texture_region_size = Vector2i(TILE_SIZE, TILE_SIZE)
	tileset.add_source(atlas_source, source_id)

	# Create tiles and set walkability data
	for i in colors.size():
		atlas_source.create_tile(Vector2i(i, 0))
		var tile_data = atlas_source.get_tile_data(Vector2i(i, 0), 0)
		tile_data.set_custom_data("walkable", walkable_flags[i])
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/scripts/tileset_factory.gd
git commit -m "feat: add TilesetFactory for prototype colored-tile tileset"
```

---

## Task 8: Main Scene Assembly

**Files:**
- Modify: `project/hosts/complete-app/scenes/main.tscn` (replace current test scene)
- Create: `project/hosts/complete-app/scripts/main.gd`

This is the largest task. It wires everything together: creates the World, spawns entities, builds the two game views, and drives the ECS loop.

- [ ] **Step 1: Create main.gd**

```gdscript
# scripts/main.gd
extends Control

## Map definitions for each era. Each is a 2D array of atlas coords.
## Atlas coords reference TilesetFactory source IDs:
##   Father (source 0): (0,0)=grass, (1,0)=path, (2,0)=building, (3,0)=water
##   Son    (source 1): (0,0)=dead_grass, (1,0)=path, (2,0)=ruin, (3,0)=blocked

const MAP_WIDTH := 10
const MAP_HEIGHT := 8
const TILE_SIZE := 32

# Father's map: a small town with paths, buildings, water
const FATHER_MAP := [
	[0,0,0,2,2,0,0,0,3,3],
	[0,0,1,1,1,1,0,0,3,3],
	[0,1,1,0,0,1,1,0,0,3],
	[2,1,0,0,0,0,1,0,0,0],
	[2,1,0,0,0,0,1,1,1,0],
	[0,1,1,0,2,0,0,0,1,0],
	[0,0,1,1,1,1,1,1,1,0],
	[0,0,0,0,0,0,0,0,0,0],
]

# Son's map: same layout but ruined. Buildings become ruins, water blocked.
const SON_MAP := [
	[0,0,0,2,2,0,0,0,3,3],
	[0,0,1,1,1,1,0,0,3,3],
	[0,1,1,0,0,1,1,0,0,3],
	[2,1,0,0,0,0,1,0,0,0],
	[2,1,0,0,0,0,1,1,1,0],
	[0,1,1,0,2,0,0,0,1,0],
	[0,0,1,1,1,1,1,1,1,0],
	[0,0,0,0,0,0,0,0,0,0],
]

## The boulder in father's map is at (5, 3). It blocks path tile (5, 3) in son's map.
const BOULDER_COL := 5
const BOULDER_ROW := 3
const BLOCKED_COL := 5
const BLOCKED_ROW := 3

var world: World
var tileset: TileSet

var father_view: SubViewportContainer
var son_view: SubViewportContainer
var father_player: E_Player
var son_player: E_Player
var father_tilemap: TileMapLayer
var son_tilemap: TileMapLayer

var active_era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER

# World map
var world_map_layer: CanvasLayer
var map_is_open := false

# Layout constants (percentage of viewport)
const ACTIVE_VIEW_SCALE := 0.50
const INACTIVE_VIEW_SCALE := 0.40

func _ready() -> void:
	# Create tileset
	tileset = TilesetFactory.create_tileset()

	# Create ECS World
	world = World.new()
	world.name = "World"
	add_child(world)
	ECS.world = world

	# Build the world map background
	_build_world_map()

	# Build the two game views
	father_view = _build_game_view(C_TimelineEra.Era.FATHER, FATHER_MAP, 0)
	son_view = _build_game_view(C_TimelineEra.Era.SON, SON_MAP, 1)
	add_child(father_view)
	add_child(son_view)

	# Store tilemap references as metadata on world node for systems to find
	world.set_meta("father_tilemap", father_tilemap)
	world.set_meta("son_tilemap", son_tilemap)

	# Spawn players — add_entity with add_to_tree=false, then reparent into
	# the correct SubViewport so they render in the right view.
	father_player = E_Player.new()
	father_player.era = C_TimelineEra.Era.FATHER
	father_player.start_col = 2
	father_player.start_row = 2
	father_player.name = "FatherPlayer"
	father_view.get_node("SubViewport").add_child(father_player)
	ECS.world.add_entity(father_player, [], false)

	son_player = E_Player.new()
	son_player.era = C_TimelineEra.Era.SON
	son_player.start_col = 7
	son_player.start_row = 4
	son_player.name = "SonPlayer"
	son_view.get_node("SubViewport").add_child(son_player)
	ECS.world.add_entity(son_player, [], false)

	# Spawn the boulder (father era) and blocked path (son era)
	var boulder = E_Interactable.new()
	boulder.era = C_TimelineEra.Era.FATHER
	boulder.start_col = BOULDER_COL
	boulder.start_row = BOULDER_ROW
	boulder.interact_type = C_Interactable.InteractType.BOULDER
	boulder.id = "boulder_father"
	boulder.linked_id = "blocked_son"
	boulder.name = "Boulder"
	father_view.get_node("SubViewport").add_child(boulder)
	ECS.world.add_entity(boulder, [], false)

	var blocked = E_Interactable.new()
	blocked.era = C_TimelineEra.Era.SON
	blocked.start_col = BLOCKED_COL
	blocked.start_row = BLOCKED_ROW
	blocked.interact_type = C_Interactable.InteractType.BOULDER
	blocked.id = "blocked_son"
	blocked.linked_id = "boulder_father"
	blocked.name = "BlockedPath"
	son_view.get_node("SubViewport").add_child(blocked)
	ECS.world.add_entity(blocked, [], false)

	# Add systems to the world
	var input_system = S_PlayerInput.new()
	var movement_system = S_GridMovement.new()
	var interaction_system = S_Interaction.new()
	world.add_systems([input_system, movement_system, interaction_system])

	# Set initial layout
	_update_layout()
	get_viewport().size_changed.connect(_update_layout)

func _input(event: InputEvent) -> void:
	# Tab toggles active era
	if event is InputEventKey and event.pressed and event.keycode == KEY_TAB:
		get_viewport().set_input_as_handled()
		_toggle_era()
	# M toggles world map
	if event is InputEventKey and event.pressed and event.keycode == KEY_M:
		get_viewport().set_input_as_handled()
		_toggle_map()

func _process(delta: float) -> void:
	ECS.process(delta)

	# Update cameras
	var active_player = father_player if active_era == C_TimelineEra.Era.FATHER else son_player
	var inactive_player = son_player if active_era == C_TimelineEra.Era.FATHER else father_player
	var active_view = father_view if active_era == C_TimelineEra.Era.FATHER else son_view
	var inactive_view = son_view if active_era == C_TimelineEra.Era.FATHER else father_view

	var active_cam = active_view.get_node("SubViewport/Camera2D") as Camera2D
	var inactive_cam = inactive_view.get_node("SubViewport/Camera2D") as Camera2D
	if active_player:
		active_cam.position = active_cam.position.lerp(active_player.position, 0.1)
	if inactive_player:
		inactive_cam.position = inactive_cam.position.lerp(inactive_player.position, 0.1)

	# Draw player sprites (simple colored rects drawn via _draw on entities)
	queue_redraw()

func _toggle_era() -> void:
	if active_era == C_TimelineEra.Era.FATHER:
		active_era = C_TimelineEra.Era.SON
	else:
		active_era = C_TimelineEra.Era.FATHER

	# Update player control
	var father_pc = father_player.get_component(C_PlayerControlled) as C_PlayerControlled
	var son_pc = son_player.get_component(C_PlayerControlled) as C_PlayerControlled
	father_pc.active = (active_era == C_TimelineEra.Era.FATHER)
	son_pc.active = (active_era == C_TimelineEra.Era.SON)

	_update_layout()

func _toggle_map() -> void:
	map_is_open = not map_is_open
	if world_map_layer:
		world_map_layer.visible = true  # Map bg is always visible
	# Slide views offscreen when map is open
	_update_layout()

func _update_layout() -> void:
	var viewport_size = get_viewport_rect().size
	var active_view_node: SubViewportContainer
	var inactive_view_node: SubViewportContainer

	if active_era == C_TimelineEra.Era.FATHER:
		active_view_node = father_view
		inactive_view_node = son_view
	else:
		active_view_node = son_view
		inactive_view_node = father_view

	if map_is_open:
		# Slide both views off-screen
		var tween = create_tween().set_parallel(true)
		tween.tween_property(active_view_node, "position",
			Vector2(-active_view_node.size.x - 20, active_view_node.position.y), 0.4) \
			.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
		tween.tween_property(inactive_view_node, "position",
			Vector2(viewport_size.x + 20, inactive_view_node.position.y), 0.4) \
			.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
	else:
		# Active view: larger, top-left area, in front
		var active_w = viewport_size.x * ACTIVE_VIEW_SCALE
		var active_h = viewport_size.y * ACTIVE_VIEW_SCALE
		var active_pos = Vector2(20, 20)

		# Inactive view: smaller, bottom-right area, behind
		var inactive_w = viewport_size.x * INACTIVE_VIEW_SCALE
		var inactive_h = viewport_size.y * INACTIVE_VIEW_SCALE
		var inactive_pos = Vector2(
			viewport_size.x - inactive_w - 20,
			viewport_size.y - inactive_h - 20
		)

		active_view_node.size = Vector2(active_w, active_h)
		active_view_node.get_node("SubViewport").size = Vector2i(int(active_w), int(active_h))
		inactive_view_node.size = Vector2(inactive_w, inactive_h)
		inactive_view_node.get_node("SubViewport").size = Vector2i(int(inactive_w), int(inactive_h))

		# Z-order: active in front
		move_child(active_view_node, get_child_count() - 1)

		# Animate position
		var tween = create_tween().set_parallel(true)
		tween.tween_property(active_view_node, "position", active_pos, 0.3) \
			.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
		tween.tween_property(inactive_view_node, "position", inactive_pos, 0.3) \
			.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)

		# Visual state
		active_view_node.modulate.a = 1.0
		inactive_view_node.modulate.a = 0.75

func _build_game_view(era: C_TimelineEra.Era, map_data: Array, source_id: int) -> SubViewportContainer:
	var container = SubViewportContainer.new()
	container.stretch = true
	container.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var viewport = SubViewport.new()
	viewport.name = "SubViewport"
	viewport.transparent_bg = false
	viewport.canvas_item_default_texture_filter = SubViewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	container.add_child(viewport)

	# TileMapLayer
	var tilemap = TileMapLayer.new()
	tilemap.name = "TileMapLayer"
	tilemap.tile_set = tileset
	viewport.add_child(tilemap)

	# Populate tiles
	for row in range(MAP_HEIGHT):
		for col in range(MAP_WIDTH):
			var atlas_coord = Vector2i(map_data[row][col], 0)
			tilemap.set_cell(Vector2i(col, row), source_id, atlas_coord)

	# Store reference
	if era == C_TimelineEra.Era.FATHER:
		father_tilemap = tilemap
	else:
		son_tilemap = tilemap

	# Camera
	var camera = Camera2D.new()
	camera.name = "Camera2D"
	camera.position = Vector2(MAP_WIDTH * TILE_SIZE / 2, MAP_HEIGHT * TILE_SIZE / 2)
	viewport.add_child(camera)

	# Era label
	var label = Label.new()
	label.name = "EraLabel"
	var era_text = "FATHER ERA" if era == C_TimelineEra.Era.FATHER else "SON ERA"
	label.text = era_text
	label.add_theme_font_size_override("font_size", 12)
	label.position = Vector2(8, 4)
	if era == C_TimelineEra.Era.FATHER:
		label.add_theme_color_override("font_color", Color(1.0, 0.8, 0.0))
	else:
		label.add_theme_color_override("font_color", Color(1.0, 0.53, 0.53))
	container.add_child(label)

	return container

func _build_world_map() -> void:
	world_map_layer = CanvasLayer.new()
	world_map_layer.name = "WorldMapLayer"
	world_map_layer.layer = -1  # Behind everything
	add_child(world_map_layer)

	var bg = ColorRect.new()
	bg.name = "MapBackground"
	bg.color = Color(0.77, 0.64, 0.40)  # Parchment color
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	world_map_layer.add_child(bg)

	# Location labels
	var locations = {
		"Aldenmere": Vector2(0.35, 0.35),
		"Haven Town": Vector2(0.65, 0.55),
		"Iron Peaks": Vector2(0.55, 0.15),
		"Silverwood": Vector2(0.2, 0.3),
		"Ashenmoor": Vector2(0.3, 0.75),
		"Duskholm": Vector2(0.8, 0.7),
	}

	for loc_name in locations:
		var label = Label.new()
		label.text = loc_name
		label.add_theme_font_size_override("font_size", 14)
		label.add_theme_color_override("font_color", Color(0.35, 0.24, 0.11))
		# Position will be set in _process based on viewport size
		label.name = "Loc_" + loc_name.replace(" ", "")
		label.position = locations[loc_name] * Vector2(1024, 600)  # Default, updated on resize
		world_map_layer.add_child(label)
```

- [ ] **Step 2: Create the main scene (main.tscn)**

Replace the existing test scene. The root is a Control node with the main.gd script:

```
[gd_scene format=3]

[ext_resource type="Script" path="res://scripts/main.gd" id="1"]

[node name="Main" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
script = ExtResource("1")
```

Save this as `scenes/main.tscn` (overwrite the existing file).

- [ ] **Step 3: Update project.godot main scene path**

The main scene is already `res://scenes/main.tscn` so no change needed.

- [ ] **Step 4: Commit**

```bash
git add project/hosts/complete-app/scripts/main.gd project/hosts/complete-app/scenes/main.tscn
git commit -m "feat: assemble main scene with dual-timeline views, world map, and ECS wiring"
```

---

## Task 9: Player Visual Sprites

**Files:**
- Modify: `project/hosts/complete-app/ecs/entities/e_player.gd`
- Modify: `project/hosts/complete-app/ecs/entities/e_interactable.gd`

Add simple visual representation (colored rectangles) to entities so they are visible in the viewports.

- [ ] **Step 1: Add _draw() to e_player.gd**

Add drawing to make the player visible as a colored square:

```gdscript
# ecs/entities/e_player.gd
class_name E_Player
extends Entity

@export var era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER
@export var start_col: int = 0
@export var start_row: int = 0

const TILE_SIZE := 32
const FATHER_COLOR := Color(1.0, 0.8, 0.0)  # Gold
const SON_COLOR := Color(0.6, 0.8, 1.0)  # Light blue

func define_components() -> Array:
	return [
		C_TimelineEra.new(era),
		C_GridPosition.new(start_col, start_row),
		C_PlayerControlled.new(era == C_TimelineEra.Era.FATHER),
	]

func on_ready():
	var grid_pos = get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		position = Vector2(grid_pos.col * TILE_SIZE, grid_pos.row * TILE_SIZE)

func _draw() -> void:
	var color = FATHER_COLOR if era == C_TimelineEra.Era.FATHER else SON_COLOR
	# Draw character as a small square with a direction indicator
	draw_rect(Rect2(4, 4, TILE_SIZE - 8, TILE_SIZE - 8), color)
	# Direction arrow
	var grid_pos = get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		var center = Vector2(TILE_SIZE / 2.0, TILE_SIZE / 2.0)
		var arrow_end = center + Vector2(grid_pos.facing) * 10.0
		draw_line(center, arrow_end, Color.WHITE, 2.0)

func _process(_delta: float) -> void:
	queue_redraw()
```

- [ ] **Step 2: Add _draw() to e_interactable.gd**

```gdscript
# ecs/entities/e_interactable.gd
class_name E_Interactable
extends Entity

@export var era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER
@export var start_col: int = 0
@export var start_row: int = 0
@export var interact_type: C_Interactable.InteractType = C_Interactable.InteractType.BOULDER
@export var linked_id: String = ""

const TILE_SIZE := 32
const BOULDER_COLOR := Color(0.5, 0.5, 0.5)  # Gray
const BLOCKED_COLOR := Color(0.4, 0.2, 0.2)  # Dark red

func define_components() -> Array:
	return [
		C_TimelineEra.new(era),
		C_GridPosition.new(start_col, start_row),
		C_Interactable.new(interact_type),
		C_TimelineLinked.new(linked_id),
	]

func on_ready():
	var grid_pos = get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		position = Vector2(grid_pos.col * TILE_SIZE, grid_pos.row * TILE_SIZE)

func _draw() -> void:
	var interactable = get_component(C_Interactable) as C_Interactable
	if not interactable or interactable.state == C_Interactable.InteractState.ACTIVATED:
		return  # Don't draw activated (removed) objects
	var color = BOULDER_COLOR if era == C_TimelineEra.Era.FATHER else BLOCKED_COLOR
	# Draw as a circle to distinguish from player squares
	draw_circle(Vector2(TILE_SIZE / 2.0, TILE_SIZE / 2.0), TILE_SIZE / 3.0, color)

func _process(_delta: float) -> void:
	queue_redraw()
```

- [ ] **Step 3: Commit**

```bash
git add project/hosts/complete-app/ecs/entities/
git commit -m "feat: add visual sprites to player and interactable entities"
```

---

## Task 10: Input Actions Setup

**Files:**
- Modify: `project/hosts/complete-app/project.godot`

Add the custom input actions used by the systems (toggle_map). The default `ui_*` actions already cover movement and accept.

- [ ] **Step 1: Add input map to project.godot**

Add the following section to `project.godot`:

```ini
[input]

toggle_map={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":77,"physical_keycode":0,"key_label":0,"unicode":109,"location":0,"echo":false,"script":null)
]
}
```

Note: Keycode 77 = M key. The Tab key for era toggle is handled directly in `main.gd._input()` since Tab has special behavior in Godot UI.

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/project.godot
git commit -m "feat: add toggle_map input action (M key)"
```

---

## Task 11: Build and Test Web Export

**Files:** No new files. This is a verification step.

- [ ] **Step 1: Build the web export**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad && task build
```

Expected: Godot exports to `build/_artifacts/<version>/web/complete-app.html` with no errors.

- [ ] **Step 2: Serve and test locally**

```bash
task serve
```

Open `http://localhost:8080` in a browser.

Expected behavior:
- Two game views visible: father era (gold border, top-left, larger) and son era (red border, bottom-right, smaller)
- Parchment-colored world map visible behind and around the views
- Arrow keys move the gold player square in the father view
- Press **Tab** — views swap: son becomes active (larger, front), father becomes inactive
- Arrow keys now move the blue player square in the son view
- Press **M** — both views slide off-screen revealing the world map with location names
- Press **M** again — views slide back
- In father's view, walk to the boulder (gray circle) and press **Enter/Space** facing it — boulder disappears, and the blocked path in the son's view also disappears

- [ ] **Step 3: Fix any issues found during testing**

Iterate on bugs discovered during the web test. Common issues to watch for:
- SubViewport not rendering (check `stretch = true` on container)
- Tilemap not showing (check source_id matches tileset sources)
- Input not working (check `mouse_filter = MOUSE_FILTER_IGNORE` on containers)
- Entity position wrong (check TILE_SIZE consistency across files)

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve issues found during web export testing"
```

---

## Summary

| Task | Description | Files | Depends On |
|------|-------------|-------|------------|
| 1 | ECS Components | 5 new files | None |
| 2 | Player Entity | 1 new file | Task 1 |
| 3 | Interactable Entity | 1 new file | Task 1 |
| 4 | Player Input System | 1 new file | Task 1 |
| 5 | Grid Movement System | 1 new file | Task 1 |
| 6 | Interaction System | 1 new file | Task 1 |
| 7 | Tileset Factory | 1 new file | None |
| 8 | Main Scene Assembly | 2 files (new + replace) | Tasks 1-7 |
| 9 | Player Visual Sprites | 2 modified files | Tasks 2-3 |
| 10 | Input Actions | 1 modified file | None |
| 11 | Build and Test | No files | Tasks 1-10 |

**Parallel opportunities:** Tasks 1 and 7 can run in parallel (no dependencies). After Task 1, Tasks 2-6 can be parallelized. Task 8 depends on all prior tasks. Tasks 9-10 can be done alongside Task 8. Task 11 is the final verification.
