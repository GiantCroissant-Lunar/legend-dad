extends GutTest

func test_default_values():
	# GameConfig should have sensible defaults before any location is loaded
	assert_eq(GameConfig.cell_size, 16, "default cell_size should be 16 (LDtk default)")
	assert_eq(GameConfig.map_width, 0, "map_width should be 0 before level load")
	assert_eq(GameConfig.map_height, 0, "map_height should be 0 before level load")
	assert_almost_eq(GameConfig.move_speed, 8.0, 0.01, "default move_speed should be 8.0")
	assert_almost_eq(GameConfig.move_cooldown, 0.15, 0.01, "default move_cooldown should be 0.15")

func test_cell_size_setter():
	var original = GameConfig.cell_size
	GameConfig.cell_size = 32
	assert_eq(GameConfig.cell_size, 32, "cell_size should be settable")
	GameConfig.cell_size = original

func test_map_dimensions_setter():
	GameConfig.map_width = 20
	GameConfig.map_height = 16
	assert_eq(GameConfig.map_width, 20)
	assert_eq(GameConfig.map_height, 16)
	GameConfig.map_width = 0
	GameConfig.map_height = 0
