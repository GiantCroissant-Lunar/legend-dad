import { createTool } from "@mastra/core/tools";
import { z } from "zod";

export function createScreenshotTool(connMgr) {
	return createTool({
		id: "screenshot",
		description:
			"Capture a screenshot of the game SubViewport. Use with pause_time/step_frame for precise before/after comparison. Returns base64-encoded image data.",
		inputSchema: z.object({
			viewport: z
				.enum(["active", "father", "son", "both"])
				.default("active")
				.describe("Which viewport to capture"),
			format: z.enum(["png", "jpeg"]).default("jpeg").describe("Image format"),
			quality: z
				.number()
				.min(1)
				.max(100)
				.default(80)
				.describe("JPEG quality (1-100)"),
			max_width: z
				.number()
				.min(0)
				.default(0)
				.describe("Max width in pixels (0 = no resize)"),
		}),
		outputSchema: z.object({
			success: z.boolean(),
			error: z.string().nullable(),
			screenshot: z.string().optional(),
			father_screenshot: z.string().optional(),
			son_screenshot: z.string().optional(),
		}),
		execute: async (input) => {
			const ack = await connMgr.sendCommandToGodot("screenshot", {
				viewport: input.viewport ?? "active",
				format: input.format ?? "jpeg",
				quality: input.quality ?? 80,
				max_width: input.max_width ?? 0,
			});
			return {
				success: ack.success,
				error: ack.error ?? null,
				screenshot: ack.screenshot ?? undefined,
				father_screenshot: ack.father_screenshot ?? undefined,
				son_screenshot: ack.son_screenshot ?? undefined,
			};
		},
	});
}
