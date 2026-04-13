#!/usr/bin/env node
/**
 * MCP transport verification test.
 *
 * 1. Starts the game server
 * 2. Connects a mock Godot client
 * 3. Tests MCP initialize, tools/list, and tool calls via HTTP
 * 4. Verifies poll_events receives game state events
 *
 * Usage:
 *   node src/test-mcp.js
 */
import { createServer } from "node:http";
import { WebSocket, WebSocketServer } from "ws";
import { createMastraServer } from "./mastra/index.js";
import { EventQueueRegistry } from "./mcp/event-queue.js";
import { GameStateStore } from "./state/store.js";
import { ConnectionManager } from "./ws/connection.js";

const PORT = 3098;
const BASE = `http://localhost:${PORT}`;
const MCP_URL = `${BASE}/mcp`;
const HEADERS = {
	"Content-Type": "application/json",
	Accept: "application/json, text/event-stream",
};

let sessionId = null;
let passed = 0;
let failed = 0;

function assert(label, condition, detail = "") {
	if (condition) {
		console.log(`  ✅ ${label}`);
		passed++;
	} else {
		console.log(`  ❌ ${label}${detail ? ` — ${detail}` : ""}`);
		failed++;
	}
}

/** Parse SSE response body into JSON-RPC result */
function parseSSE(body) {
	for (const line of body.split("\n")) {
		if (line.startsWith("data: ")) {
			return JSON.parse(line.slice(6));
		}
	}
	// Try direct JSON parse
	return JSON.parse(body);
}

async function mcpRequest(method, params = {}, id = 1) {
	const headers = { ...HEADERS };
	if (sessionId) {
		headers["mcp-session-id"] = sessionId;
	}
	const res = await fetch(MCP_URL, {
		method: "POST",
		headers,
		body: JSON.stringify({ jsonrpc: "2.0", id, method, params }),
	});

	// Capture session ID from response
	const sid = res.headers.get("mcp-session-id");
	if (sid) sessionId = sid;

	const text = await res.text();
	return { status: res.status, body: parseSSE(text), raw: text };
}

// --- Mock game state ---
const MOCK_STATE = {
	active_era: "FATHER",
	active_entity_id: "father",
	entities: [
		{
			entity_id: "FatherPlayer",
			components: {
				grid_position: { col: 2, row: 2, facing: "down" },
				timeline_era: { era: "FATHER" },
				player_controlled: { active: true },
			},
		},
	],
	map: { width: 10, height: 8, father_tiles: [[0]], son_tiles: [[0]] },
	battle: null,
};

// --- Set up server ---
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
	const url = new URL(req.url || "", `http://localhost:${PORT}`);
	if (url.pathname === "/mcp") {
		await mcpServer.startHTTP({
			url,
			httpPath: "/mcp",
			req,
			res,
		});
		return;
	}
	res.writeHead(200);
	res.end("ok");
});

const wss = new WebSocketServer({ server: httpServer });
wss.on("connection", (ws) => connMgr.handleConnection(ws));

// --- Start ---
httpServer.listen(PORT, async () => {
	console.log(`[test-mcp] server on port ${PORT}\n`);

	// Connect mock Godot
	await connectMockGodot();
	// Wait for handshake
	await sleep(500);

	await runTests();

	console.log(`\n=== RESULTS: ${passed} passed, ${failed} failed ===\n`);
	httpServer.close();
	wss.close();
	eventRegistry.dispose();
	process.exit(failed > 0 ? 1 : 0);
});

function sleep(ms) {
	return new Promise((r) => setTimeout(r, ms));
}

function connectMockGodot() {
	return new Promise((resolve) => {
		const ws = new WebSocket(`ws://localhost:${PORT}`);
		ws.on("open", () => {
			ws.send(
				JSON.stringify({
					type: "handshake",
					client_type: "godot",
					name: "mock-godot",
				}),
			);
		});
		ws.on("message", (raw) => {
			const msg = JSON.parse(raw.toString());
			if (msg.type === "handshake_ack") {
				resolve(ws);
			}
			if (msg.type === "command") {
				// Respond to all commands
				ws.send(
					JSON.stringify({
						type: "command_ack",
						id: msg.id,
						success: true,
						error: null,
					}),
				);
				if (msg.action === "get_state") {
					ws.send(JSON.stringify({ type: "state_snapshot", data: MOCK_STATE }));
				}
				if (msg.action === "move") {
					ws.send(
						JSON.stringify({
							type: "state_event",
							event: "entity_updated",
							data: {
								entity_id: "FatherPlayer",
								components: {
									grid_position: {
										col: 3,
										row: 2,
										facing: msg.payload?.direction || "right",
									},
								},
							},
						}),
					);
				}
			}
		});
	});
}

