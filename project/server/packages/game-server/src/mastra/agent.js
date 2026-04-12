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
 * Default model providers. Rotated round-robin to avoid rate limits.
 * Override with AGENT_PROVIDERS env var (JSON array) or opts.providers.
 */
const DEFAULT_PROVIDERS = [
	{
		name: "zai",
		url: "https://api.z.ai/api/coding/paas/v4",
		apiKey: process.env.ZAI_API_KEY || "",
		model: process.env.ZAI_MODEL || "glm-5.1",
	},
	{
		name: "alibaba",
		url: "https://coding-intl.dashscope.aliyuncs.com/v1",
		apiKey: process.env.ALIBABA_API_KEY || "",
		model: process.env.ALIBABA_MODEL || "qwen3.5-plus",
	},
];

let _providerIndex = 0;

/**
 * Pick the next provider from the rotation.
 * Skips providers with empty API keys.
 * @param {Array} providers
 * @returns {object} { name, url, apiKey, model }
 */
export function nextProvider(providers = DEFAULT_PROVIDERS) {
	const available = providers.filter((p) => p.apiKey);
	if (available.length === 0) {
		throw new Error(
			"no model providers configured — set ZAI_API_KEY or ALIBABA_API_KEY",
		);
	}
	const provider = available[_providerIndex % available.length];
	_providerIndex++;
	console.log(`[agent] using provider: ${provider.name} (${provider.model})`);
	return provider;
}

/**
 * Create a game-playing agent bound to the Mastra tools.
 * Async — builds replay context and rotates model providers.
 *
 * @param {object} tools — { moveTool, interactTool, switchEraTool, getStateTool }
 * @param {object} opts — { providers, contextBuilder, stateStore }
 */
export async function createGameAgent(tools, opts = {}) {
	const providers = opts.providers || DEFAULT_PROVIDERS;
	const provider = nextProvider(providers);

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
			id: `custom/${provider.model}`,
			url: provider.url,
			apiKey: provider.apiKey,
		},
		tools: {
			move: tools.moveTool,
			interact: tools.interactTool,
			switch_era: tools.switchEraTool,
			get_state: tools.getStateTool,
		},
	});
}
