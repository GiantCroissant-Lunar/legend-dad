import { createTool } from "@mastra/core/tools";
import { z } from "zod";

const ackSchema = z.object({
	success: z.boolean(),
	error: z.string().nullable(),
});

export function createSetTimeSpeedTool(connMgr) {
	return createTool({
		id: "set_time_speed",
		description:
			"Set game time speed multiplier. 1.0 = normal, 0.25 = quarter speed, 2.0 = double speed. Clamped to 0.25–4.0.",
		inputSchema: z.object({
			speed: z.number().min(0.25).max(4.0).describe("Time speed multiplier"),
		}),
		outputSchema: ackSchema,
		execute: async (input) => {
			const ack = await connMgr.sendCommandToGodot("time_set_speed", {
				speed: input.speed,
			});
			return { success: ack.success, error: ack.error ?? null };
		},
	});
}

export function createPauseTimeTool(connMgr) {
	return createTool({
		id: "pause_time",
		description:
			"Pause the game. All game logic stops but WS connection stays active.",
		inputSchema: z.object({}),
		outputSchema: ackSchema,
		execute: async () => {
			const ack = await connMgr.sendCommandToGodot("time_pause", {});
			return { success: ack.success, error: ack.error ?? null };
		},
	});
}

export function createResumeTimeTool(connMgr) {
	return createTool({
		id: "resume_time",
		description:
			"Resume the game from paused state. Restores previous time speed.",
		inputSchema: z.object({}),
		outputSchema: ackSchema,
		execute: async () => {
			const ack = await connMgr.sendCommandToGodot("time_resume", {});
			return { success: ack.success, error: ack.error ?? null };
		},
	});
}

export function createStepFrameTool(connMgr) {
	return createTool({
		id: "step_frame",
		description:
			"Advance exactly one game frame while paused. Only works when game is paused. Useful for precise before/after screenshot comparison.",
		inputSchema: z.object({}),
		outputSchema: ackSchema,
		execute: async () => {
			const ack = await connMgr.sendCommandToGodot("time_step", {});
			return { success: ack.success, error: ack.error ?? null };
		},
	});
}
