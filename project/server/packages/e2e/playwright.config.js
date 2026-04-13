import { defineConfig } from "@playwright/test";

export default defineConfig({
	testDir: "./tests",
	timeout: 60_000,
	retries: 0,
	use: {
		baseURL: "http://localhost:8080",
		screenshot: "only-on-failure",
		trace: "retain-on-failure",
	},
	projects: [
		{
			name: "chromium",
			use: { browserName: "chromium" },
		},
	],
	outputDir: "../../../../build/_artifacts/latest/screenshots",
	webServer: [
		{
			command: "node src/index.js",
			cwd: "../game-server",
			port: 3000,
			reuseExistingServer: true,
			timeout: 10_000,
		},
		{
			command:
				"node ../../../../scripts/serve_web.js ../../../../build/_artifacts/latest/web",
			port: 8080,
			reuseExistingServer: true,
			timeout: 10_000,
		},
	],
});
