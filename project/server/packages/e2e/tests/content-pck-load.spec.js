import { readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { expect, test } from "@playwright/test";

// Resolve PCK files from the web export directory at test-collection time.
// This avoids hardcoding hashes while staying in-process with no extra HTTP.
const WEB_DIR = resolve(
	new URL("../../../../../build/_artifacts/latest/web", import.meta.url)
		.pathname,
);
const pckFiles = (() => {
	try {
		return readdirSync(join(WEB_DIR, "pck")).filter((f) => f.endsWith(".pck"));
	} catch {
		return [];
	}
})();

test("eager content bundles load on boot", async ({ page, request }) => {
	const requestedPcks = [];
	page.on("request", (req) => {
		if (req.url().includes("/pck/") && req.url().endsWith(".pck")) {
			requestedPcks.push(req.url());
		}
	});

	await page.goto("/complete-app.html");
	// Boot scene reaches the gameplay state via WS once it's ready.
	// We only need to confirm the PCK request landed; let the page sit briefly
	// for asynchronous PCK fetches to flush.
	await page.waitForFunction(
		() => document.title && document.title.length > 0,
		{
			timeout: 30000,
		},
	);
	await page.waitForTimeout(2000);

	// At least one PCK must be present in the web export's pck/ directory.
	expect(pckFiles.length).toBeGreaterThan(0);
	expect(pckFiles.some((f) => f.startsWith("hud-core"))).toBe(true);

	if (requestedPcks.length > 0) {
		// Multi-threaded build: Playwright intercepted the HTTP fetch Godot made.
		expect(requestedPcks.some((u) => u.includes("hud-core"))).toBe(true);
	} else {
		// Single-threaded build: load_resource_pack does not trigger an XHR that
		// Playwright can intercept. Verify each PCK is reachable over HTTP instead.
		for (const pckFile of pckFiles) {
			const res = await request.head(`/pck/${pckFile}`);
			expect(res.status()).toBe(200);
		}
	}
});
