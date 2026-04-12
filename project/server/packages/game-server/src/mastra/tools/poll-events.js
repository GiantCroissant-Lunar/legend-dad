// project/server/packages/game-server/src/mastra/tools/poll-events.js
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

/**
 * Create a poll_events tool bound to an EventQueueRegistry.
 * MCP clients call this to drain buffered game events.
 *
 * NOTE: Mastra's startHTTP does not expose the MCP session ID to tool
 * execute functions. We use a single shared queue that broadcasts to
 * all MCP sessions via the registry. For poll_events, we use a
 * dedicated per-tool-invocation approach: the registry broadcasts to
 * all queues, and each MCP client drains its own queue.
 *
 * Since Claude Code is typically the only MCP client, we use a
 * default session key. If multi-session support is needed later,
 * the sessionId can be passed as an input parameter.
 *
 * @param {import('../mcp/event-queue.js').EventQueueRegistry} registry
 */
export function createPollEventsTool(registry) {
	return createTool({
		id: "poll_events",
		description:
			"Drain all game events buffered since your last poll. Returns state_event and state_snapshot messages from Godot. Call this between actions to see what changed in the game world (entity moves, era switches, battle starts, interactions).",
		inputSchema: z.object({
			sessionId: z
				.string()
				.optional()
				.describe("MCP session ID. Omit to use the default session."),
		}),
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
		execute: async (input) => {
			// Try provided sessionId, fall back to first available queue
			let queue = null;
			if (input.sessionId) {
				queue = registry.get(input.sessionId);
			}
			if (!queue) {
				// Fall back: get the first session's queue (single-client case)
				for (const [id] of registry._sessions) {
					queue = registry.get(id);
					break;
				}
			}
			if (!queue) {
				return { events: [], count: 0 };
			}
			const events = queue.drain();
			return { events, count: events.length };
		},
	});
}
