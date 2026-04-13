import { expect, test } from "@playwright/test";

test.describe("Godot web build smoke test", () => {
	test("page loads and Godot canvas renders", async ({ page }) => {
		await page.goto("/");

		// Godot creates a <canvas> element for rendering
		const canvas = page.locator("canvas");
		await expect(canvas).toBeVisible({ timeout: 30_000 });

		// Verify the canvas has non-zero dimensions (WASM loaded and rendering)
		const box = await canvas.boundingBox();
		expect(box.width).toBeGreaterThan(0);
		expect(box.height).toBeGreaterThan(0);
	});

	test("WebSocket connection is established", async ({ page }) => {
		// Listen for WebSocket connections
		const wsPromise = page.waitForEvent("websocket", {
			timeout: 30_000,
		});

		await page.goto("/");

		const ws = await wsPromise;
		expect(ws.url()).toContain("localhost:3000");

		// Wait for handshake to complete
		const framePromise = ws.waitForEvent("framesent", {
			predicate: (frame) => {
				try {
					const data = JSON.parse(frame.payload);
					return data.type === "handshake";
				} catch {
					return false;
				}
			},
			timeout: 10_000,
		});

		await framePromise;
	});
});
