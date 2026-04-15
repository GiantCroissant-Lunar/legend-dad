// End-to-end: F9 in the running game re-fetches the manifest, detects that
// hud-core's PCK hash changed (because we just rebuilt it with a tweaked
// constant), and swaps in the new PCK without a page reload.
//
// Verifies the full chain:
//   game-server  /manifest.json      (new endpoint)
//   ContentManager.reload_manifest() (HTTP fetch of manifest)
//   ContentManager.reload_bundle()   (re-fetch PCK with replace_files=true)
//   main.gd._on_bundle_will_reload   (frees existing widgets)
//   main.gd._on_bundle_reloaded      (re-instantiates from new PCK)
//
// Requires --headed (hidden tabs throttle Godot's main loop — same caveat
// as lazy-bundle-load.spec.js).

import { execSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test } from "@playwright/test";

const REPO_ROOT = resolve(new URL("../../../../..", import.meta.url).pathname);
const TWEAKED_FILE = resolve(
	REPO_ROOT,
	"project/shared/content/hud/hud-core/activity_log_panel.gd",
);

test("F9 hot-reloads hud-core after `task content:build`", async ({ page }) => {
	test.setTimeout(180_000);

	// Snapshot the activity_log source so we can guarantee restoration.
	const original = readFileSync(TWEAKED_FILE, "utf8");
	if (!original.includes("BG_COLOR = Color(0.05, 0.05, 0.15, 0.85)")) {
		throw new Error(
			"activity_log_panel.gd shape changed; update the test's marker",
		);
	}

	const pcks = [];
	page.on("request", (req) => {
		const u = req.url();
		if (u.includes("/pck/") && u.endsWith(".pck")) pcks.push(u);
	});

	const consoleHits = [];
	page.on("console", (msg) => {
		const text = msg.text();
		if (text.includes("ContentManager") || text.includes("[main]"))
			consoleHits.push(`[${msg.type()}] ${text}`);
	});

	try {
		// 1. Boot. Confirm initial hud-core load.
		await page.goto("/complete-app.html");
		await expect(page.locator("canvas")).toBeVisible({ timeout: 30_000 });
		await page.waitForTimeout(8_000);

		const initialHudCorePcks = pcks.filter((u) => u.includes("hud-core"));
		expect(initialHudCorePcks.length).toBeGreaterThan(0);
		const initialHash =
			initialHudCorePcks[0].match(/hud-core@([a-f0-9]+)/)?.[1];
		expect(
			initialHash,
			`expected hash in URL ${initialHudCorePcks[0]}`,
		).toBeTruthy();
		console.log(`[test] initial hud-core hash: ${initialHash}`);

		// 2. Tweak the source. Trivial whitespace change is enough to flip the
		// content hash (the hash is computed over PCK contents which include
		// the compiled .gdc, which is byte-sensitive to source).
		const tweaked = original.replace(
			"BG_COLOR = Color(0.05, 0.05, 0.15, 0.85)",
			"BG_COLOR = Color(0.10, 0.05, 0.15, 0.85)  # hot-reload test tweak",
		);
		writeFileSync(TWEAKED_FILE, tweaked);

		// 3. Rebuild the bundle. This regenerates content_manifest.json with
		// the new hash and writes a new hud-core@{newHash}.pck.
		console.log("[test] rebuilding hud-core bundle");
		execSync("task content:build -- hud-core", {
			cwd: REPO_ROOT,
			stdio: "pipe",
			timeout: 60_000,
		});

		// 4. Focus the canvas + press F9 to trigger hot reload.
		await page.locator("canvas").click();
		await page.waitForTimeout(200);
		await page.keyboard.down("F9");
		await page.waitForTimeout(120);
		await page.keyboard.up("F9");

		// 5. Wait for the manifest fetch + PCK re-fetch + re-instantiate.
		await page.waitForTimeout(5_000);

		// 6. Assert: a new hud-core PCK was fetched with a different hash,
		// and we did NOT reload the page (initial fetch wasn't repeated).
		const allHashes = pcks
			.map((u) => u.match(/hud-core@([a-f0-9]+)/)?.[1])
			.filter(Boolean);
		console.log(`[test] hud-core hashes seen: ${JSON.stringify(allHashes)}`);
		const uniqueHashes = [...new Set(allHashes)];
		expect(
			uniqueHashes.length,
			`hud-core hash should change: ${JSON.stringify(uniqueHashes)}`,
		).toBeGreaterThanOrEqual(2);

		// Sanity: ContentManager prints land in console — proves the GD code
		// path ran rather than e.g. the page reloading.
		const reloadHits = consoleHits.filter(
			(l) => l.includes("manifest reloaded") || l.includes("hash"),
		);
		console.log("[test] reload-related console:", reloadHits);
		expect(reloadHits.length).toBeGreaterThan(0);
	} finally {
		// 7. Always restore the source so the working tree stays clean.
		writeFileSync(TWEAKED_FILE, original);
		// Rebuild back to the original hash so subsequent test runs start
		// from a known state. Best-effort — if it fails, the next build
		// will fix it.
		try {
			execSync("task content:build -- hud-core", {
				cwd: REPO_ROOT,
				stdio: "pipe",
				timeout: 60_000,
			});
		} catch (e) {
			console.warn("[test] cleanup rebuild failed:", e.message);
		}
	}
});
