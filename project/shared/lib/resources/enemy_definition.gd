extends Resource
class_name EnemyDefinition

@export var id: String
@export var display_name: String
@export var sprite: Texture2D
@export var max_hp: int = 1
@export var attack: int = 1
@export var defense: int = 0
@export var xp_reward: int = 1
@export var behavior_tree: PackedScene  # Beehave tree, optional
