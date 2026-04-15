// End-to-end: spells-core bundle loads and combat menu offers "Spell"
// for casters.
//
// This asserts the integration wiring: bundle → ContentManager →
// Combatant.known_spells → BattleManager menu construction. The cast
// resolution math (MP deducted, HP changed, damage/heal clamping) is
// covered by `tests/test_battle_manager_cast.gd` in the Godot project.
//
// We don't drive the menu keyboard-first from Playwright because Chrome
// throttles the tab's RAF / keyboard event delivery after a few hundred
// ms of lost focus. Even direct `dispatchEvent` calls through
// page.evaluate only land the first keystroke reliably. The BattleManager
// input refactor to `_input` fixes responsiveness for real players but
// can't unstick the browser throttling — that's a Playwright harness
// problem, not a game problem.

import { expect, test } from "@playwright/test";

test("spells-core loads eagerly and caster menu offers Spell", async ({
	page,
}) => {
	test.setTimeout(60_000);

	const logs = [];
	page.on("console", (msg) => {
		const text = msg.text();
		if (
			text.includes("[ContentManager]") ||
			text.includes("[battle-menu]") ||
			text.includes("[battle]")
		) {
			logs.push(text);
		}
	});

	await page.goto("/complete-app.html");
	await expect(page.locator("canvas")).toBeVisible({ timeout: 30_000 });
	await page.waitForTimeout(10_000);

	// Drive Father onto the slime at (4, 4) and press E to interact.
	await page.locator("canvas").click();
	async function tap(key, holdMs = 120) {
		await page.keyboard.down(key);
		await page.waitForTimeout(holdMs);
		await page.keyboard.up(key);
		await page.waitForTimeout(200);
	}
	for (const key of [
		"ArrowRight",
		"ArrowRight",
		"ArrowDown",
		"ArrowDown",
		"e",
	]) {
		await tap(key);
	}
	await page.waitForTimeout(3_000); // intro message timer + margin

	// Assertion 1: spells-core loaded at boot (eager).
	expect(
		logs.some((l) => l.includes("spells-core@")),
		"spells-core@{hash}.pck must load eagerly at boot",
	).toBe(true);

	// Assertion 2: combat intro fired.
	expect(
		logs.some((l) => l.includes("Slime appeared!")),
		"combat intro must fire once the player interacts with the slime",
	).toBe(true);

	// Assertion 3: Father's command menu opened with "Spell" present.
	// Only happens when Combatant.known_spells was populated correctly
	// from BattleData.FATHER_STATS["spells"] via Combatant.from_dict.
	const menuLine = logs.find(
		(l) => l.includes("[battle-menu]") && l.includes("Father"),
	);
	expect(
		menuLine,
		`Father's command menu must have opened. Logs:\n${logs.join("\n")}`,
	).toBeTruthy();
	expect(
		menuLine,
		`Father's menu must include "Spell". Got: ${menuLine}`,
	).toContain("Spell");
});
