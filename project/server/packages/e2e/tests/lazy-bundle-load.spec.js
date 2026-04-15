// End-to-end verification for the content-runtime split's two trickiest seams:
//   1. hud-battle (lazy bundle) is NOT fetched at boot, but IS fetched the
//      first time the player enters combat. (Item #1 from the post-merge
//      handover doc.)
//   2. The whispering-woods location PCK loads its palette textures without
//      "could not resolve" errors (the .ctex-outside-PCK bug fixed by baking
//      palettes as embedded ImageTexture .tres resources). (Item #2.)
//
// Tab visibility throttling — running headed only — is required: hidden
// Chrome tabs throttle requestAnimationFrame, which makes Godot's HTTPRequest
// take 50+ seconds to deliver request_completed. See item #3 in the handover.

import { expect, test } from "@playwright/test";

const MCP_URL = "http://localhost:7600/mcp";
const MCP_HEADERS = {
	"Content-Type": "application/json",
	Accept: "application/json, text/event-stream",
};

function parseSSE(body) {
	for (const line of body.split("\n")) {
		if (line.startsWith("data: ")) return JSON.parse(line.slice(6));
	}
	return JSON.parse(body);
}

async function mcpInit(request) {
	const res = await request.post(MCP_URL, {
		headers: MCP_HEADERS,
		data: {
			jsonrpc: "2.0",
			id: 1,
			method: "initialize",
			params: {
				protocolVersion: "2025-03-26",
				capabilities: {},
				clientInfo: { name: "lazy-bundle-test", version: "0.1.0" },
			},
		},
	});
	const sessionId = res.headers()["mcp-session-id"];
	await request.post(MCP_URL, {
		headers: { ...MCP_HEADERS, "mcp-session-id": sessionId },
		data: { jsonrpc: "2.0", method: "notifications/initialized" },
	});
	return sessionId;
}

async function mcpCall(request, sessionId, name, args = {}, id = 100) {
	const res = await request.post(MCP_URL, {
		headers: { ...MCP_HEADERS, "mcp-session-id": sessionId },
		data: {
			jsonrpc: "2.0",
			id,
			method: "tools/call",
			params: { name, arguments: args },
		},
	});
	const body = parseSSE(await res.text());
	if (body.error) throw new Error(`${name}: ${JSON.stringify(body.error)}`);
	return JSON.parse(body.result.content[0].text);
}

test.describe.configure({ mode: "serial" });

test("hud-battle bundle is lazy + palette textures load cleanly", async ({
	page,
	request,
}) => {
	test.setTimeout(120_000);

	// Track every PCK request the page makes.
	const pcks = [];
	page.on("request", (req) => {
		const u = req.url();
		if (u.includes("/pck/") && u.endsWith(".pck")) pcks.push(u);
	});

	// Track Godot console errors. We expect ZERO palette/load errors.
	const consoleErrors = [];
	const allLogs = [];
	page.on("console", (msg) => {
		const text = msg.text();
		allLogs.push(`[${msg.type()}] ${text}`);
		// Surface ContentManager and main.gd diagnostics for debugging.
		if (text.includes("ContentManager") || text.includes("[main]")) {
			console.log(`>> [${msg.type()}] ${text}`);
		}
		if (
			text.includes("ERROR") ||
			text.includes("palette") ||
			text.includes("CompressedTexture") ||
			(text.includes("LocationManager") && text.includes("fail"))
		) {
			consoleErrors.push(`[${msg.type()}] ${text}`);
		}
	});

	await page.goto("/complete-app.html");
	const canvas = page.locator("canvas");
	await expect(canvas).toBeVisible({ timeout: 30_000 });

	// Wait for boot to fully complete (eager bundles loaded, main scene up,
	// WS handshake done). The boot.gd `[boot] Ready` print is observable but
	// console message order is brittle — give wall-clock headroom instead.
	await page.waitForTimeout(8_000);

	// Phase 1: At boot, hud-core (eager) must have loaded; hud-battle (lazy)
	// must NOT have loaded.
	expect(
		pcks.some((u) => u.includes("hud-core")),
		`expected hud-core PCK at boot, saw: ${JSON.stringify(pcks)}`,
	).toBe(true);
	expect(
		pcks.some((u) => u.includes("hud-battle")),
		`hud-battle should NOT load at boot, saw: ${JSON.stringify(pcks)}`,
	).toBe(false);

	// Phase 2: Drive the player into a slime via direct Playwright keyboard
	// input. We deliberately avoid MCP here — when the user has another
	// browser tab open with the game, *its* WS connection competes for
	// `connMgr.godotClient` slot on the game server (last-write-wins), so
	// MCP commands can land on the wrong instance. Direct keyboard input
	// stays inside Playwright's browser. The canvas needs a real click to
	// receive Godot's input events.
	await page.locator("canvas").click();
	await page.waitForTimeout(300);

	// Slime is at (4,4) FATHER, player spawns at (2,2). Hold each key for
	// 200ms so S_PlayerInput.process() (Input.is_action_pressed polled per
	// frame) actually sees it as pressed for at least one tick. A bare
	// `press` is too fast on the multi-threaded export and frequently
	// produces zero pressed-frames.
	async function tap(key) {
		await page.keyboard.down(key);
		await page.waitForTimeout(120);
		await page.keyboard.up(key);
		await page.waitForTimeout(280);
	}
	const path = ["ArrowRight", "ArrowDown", "ArrowDown", "ArrowRight"];
	for (const key of path) await tap(key);

	// Enter combat — E key = interact action. Generous window for the
	// lazy hud-battle fetch + load_resource_pack to complete (sub-second
	// once the tab is focused / RAF unthrottled).
	await tap("KeyE");
	await page.waitForTimeout(5_000);

	// Cropped screenshot of the top-left HUD region for visual sanity-check
	// (version stamp + Era/Pos line). Lands at:
	// build/_artifacts/latest/screenshots/lazy-bundle-load-final.png
	await page.screenshot({
		path: "../../../../build/_artifacts/latest/screenshots/lazy-bundle-load-final.png",
		clip: { x: 0, y: 0, width: 600, height: 200 },
	});

	// Dump tail of the Godot console — the [main] / ContentManager prints
	// only fire if signals routed correctly.
	console.log(`[test] Captured ${allLogs.length} console lines total`);
	const interesting = allLogs.filter(
		(l) =>
			l.includes("main]") ||
			l.includes("ContentManager") ||
			l.includes("encounter") ||
			l.includes("battle") ||
			l.includes("Battle"),
	);
	for (const l of interesting) console.log("  ::", l);

	// Phase 3: hud-battle PCK should now have been requested.
	expect(
		pcks.some((u) => u.includes("hud-battle")),
		`hud-battle should load after combat entry, saw: ${JSON.stringify(pcks)}`,
	).toBe(true);

	// Phase 4 (palette fix): No location/palette/CompressedTexture errors
	// should have surfaced during boot or during the location PCK load.
	expect(
		consoleErrors,
		`unexpected errors: ${consoleErrors.join("\n")}`,
	).toEqual([]);
});
