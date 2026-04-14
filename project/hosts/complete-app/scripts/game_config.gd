class_name GameConfigClass
extends Node

## Single source of truth for cell/tile dimensions and tunable gameplay constants.
## Populated at runtime by LocationManager (cell_size) and main.gd (map dimensions).
## Never hardcode these values elsewhere — always read from GameConfig.

## Cell size in pixels, read from LDtk project's defaultGridSize.
var cell_size: int = 16

## Current level dimensions in cells.
var map_width: int = 0
var map_height: int = 0

## Movement tuning.
var move_speed: float = 8.0
var move_cooldown: float = 0.15
