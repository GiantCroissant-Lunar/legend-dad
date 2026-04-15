import { defineConfig } from "@playwright/test";

export default defineConfig({
	testDir: "./tests",
	timeout: 60_000,
	retries: 0,
	// Several tests (hot-reload, style-hot-reload, cast-spell) mutate
	// shared content files — e.g. activity_log_panel_style.tres — so
	// parallel execution creates races. Run serially.
	workers: 1,
	fullyParallel: false,
	use: {
		baseURL: "http://localhost:7601",
		screenshot: "only-on-failure",
		trace: "retain-on-failure",
	},
	projects: [
		{
			name: "chromium",
			use: {
				browserName: "chromium",
				// Keep the tab from throttling its RAF/timers when it loses
				// foreground focus — Godot's main loop depends on RAF and
				// tests that send keyboard input across >2s time spans (combat
				// menu navigation) see the engine freeze otherwise.
				launchOptions: {
					args: [
						"--disable-background-timer-throttling",
						"--disable-backgrounding-occluded-windows",
						"--disable-renderer-backgrounding",
					],
				},
			},
		},
	],
	outputDir: "../../../../build/_artifacts/latest/screenshots",
	webServer: [
		{
			command: "node src/index.js",
			cwd: "../game-server",
			port: 7600,
			reuseExistingServer: true,
			timeout: 10_000,
		},
		{
			command:
				"node ../../../../scripts/serve_web.js ../../../../build/_artifacts/latest/web",
			port: 7601,
			reuseExistingServer: true,
			timeout: 10_000,
		},
	],
});
