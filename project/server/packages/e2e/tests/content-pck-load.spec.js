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

test("eager content bundles load on boot", async ({ page }) => {
	const requestedPcks = [];
	page.on("request", (req) => {
		if (req.url().includes("/pck/") && req.url().endsWith(".pck")) {
			requestedPcks.push(req.url());
		}
	});

	await page.goto("/complete-app.html");
	// Boot scene reaches the gameplay state via WS once it's ready.
	// We only need to confirm the PCK request landed; let the page sit briefly
	// for asynchronous PCK fetches to flush. ContentManager.load_bundle on web
	// uses HTTPRequest which can take 10+ seconds for the first signal under
	// the multi-threaded export — give the await chain plenty of headroom.
	await page.waitForFunction(
		() => document.title && document.title.length > 0,
		{
			timeout: 30000,
		},
	);
	await page.waitForTimeout(20000);

	// At least one PCK must be present in the web export's pck/ directory.
	expect(pckFiles.length).toBeGreaterThan(0);
	expect(pckFiles.some((f) => f.startsWith("hud-core"))).toBe(true);

	// ContentManager._load_pck_web fetches each eager PCK via HTTPRequest at
	// boot. Confirm Playwright observed the network call. Without this, F10
	// silently regresses to PCKs being baked into the main wasm at export time.
	expect(requestedPcks.length).toBeGreaterThan(0);
	expect(requestedPcks.some((u) => u.includes("hud-core"))).toBe(true);
});
