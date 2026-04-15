// End-to-end: spells-core bundle loads and combat menu offers "Spell"
// for casters.
//
// This asserts the integration wiring: bundle → ContentManager →
// Combatant.known_spells → BattleManager menu construction. The cast
// resolution math (MP deducted, HP changed, damage/heal clamping) is
// covered by `tests/test_battle_manager_cast.gd` in the Godot project —
// Playwright can't reliably drive the battle menu itself because Chrome
// throttles the tab's RAF after ~2s of lost focus, which freezes the
// Godot main loop that the polling-based input handlers depend on.

import { expect, test } from "@playwright/test";

test("spells-core loads eagerly and caster menu offers Spell", async ({
	page,
}) => {
	test.setTimeout(60_000);

	const logs = [];
	page.on("console", (msg) => {
		const text = msg.text();
		if (text.includes("[ContentManager]") || text.includes("[battle-menu]")) {
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
	// Intro message timer ≈ 1.2s; give plenty of headroom for the command
	// menu to open. (We only need the _show_menu_for_current_member print
	// to land — no keyboard navigation needed.)
	await page.waitForTimeout(4_000);

	// Assertion 1: spells-core PCK was fetched eagerly at boot.
	// `fetching /pck/spells-core@...` happens on request; `fetched
	// spells-core@... in N ms` confirms completion. Either line proves
	// the bundle was pulled.
	const spellsLoaded = logs.some((l) => l.includes("spells-core@"));
	expect(
		spellsLoaded,
		"spells-core@{hash}.pck must be fetched during boot (eager bundle)",
	).toBe(true);

	// Assertion 2: when the command menu opened for Father, the options
	// included "Spell" — which only happens when Combatant.known_spells
	// is non-empty AND was populated from BattleData.FATHER_STATS.
	const menuLine = logs.find(
		(l) => l.includes("[battle-menu]") && l.includes("Father"),
	);
	expect(
		menuLine,
		`expected a [battle-menu] Father line — got logs: ${JSON.stringify(logs)}`,
	).toBeTruthy();
	expect(
		menuLine,
		`Father's menu must contain "Spell" — got: ${menuLine}`,
	).toContain("Spell");
});
