import { createTool } from "@mastra/core/tools";
import { z } from "zod";

export function createSwitchEraTool(connMgr) {
	return createTool({
		id: "switch_era",
		description:
			"Switch the active player between Father and Son timelines. Returns the command acknowledgement from the game.",
		inputSchema: z.object({}),
		outputSchema: z.object({
			success: z.boolean(),
			error: z.string().nullable(),
		}),
		execute: async () => {
			const ack = await connMgr.sendCommandToGodot("switch_era");
			return { success: ack.success, error: ack.error ?? null };
		},
	});
}
