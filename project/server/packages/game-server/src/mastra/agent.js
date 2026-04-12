// project/server/packages/game-server/src/mastra/agent.js
import { Agent } from "@mastra/core/agent";

const BASE_INSTRUCTIONS = `You are an AI agent playing the game "Legend Dad". You control a character on a 10x8 tile grid.

## Game World
- Two timelines: FATHER (present) and SON (future/ruined)
- You control one character at a time (Father or Son)
- Movement is grid-based: up, down, left, right (one tile per move)
- You can interact with objects in front of you (boulders, switches)
- You can switch between Father and Son timelines

## Available Actions
- move(direction) — Move one tile. direction: "up", "down", "left", "right"
- interact() — Interact with the object in the tile you're facing
- switch_era() — Toggle between Father and Son
- get_state() — Get the full game state snapshot

## Tile Types
- 0 = grass/dead_grass (walkable)
- 1 = path (walkable)
- 2 = building/ruin (not walkable)
- 3 = water/blocked (not walkable)

## Strategy
1. Always call get_state() first to understand your position and surroundings
2. Plan your movement path considering walkable tiles
3. Interact with objects when you're adjacent and facing them
4. Use switch_era when you need to affect the other timeline

When asked to explore or play, start by getting the state, then move around the map systematically.`;

/**
 * Create a game-playing agent bound to the Mastra tools.
 * Now async — builds replay context before creating the agent.
 *
 * @param {object} tools — { moveTool, interactTool, switchEraTool, getStateTool }
 * @param {object} opts — { modelUrl, apiKey, modelId, contextBuilder, stateStore }
 */
export async function createGameAgent(tools, opts = {}) {
	const modelUrl =
		opts.modelUrl ||
		process.env.ZAI_BASE_URL ||
		"https://api.z.ai/api/coding/paas/v4";
	const apiKey = opts.apiKey || process.env.ZAI_API_KEY || "";
	const modelId = opts.modelId || process.env.ZAI_MODEL || "glm-5.1";

	// Build replay context if context builder is available
	let replayContext = "";
	if (opts.contextBuilder && opts.stateStore) {
		const currentState = opts.stateStore.getState();
		replayContext = await opts.contextBuilder.buildContext(currentState);
		if (replayContext) {
			console.log(
				"[agent] injected replay context (%d chars)",
				replayContext.length,
			);
		}
	}

	const instructions = replayContext
		? `${BASE_INSTRUCTIONS}\n${replayContext}`
		: BASE_INSTRUCTIONS;

	return new Agent({
		id: "legend-dad-player",
		name: "Legend Dad Player Agent",
		instructions,
		model: {
			id: `custom/${modelId}`,
			url: modelUrl,
			apiKey: apiKey,
		},
		tools: {
			move: tools.moveTool,
			interact: tools.interactTool,
			switch_era: tools.switchEraTool,
			get_state: tools.getStateTool,
		},
	});
}
