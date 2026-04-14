import { mkdirSync } from "node:fs";
import { join } from "node:path";
import { createTool } from "@mastra/core/tools";
import { chromium } from "playwright";
import { z } from "zod";

export function createBrowserScreenshotTool() {
	return createTool({
		id: "browser_screenshot",
		description:
			"Capture a full-page screenshot of the game running in the browser via Playwright. Saves PNG to build/_artifacts/latest/screenshots/. Reuses existing Chromium if available.",
		inputSchema: z.object({
			filename: z
				.string()
				.default("")
				.describe(
					"Screenshot filename (without extension). Defaults to timestamp.",
				),
			game_url: z
				.string()
				.default("http://localhost:7601")
				.describe("URL of the running game"),
		}),
		outputSchema: z.object({
			success: z.boolean(),
			path: z.string().optional(),
			error: z.string().nullable(),
		}),
		execute: async (input) => {
			let browser;
			try {
				const filename = input.filename || `screenshot-${Date.now()}`;
				const screenshotDir = join(
					process.cwd(),
					"..",
					"..",
					"..",
					"build",
					"_artifacts",
					"latest",
					"screenshots",
				);
				mkdirSync(screenshotDir, { recursive: true });
				const screenshotPath = join(screenshotDir, `${filename}.png`);

				browser = await chromium.launch({ headless: true });
				const page = await browser.newPage();
				await page.goto(input.game_url || "http://localhost:7601", {
					waitUntil: "networkidle",
					timeout: 10000,
				});
				// Wait for game to render
				await page.waitForTimeout(2000);
				await page.screenshot({ path: screenshotPath, fullPage: true });

				return { success: true, path: screenshotPath, error: null };
			} catch (err) {
				return { success: false, error: err.message };
			} finally {
				if (browser) await browser.close();
			}
		},
	});
}
