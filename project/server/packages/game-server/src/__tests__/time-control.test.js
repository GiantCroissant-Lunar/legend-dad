import { beforeEach, describe, expect, it, vi } from "vitest";
import {
	createPauseTimeTool,
	createResumeTimeTool,
	createSetTimeSpeedTool,
	createStepFrameTool,
} from "../mastra/tools/time-control.js";

function makeMockConnMgr() {
	return {
		sendCommandToGodot: vi
			.fn()
			.mockResolvedValue({ success: true, error: null }),
	};
}

describe("time-control tools", () => {
	let connMgr;

	beforeEach(() => {
		connMgr = makeMockConnMgr();
	});

	it("set_time_speed sends time_set_speed command", async () => {
		const tool = createSetTimeSpeedTool(connMgr);
		const result = await tool.execute({ speed: 0.5 });
		expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("time_set_speed", {
			speed: 0.5,
		});
		expect(result.success).toBe(true);
	});

	it("pause_time sends time_pause command", async () => {
		const tool = createPauseTimeTool(connMgr);
		const result = await tool.execute({});
		expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("time_pause", {});
		expect(result.success).toBe(true);
	});

	it("resume_time sends time_resume command", async () => {
		const tool = createResumeTimeTool(connMgr);
		const result = await tool.execute({});
		expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("time_resume", {});
		expect(result.success).toBe(true);
	});

	it("step_frame sends time_step command", async () => {
		const tool = createStepFrameTool(connMgr);
		const result = await tool.execute({});
		expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("time_step", {});
		expect(result.success).toBe(true);
	});
});
