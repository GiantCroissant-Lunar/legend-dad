# WebSocket client — connects to the Node.js server, relays commands to
# GameActions bus, and pushes game state changes back to the server.
extends Node

const DIRECTION_MAP := {
	"up": Vector2i.UP,
	"down": Vector2i.DOWN,
	"left": Vector2i.LEFT,
	"right": Vector2i.RIGHT,
}

@export var server_url := "ws://localhost:3000"

var _socket := WebSocketPeer.new()
var _connected := false
var _reconnect_timer := 0.0
var _reconnect_delay := 2.0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_connect_to_server()

func _connect_to_server() -> void:
	var err = _socket.connect_to_url(server_url)
	if err != OK:
		push_warning("[ws_client] failed to initiate connection: %s" % err)

func _process(delta: float) -> void:
	_socket.poll()

	var state = _socket.get_ready_state()

	match state:
		WebSocketPeer.STATE_OPEN:
			if not _connected:
				_connected = true
				_reconnect_timer = 0.0
				print("[ws_client] connected to %s" % server_url)
				_send_handshake()

			while _socket.get_available_packet_count() > 0:
				var raw = _socket.get_packet().get_string_from_utf8()
				_handle_message(raw)

		WebSocketPeer.STATE_CLOSED:
			if _connected:
				_connected = false
				print("[ws_client] disconnected (code=%s)" % _socket.get_close_code())

			_reconnect_timer -= delta
			if _reconnect_timer <= 0.0:
				_reconnect_timer = _reconnect_delay
				_socket = WebSocketPeer.new()
				_connect_to_server()

		WebSocketPeer.STATE_CONNECTING:
			pass # waiting

		WebSocketPeer.STATE_CLOSING:
			pass # closing

func _send_handshake() -> void:
	_send_json({ "type": "handshake", "client_type": "godot", "name": "legend-dad" })

func _handle_message(raw: String) -> void:
	var json = JSON.new()
	var err = json.parse(raw)
	if err != OK:
		push_warning("[ws_client] invalid JSON: %s" % raw)
		return

	var msg = json.data
	if not msg is Dictionary or not msg.has("type"):
		return

	match msg["type"]:
		"handshake_ack":
			print("[ws_client] handshake OK, session=%s" % msg.get("session_id", "?"))
		"command":
			_handle_command(msg)
		"error":
			push_warning("[ws_client] server error: %s" % msg.get("error", "unknown"))

func _handle_command(msg: Dictionary) -> void:
	var action = msg.get("action", "")
	var payload = msg.get("payload", {})
	var cmd_id = msg.get("id", "")

	match action:
		"move":
			var dir_str = payload.get("direction", "")
			if dir_str in DIRECTION_MAP:
				GameActions.move(DIRECTION_MAP[dir_str])
				_send_command_ack(cmd_id, true)
			else:
				_send_command_ack(cmd_id, false, "invalid direction: %s" % dir_str)

		"interact":
			GameActions.interact()
			_send_command_ack(cmd_id, true)

		"switch_era":
			GameActions.switch_era()
			_send_command_ack(cmd_id, true)

		"get_state":
			_send_state_snapshot()
			_send_command_ack(cmd_id, true)

		"time_set_speed":
			var speed: float = payload.get("speed", 1.0)
			TimeService.set_speed(speed)
			_send_command_ack(cmd_id, true)

		"time_pause":
			TimeService.pause()
			_send_command_ack(cmd_id, true)

		"time_resume":
			TimeService.resume()
			_send_command_ack(cmd_id, true)

		"time_step":
			TimeService.step_frame()
			_send_command_ack(cmd_id, true)

		_:
			_send_command_ack(cmd_id, false, "unknown action: %s" % action)

func _send_command_ack(cmd_id: String, success: bool, error: String = "") -> void:
	var ack := { "type": "command_ack", "id": cmd_id, "success": success }
	if not error.is_empty():
		ack["error"] = error
	else:
		ack["error"] = null
	_send_json(ack)

## Serialize and send the full game state snapshot.
## Called on get_state command and on initial connect.
func _send_state_snapshot() -> void:
	var entities_data := []
	var all_entities = ECS.world.query.with_all([C_GridPosition, C_TimelineEra]).execute()

	for entity in all_entities:
		var entry := { "entity_id": entity.name, "components": {} }

		var gp = entity.get_component(C_GridPosition) as C_GridPosition
		if gp:
			entry["components"]["grid_position"] = {
				"col": gp.col, "row": gp.row,
				"facing": _vec2i_to_string(gp.facing),
			}

		var era = entity.get_component(C_TimelineEra) as C_TimelineEra
		if era:
			entry["components"]["timeline_era"] = {
				"era": "FATHER" if era.era == C_TimelineEra.Era.FATHER else "SON",
			}

		var pc = entity.get_component(C_PlayerControlled) as C_PlayerControlled
		if pc:
			entry["components"]["player_controlled"] = { "active": pc.active }

		var enemy = entity.get_component(C_Enemy) as C_Enemy
		if enemy:
			entry["components"]["enemy"] = { "enemy_type": enemy.enemy_type }

		var inter = entity.get_component(C_Interactable) as C_Interactable
		if inter:
			entry["components"]["interactable"] = {
				"type": "BOULDER" if inter.type == C_Interactable.InteractType.BOULDER else "SWITCH",
				"state": "ACTIVATED" if inter.state == C_Interactable.InteractState.ACTIVATED else "DEFAULT",
			}

		entities_data.append(entry)

	# Determine active era from main script (accessible via get_tree)
	var main_node = get_tree().root.get_node_or_null("Main")
	var active_era := "FATHER"
	var active_entity_id := "father"
	if main_node and "active_era" in main_node:
		active_era = "FATHER" if main_node.active_era == C_TimelineEra.Era.FATHER else "SON"
		active_entity_id = "son" if active_era == "SON" else "father"

	# Include map tile data for agent reasoning
	var map_data := {}
	if main_node and "FATHER_MAP" in main_node and "SON_MAP" in main_node:
		map_data = {
			"width": main_node.MAP_WIDTH,
			"height": main_node.MAP_HEIGHT,
			"father_tiles": main_node.FATHER_MAP,
			"son_tiles": main_node.SON_MAP,
		}

	_send_json({
		"type": "state_snapshot",
		"data": {
			"active_era": active_era,
			"active_entity_id": active_entity_id,
			"entities": entities_data,
			"map": map_data,
			"battle": null,
		},
	})

func send_state_event(event_name: String, data: Dictionary) -> void:
	if not _connected:
		return
	_send_json({
		"type": "state_event",
		"event": event_name,
		"data": data,
	})

func _send_json(data: Dictionary) -> void:
	if _connected:
		_socket.send_text(JSON.stringify(data))

func _vec2i_to_string(v: Vector2i) -> String:
	if v == Vector2i.UP: return "up"
	if v == Vector2i.DOWN: return "down"
	if v == Vector2i.LEFT: return "left"
	if v == Vector2i.RIGHT: return "right"
	return "down"
