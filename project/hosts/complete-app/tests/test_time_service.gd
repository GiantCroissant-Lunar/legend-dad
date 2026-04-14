extends GutTest

func after_each():
	# Restore time scale after each test
	Engine.time_scale = 1.0

func test_initial_state():
	var state = TimeService.get_state()
	assert_eq(state["paused"], false)
	assert_almost_eq(state["speed"], 1.0, 0.01)

func test_set_speed():
	TimeService.set_speed(0.5)
	assert_almost_eq(Engine.time_scale, 0.5, 0.01)
	var state = TimeService.get_state()
	assert_almost_eq(state["speed"], 0.5, 0.01)

func test_set_speed_clamps_low():
	TimeService.set_speed(0.1)
	assert_almost_eq(Engine.time_scale, 0.25, 0.01, "should clamp to 0.25 minimum")

func test_set_speed_clamps_high():
	TimeService.set_speed(10.0)
	assert_almost_eq(Engine.time_scale, 4.0, 0.01, "should clamp to 4.0 maximum")

func test_pause_and_resume():
	TimeService.set_speed(2.0)
	TimeService.pause()
	assert_almost_eq(Engine.time_scale, 0.0, 0.01)
	assert_true(TimeService.get_state()["paused"])

	TimeService.resume()
	assert_almost_eq(Engine.time_scale, 2.0, 0.01, "should restore previous speed")
	assert_false(TimeService.get_state()["paused"])

func test_pause_when_already_paused():
	TimeService.pause()
	TimeService.pause()  # should be idempotent
	assert_true(TimeService.get_state()["paused"])
	TimeService.resume()
	assert_almost_eq(Engine.time_scale, 1.0, 0.01, "should restore to 1.0 (default)")

func test_resume_when_not_paused():
	TimeService.resume()  # should be no-op
	assert_false(TimeService.get_state()["paused"])
	assert_almost_eq(Engine.time_scale, 1.0, 0.01)
