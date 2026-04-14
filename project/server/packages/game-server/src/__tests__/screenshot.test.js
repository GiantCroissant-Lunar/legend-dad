import { beforeEach, describe, expect, it, vi } from "vitest";
import { createScreenshotTool } from "../mastra/tools/screenshot.js";

function makeMockConnMgr() {
	return {
		sendCommandToGodot: vi.fn().mockResolvedValue({
			success: true,
			error: null,
			screenshot: "data:image/jpeg;base64,/9j/fake",
		}),
	};
}

describe("screenshot tool", () => {
	let connMgr;

	beforeEach(() => {
		connMgr = makeMockConnMgr();
	});

	it("sends screenshot command with defaults", async () => {
		const tool = createScreenshotTool(connMgr);
		const result = await tool.execute({});
		expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("screenshot", {
			viewport: "active",
			format: "jpeg",
			quality: 80,
			max_width: 0,
		});
		expect(result.success).toBe(true);
		expect(result.screenshot).toContain("data:image/jpeg;base64,");
	});

	it("passes viewport and format options through", async () => {
		const tool = createScreenshotTool(connMgr);
		await tool.execute({ viewport: "both", format: "png", max_width: 256 });
		expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("screenshot", {
			viewport: "both",
			format: "png",
			quality: 80,
			max_width: 256,
		});
	});
});
