import { createServer } from "node:http";
import { WebSocketServer } from "ws";
import { createMastraServer } from "../../mastra/index.js";
import { EventQueueRegistry } from "../../mcp/event-queue.js";
import { GameStateStore } from "../../state/store.js";
import { ConnectionManager } from "../../ws/connection.js";

/**
 * Boot an isolated game server on a random available port.
 * Returns everything needed for testing + a cleanup function.
 *
 * @returns {Promise<{
 *   port: number,
 *   baseUrl: string,
 *   mcpUrl: string,
 *   stateStore: GameStateStore,
 *   connMgr: ConnectionManager,
 *   eventRegistry: EventQueueRegistry,
 *   cleanup: () => Promise<void>,
 * }>}
 */
export async function startTestServer() {
	const stateStore = new GameStateStore();
	const connMgr = new ConnectionManager(stateStore);
	const eventRegistry = new EventQueueRegistry();
	eventRegistry.create("default");

	connMgr.onEvent((direction, msg) => {
		if (
			direction === "from_godot" &&
			(msg.type === "state_event" || msg.type === "state_snapshot")
		) {
			eventRegistry.broadcast(msg);
		}
	});

	const { mcpServer } = createMastraServer(connMgr, stateStore, eventRegistry);

	const httpServer = createServer(async (req, res) => {
		const url = new URL(req.url || "", "http://localhost");
		if (url.pathname === "/mcp") {
			await mcpServer.startHTTP({ url, httpPath: "/mcp", req, res });
			return;
		}
		res.writeHead(200, { "Content-Type": "application/json" });
		res.end(JSON.stringify({ status: "ok" }));
	});

	const wss = new WebSocketServer({ server: httpServer });
	wss.on("connection", (ws) => connMgr.handleConnection(ws));

	// Listen on port 0 = random available port
	await new Promise((resolve) => httpServer.listen(0, resolve));
	const port = httpServer.address().port;

	const cleanup = () =>
		new Promise((resolve) => {
			eventRegistry.dispose();
			wss.close();
			httpServer.close(resolve);
		});

	return {
		port,
		baseUrl: `http://localhost:${port}`,
		mcpUrl: `http://localhost:${port}/mcp`,
		stateStore,
		connMgr,
		eventRegistry,
		cleanup,
	};
}
