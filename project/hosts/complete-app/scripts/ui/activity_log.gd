# scripts/ui/activity_log.gd
# Autoload: ActivityLog
# Central message bus for the activity log. Any system can push messages here.
extends Node

signal message_added(text: String)

const MAX_LINES := 50

var messages: Array[String] = []

func log_msg(text: String) -> void:
	messages.append(text)
	if messages.size() > MAX_LINES:
		messages.pop_front()
	message_added.emit(text)

func log_battle_start() -> void:
	log_msg("--- BATTLE START ---")

func log_battle_end() -> void:
	log_msg("--- BATTLE END ---")

func clear() -> void:
	messages.clear()