async function runTests() {
	// --- Test 1: Initialize ---
	console.log("Test 1: MCP Initialize");
	const init = await mcpRequest("initialize", {
		protocolVersion: "2025-03-26",
		capabilities: {},
		clientInfo: { name: "test-mcp", version: "0.1.0" },
	});
	assert("status 200", init.status === 200);
	assert(
		"returns server info",
		init.body?.result?.serverInfo?.name === "Legend Dad Game Server",
		`got: ${init.body?.result?.serverInfo?.name}`,
	);
	assert(
		"has tools capability",
		init.body?.result?.capabilities?.tools !== undefined,
	);

	// Send initialized notification
	await fetch(MCP_URL, {
		method: "POST",
		headers: { ...HEADERS, "mcp-session-id": sessionId },
		body: JSON.stringify({
			jsonrpc: "2.0",
			method: "notifications/initialized",
		}),
	});
	await sleep(200);

	// --- Test 2: List Tools ---
	console.log("\nTest 2: List Tools");
	const tools = await mcpRequest("tools/list", {}, 2);
	assert("status 200", tools.status === 200);
	const toolNames = (tools.body?.result?.tools || []).map((t) => t.name).sort();
	assert(
		"has 5 tools",
		toolNames.length === 5,
		`got ${toolNames.length}: ${toolNames.join(", ")}`,
	);
	assert("has move", toolNames.includes("move"));
	assert("has interact", toolNames.includes("interact"));
	assert("has switch_era", toolNames.includes("switch_era"));
	assert("has get_state", toolNames.includes("get_state"));
	assert("has poll_events", toolNames.includes("poll_events"));

	// --- Test 3: Call get_state ---
	console.log("\nTest 3: Call get_state");
	const state = await mcpRequest(
		"tools/call",
		{ name: "get_state", arguments: {} },
		3,
	);
	assert("status 200", state.status === 200);
	const stateContent = state.body?.result?.content?.[0]?.text;
	let stateData = null;
	try {
		stateData = JSON.parse(stateContent);
	} catch {}
	assert(
		"returns state object",
		stateData?.state !== null,
		`got: ${stateContent?.slice(0, 100)}`,
	);
	assert("active_era is FATHER", stateData?.state?.active_era === "FATHER");

	// --- Test 4: Call move ---
	console.log("\nTest 4: Call move");
	const move = await mcpRequest(
		"tools/call",
		{ name: "move", arguments: { direction: "right" } },
		4,
	);
	assert("status 200", move.status === 200);
	const moveContent = move.body?.result?.content?.[0]?.text;
	let moveData = null;
	try {
		moveData = JSON.parse(moveContent);
	} catch {}
	assert("move succeeded", moveData?.success === true, `got: ${moveContent}`);

	// Wait for event to propagate
	await sleep(300);

	// --- Test 5: Call poll_events ---
	console.log("\nTest 5: Call poll_events");
	const poll = await mcpRequest(
		"tools/call",
		{ name: "poll_events", arguments: {} },
		5,
	);
	assert("status 200", poll.status === 200);
	const pollContent = poll.body?.result?.content?.[0]?.text;
	let pollData = null;
	try {
		pollData = JSON.parse(pollContent);
	} catch {}
	assert("has events", pollData?.count > 0, `got count: ${pollData?.count}`);
	const hasEntityUpdate = pollData?.events?.some(
		(e) => e.event === "entity_updated",
	);
	assert("includes entity_updated event", hasEntityUpdate);

	// --- Test 6: poll_events drains (second call empty) ---
	console.log("\nTest 6: poll_events drains queue");
	const poll2 = await mcpRequest(
		"tools/call",
		{ name: "poll_events", arguments: {} },
		6,
	);
	const poll2Content = poll2.body?.result?.content?.[0]?.text;
	let poll2Data = null;
	try {
		poll2Data = JSON.parse(poll2Content);
	} catch {}
	assert(
		"second poll is empty",
		poll2Data?.count === 0,
		`got count: ${poll2Data?.count}`,
	);
}
