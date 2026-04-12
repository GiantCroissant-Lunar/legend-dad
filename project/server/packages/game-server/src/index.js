// project/server/packages/game-server/src/index.js
import { createServer } from "node:http";
import { WebSocketServer } from "ws";
import { createMastraServer } from "./mastra/index.js";
import { GameStateStore } from "./state/store.js";
import { ConnectionManager } from "./ws/connection.js";

const PORT = Number.parseInt(process.env.PORT || "3000", 10);

// --- State & connections ---
const stateStore = new GameStateStore();
const connMgr = new ConnectionManager(stateStore);

// --- Mastra MCP server ---
const { mcpServer } = createMastraServer(connMgr, stateStore);

// --- HTTP server (health check) ---
const server = createServer((req, res) => {
	res.writeHead(200, { "Content-Type": "application/json" });
	res.end(
		JSON.stringify({
			name: "legend-dad-game-server",
			status: "ok",
			godot_connected: connMgr.godotClient !== null,
			agent_count: connMgr.agentClients.size,
		}),
	);
});

// --- WebSocket server ---
const wss = new WebSocketServer({ server });

wss.on("connection", (ws, req) => {
	console.log(`[ws] new connection from ${req.socket.remoteAddress}`);
	connMgr.handleConnection(ws);
});

// --- Start ---
server.listen(PORT, () => {
	console.log(`[server] listening on http://localhost:${PORT}`);
	console.log(`[ws] WebSocket server ready on ws://localhost:${PORT}`);
	console.log(
		"[mcp] MCP server initialized — tools: move, interact, switch_era, get_state",
	);
});
