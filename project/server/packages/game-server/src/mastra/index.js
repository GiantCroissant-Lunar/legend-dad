import { MCPServer } from "@mastra/mcp";
import { createGetStateTool } from "./tools/get-state.js";
import { createInteractTool } from "./tools/interact.js";
import { createMoveTool } from "./tools/move.js";
import { createSwitchEraTool } from "./tools/switch-era.js";

/**
 * Initialize Mastra tools and MCP server, bound to live connection/state instances.
 *
 * @param {import('../ws/connection.js').ConnectionManager} connMgr
 * @param {import('../state/store.js').GameStateStore} stateStore
 */
export function createMastraServer(connMgr, stateStore) {
	const moveTool = createMoveTool(connMgr);
	const interactTool = createInteractTool(connMgr);
	const switchEraTool = createSwitchEraTool(connMgr);
	const getStateTool = createGetStateTool(stateStore);

	const mcpServer = new MCPServer({
		id: "legend-dad-game",
		name: "Legend Dad Game Server",
		version: "0.1.0",
		description:
			"Control the Legend Dad game — move characters, interact with objects, switch timelines, and observe game state.",
		tools: {
			move: moveTool,
			interact: interactTool,
			switch_era: switchEraTool,
			get_state: getStateTool,
		},
	});

	return {
		mcpServer,
		tools: { moveTool, interactTool, switchEraTool, getStateTool },
	};
}
