import { createTool } from "@mastra/core/tools";
import { z } from "zod";

export function createInteractTool(connMgr) {
	return createTool({
		id: "interact",
		description:
			"Interact with the object in front of the active player character. Returns the command acknowledgement from the game.",
		inputSchema: z.object({}),
		outputSchema: z.object({
			success: z.boolean(),
			error: z.string().nullable(),
		}),
		execute: async () => {
			const ack = await connMgr.sendCommandToGodot("interact");
			return { success: ack.success, error: ack.error ?? null };
		},
	});
}
