import { createTool } from "@mastra/core/tools";
import { z } from "zod";

export function createMoveTool(connMgr) {
	return createTool({
		id: "move",
		description:
			"Move the active player character one tile in the given direction. Returns the command acknowledgement from the game.",
		inputSchema: z.object({
			direction: z
				.enum(["up", "down", "left", "right"])
				.describe("Direction to move the active player"),
		}),
		outputSchema: z.object({
			success: z.boolean(),
			error: z.string().nullable(),
		}),
		execute: async (input) => {
			const ack = await connMgr.sendCommandToGodot("move", {
				direction: input.direction,
			});
			return { success: ack.success, error: ack.error ?? null };
		},
	});
}
