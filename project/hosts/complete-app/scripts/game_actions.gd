# project/hosts/complete-app/scripts/game_actions.gd
# Autoload: GameActions
# Semantic action bus — decouples input sources from game logic.
# Both keyboard input and WS commands dispatch through this bus.
extends Node

signal action_move(direction: Vector2i)
signal action_interact
signal action_switch_era
signal state_changed(event_name: String, data: Dictionary)

## Dispatch a movement action.
func move(direction: Vector2i) -> void:
	action_move.emit(direction)

## Dispatch an interact action.
func interact() -> void:
	action_interact.emit()

## Dispatch a timeline switch action.
func switch_era() -> void:
	action_switch_era.emit()
