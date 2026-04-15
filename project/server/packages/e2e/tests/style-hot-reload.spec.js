// End-to-end: F9 picks up fresh `.tres` style values.
//
// Tunables in HUD widgets live in `<widget>_style.tres` (not script consts)
// so they hot-reload on web — see the vault dev-log dated 2026-04-15 for
// why script consts can't hot-reload under a web export (compiled .gdc
// has no source to re-parse; no `GDScript.reload` works).
//
// This test proves the end-to-end iteration loop:
//   edit style.tres -> task content:build -> F9 -> new value visible.
//
// Verification is via the `[style-alp] bg_color=...` print the widget
// emits from `_ready`. After F9 the widget is re-instantiated and prints
// the fresh value. No pixel-diff needed.

import { execSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test } from "@playwright/test";

const REPO_ROOT = resolve(new URL("../../../../..", import.meta.url).pathname);
const STYLE_FILE = resolve(
	REPO_ROOT,
	"project/shared/content/hud/hud-core/activity_log_panel_style.tres",
);

test("F9 picks up fresh bg_color from activity_log_panel_style.tres", async ({
	page,
}) => {
	test.setTimeout(180_000);

	const original = readFileSync(STYLE_FILE, "utf8");
	if (!original.includes("bg_color = Color(0.05, 0.05, 0.15, 0.85)")) {
		throw new Error(
			"activity_log_panel_style.tres baseline shape changed; update this test's marker",
		);
	}

	const stylePrints = [];
	page.on("console", (msg) => {
		const text = msg.text();
		if (text.startsWith("[style-alp]")) stylePrints.push(text);
	});

	try {
		// 1. Boot. Widget _ready fires once with baseline bg_color.
		await page.goto("/complete-app.html");
		await expect(page.locator("canvas")).toBeVisible({ timeout: 30_000 });
		await page.waitForTimeout(10_000);

		const bootPrints = [...stylePrints];
		console.log("[test] boot style prints:", bootPrints);
		expect(
			bootPrints.length,
			"widget should print [style-alp] once on boot",
		).toBeGreaterThanOrEqual(1);
		const bootValue = bootPrints.at(-1);
		expect(
			bootValue,
			`boot value should reflect baseline: ${bootValue}`,
		).toContain("(0.05, 0.05, 0.15, 0.85)");

		// 2. Tweak just the bg_color field in the style .tres. Leave other
		// fields + the ExtResource reference untouched.
		const tweaked = original.replace(
			"bg_color = Color(0.05, 0.05, 0.15, 0.85)",
			"bg_color = Color(0.45, 0.05, 0.15, 0.85)",
		);
		writeFileSync(STYLE_FILE, tweaked);

		// 3. Rebuild the bundle (regenerates hash, writes new PCK, updates
		// project/shared/data/content_manifest.json).
		execSync("task content:build -- hud-core", {
			cwd: REPO_ROOT,
			stdio: "pipe",
			timeout: 60_000,
		});

		// 4. F9.
		await page.locator("canvas").click();
		await page.waitForTimeout(200);
		await page.keyboard.down("F9");
		await page.waitForTimeout(120);
		await page.keyboard.up("F9");
		await page.waitForTimeout(5_000);

		// 5. Assert a NEW [style-alp] print appeared with the tweaked value.
		const newPrints = stylePrints.slice(bootPrints.length);
		console.log("[test] post-F9 style prints:", newPrints);
		expect(
			newPrints.length,
			"widget should print [style-alp] again after F9 re-instantiation",
		).toBeGreaterThanOrEqual(1);
		const f9Value = newPrints.at(-1);
		expect(f9Value, `post-F9 value should reflect tweak: ${f9Value}`).toContain(
			"(0.45, 0.05, 0.15, 0.85)",
		);

		// 6. Visual spot-check: screenshot for manual inspection / diff baseline.
		// The activity log's bottom-left background should now have a red tint.
		await page.screenshot({
			path: resolve(
				REPO_ROOT,
				"build/_artifacts/latest/screenshots/style-hot-reload-after.png",
			),
		});
	} finally {
		writeFileSync(STYLE_FILE, original);
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
