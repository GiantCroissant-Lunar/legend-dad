import { createReadStream, statSync } from "node:fs";
// project/server/packages/game-server/src/index.js
import { createServer } from "node:http";
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { WebSocketServer } from "ws";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = resolve(__dirname, "../../../../..");
const PCK_DIR = resolve(PROJECT_ROOT, "build/_artifacts/pck");
import { createMastraServer } from "./mastra/index.js";
import { EventQueueRegistry } from "./mcp/event-queue.js";
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

	// --- MCP event queue registry ---
	const eventRegistry = new EventQueueRegistry();

	// Create a default queue eagerly for the single-client case (Claude Code).
	// Mastra's startHTTP onsessioninitialized callback is overridden internally,
	// so per-session queue creation doesn't work. This is the workaround.
	eventRegistry.create("default");

	// Subscribe registry to all game events from Godot
	connMgr.onEvent((direction, msg) => {
		if (
			direction === "from_godot" &&
			(msg.type === "state_event" || msg.type === "state_snapshot")
		) {
			eventRegistry.broadcast(msg);
		}
	});

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

	// --- Mastra MCP server (with event registry for poll_events) ---
	const { mcpServer } = createMastraServer(connMgr, stateStore, eventRegistry);

	// --- HTTP server (health check + MCP endpoint) ---
	const server = createServer(async (req, res) => {
		const url = new URL(req.url || "", `http://localhost:${PORT}`);

		// MCP Streamable HTTP endpoint
		if (url.pathname === "/mcp") {
			try {
				await mcpServer.startHTTP({
					url,
					httpPath: "/mcp",
					req,
					res,
				});
			} catch (err) {
				console.error("[mcp] error:", err.message);
				if (!res.headersSent) {
					res.writeHead(500, { "Content-Type": "application/json" });
					res.end(JSON.stringify({ error: "MCP error" }));
				}
			}
			return;
		}

		// Serve PCK files from build artifacts
		if (url.pathname.startsWith("/pck/")) {
			const filename = basename(url.pathname);
			if (!filename.endsWith(".pck")) {
				res.writeHead(400, { "Content-Type": "text/plain" });
				res.end("Bad request: only .pck files");
				return;
			}
			const pckPath = resolve(PCK_DIR, filename);
			try {
				const stat = statSync(pckPath);
				res.writeHead(200, {
					"Content-Type": "application/octet-stream",
					"Content-Length": stat.size,
					"Access-Control-Allow-Origin": "*",
				});
				createReadStream(pckPath).pipe(res);
			} catch {
				res.writeHead(404, { "Content-Type": "text/plain" });
				res.end(`PCK not found: ${filename}`);
			}
			return;
		}

		// Health check (default)
		res.writeHead(200, { "Content-Type": "application/json" });
		res.end(
			JSON.stringify({
				name: "legend-dad-game-server",
				status: "ok",
				godot_connected: connMgr.godotClient !== null,
				agent_count: connMgr.agentClients.size,
				replay_enabled: recorder !== null,
				mcp_enabled: true,
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
			`[mcp] Streamable HTTP endpoint at http://localhost:${PORT}/mcp`,
		);
		console.log(
			"[mcp] tools: move, interact, switch_era, get_state, poll_events",
		);
	});
}

main().catch((err) => {
	console.error("[server] fatal:", err);
	process.exit(1);
});
