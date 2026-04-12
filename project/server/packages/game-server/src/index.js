// project/server/packages/game-server/src/index.js
import { createServer } from "node:http";
import { WebSocketServer } from "ws";
import { createMastraServer } from "./mastra/index.js";
import { ContextBuilder } from "./replay/context-builder.js";
import { initReplayDB } from "./replay/db.js";
import { initEmbedder } from "./replay/embedder.js";
import { Recorder } from "./replay/recorder.js";
import { GameStateStore } from "./state/store.js";
import { ConnectionManager } from "./ws/connection.js";

const PORT = Number.parseInt(process.env.PORT || "3000", 10);

async function main() {
	// --- State & connections ---
	const stateStore = new GameStateStore();
	const connMgr = new ConnectionManager(stateStore);

	// --- Replay system ---
	let recorder = null;
	let contextBuilder = null;
	try {
		const db = await initReplayDB();
		await initEmbedder();
		recorder = new Recorder(db);
		recorder.setStateStore(stateStore);
		contextBuilder = new ContextBuilder(db);

		// Hook recorder into connection manager
		connMgr.onEvent((direction, msg) => {
			recorder.recordEvent(direction, msg).catch((err) => {
				console.error("[replay] record error:", err.message);
			});
		});

		console.log("[replay] recording enabled");
	} catch (err) {
		console.warn("[replay] disabled —", err.message);
		console.warn("[replay] server will run without replay recording");
	}

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
				replay_enabled: recorder !== null,
			}),
		);
	});

	// --- WebSocket server ---
	const wss = new WebSocketServer({ server });

	wss.on("connection", (ws, req) => {
		console.log(`[ws] new connection from ${req.socket.remoteAddress}`);
		connMgr.handleConnection(ws);

		// End recording session when WS disconnects
		if (recorder) {
			ws.on("close", () => {
				if (recorder._sessionId) {
					recorder.endSession("abandoned").catch((err) => {
						console.error("[replay] end session error:", err.message);
					});
				}
			});
		}
	});

	// --- Start replay session when Godot registers ---
	if (recorder) {
		connMgr.onEvent((direction, msg) => {
			// Detect initial get_state command (sent right after Godot registers)
			if (
				direction === "to_godot" &&
				msg.type === "command" &&
				msg.action === "get_state"
			) {
				if (!recorder._sessionId) {
					recorder
						.startSession("agent", process.env.ZAI_MODEL || "glm-5.1")
						.catch((err) => {
							console.error("[replay] start session error:", err.message);
						});
				}
			}
		});
	}

	// --- Start ---
	server.listen(PORT, () => {
		console.log(`[server] listening on http://localhost:${PORT}`);
		console.log(`[ws] WebSocket server ready on ws://localhost:${PORT}`);
		console.log(
			"[mcp] MCP server initialized — tools: move, interact, switch_era, get_state",
		);
	});
}

main().catch((err) => {
	console.error("[server] fatal:", err);
	process.exit(1);
});
