import { createTool } from "@mastra/core/tools";
import { z } from "zod";

export function createGetStateTool(stateStore) {
	return createTool({
		id: "get_state",
		description:
			"Get the current full game state snapshot including all entity positions, interactable states, map data, and battle state.",
		inputSchema: z.object({}),
		outputSchema: z.object({
			state: z.any().nullable(),
			error: z.string().nullable(),
		}),
		execute: async () => {
			const state = stateStore.getState();
			if (state === null) {
				return {
					state: null,
					error: "no game state available — Godot may not be connected",
				};
			}
			return { state, error: null };
		},
	});
}
