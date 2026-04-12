// project/server/packages/game-server/src/mastra/tools/poll-events.js
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

/**
 * Create a poll_events tool bound to an EventQueueRegistry.
 * MCP clients call this to drain buffered game events.
 *
 * NOTE: Mastra's startHTTP does not expose the MCP session ID to tool
 * execute functions. In the single-client case (Claude Code), we fall
 * back to the first available queue via registry.getFirstQueue().
 *
 * @param {import('../../mcp/event-queue.js').EventQueueRegistry} registry
 */
export function createPollEventsTool(registry) {
	return createTool({
		id: "poll_events",
		description:
			"Drain all game events buffered since your last poll. Returns state_event and state_snapshot messages from Godot. Call this between actions to see what changed in the game world (entity moves, era switches, battle starts, interactions).",
		inputSchema: z.object({}),
		outputSchema: z.object({
			events: z.array(
				z.object({
					type: z.string(),
					event: z.string().nullable(),
					data: z.any(),
					timestamp: z.string(),
				}),
			),
			count: z.number(),
		}),
		execute: async () => {
			const queue = registry.getFirstQueue();
			if (!queue) {
				return { events: [], count: 0 };
			}
			const events = queue.drain();
			return { events, count: events.length };
		},
	});
}
