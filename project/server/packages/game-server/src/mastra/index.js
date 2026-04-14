// project/server/packages/game-server/src/mastra/index.js
import { MCPServer } from "@mastra/mcp";
import { createGetStateTool } from "./tools/get-state.js";
import { createInteractTool } from "./tools/interact.js";
import { createMoveTool } from "./tools/move.js";
import { createPollEventsTool } from "./tools/poll-events.js";
import { createScreenshotTool } from "./tools/screenshot.js";
import { createSwitchEraTool } from "./tools/switch-era.js";
import {
	createPauseTimeTool,
	createResumeTimeTool,
	createSetTimeSpeedTool,
	createStepFrameTool,
} from "./tools/time-control.js";

/**
 * Initialize Mastra tools and MCP server, bound to live connection/state instances.
 *
 * @param {import('../ws/connection.js').ConnectionManager} connMgr
 * @param {import('../state/store.js').GameStateStore} stateStore
 * @param {import('../mcp/event-queue.js').EventQueueRegistry} [eventRegistry]
 */
export function createMastraServer(connMgr, stateStore, eventRegistry) {
	const moveTool = createMoveTool(connMgr);
	const interactTool = createInteractTool(connMgr);
	const switchEraTool = createSwitchEraTool(connMgr);
	const getStateTool = createGetStateTool(stateStore);
	const setTimeSpeedTool = createSetTimeSpeedTool(connMgr);
	const pauseTimeTool = createPauseTimeTool(connMgr);
	const resumeTimeTool = createResumeTimeTool(connMgr);
	const stepFrameTool = createStepFrameTool(connMgr);
	const screenshotTool = createScreenshotTool(connMgr);

	const tools = {
		move: moveTool,
		interact: interactTool,
		switch_era: switchEraTool,
		get_state: getStateTool,
		set_time_speed: setTimeSpeedTool,
		pause_time: pauseTimeTool,
		resume_time: resumeTimeTool,
		step_frame: stepFrameTool,
		screenshot: screenshotTool,
	};

	// Add poll_events only when an event registry is provided (MCP mode)
	if (eventRegistry) {
		tools.poll_events = createPollEventsTool(eventRegistry);
	}

	const mcpServer = new MCPServer({
		id: "legend-dad-game",
		name: "Legend Dad Game Server",
		version: "0.1.0",
		description:
			"Control the Legend Dad game — move characters, interact with objects, switch timelines, and observe game state.",
		tools,
	});

	return {
		mcpServer,
		tools: { moveTool, interactTool, switchEraTool, getStateTool },
	};
}
