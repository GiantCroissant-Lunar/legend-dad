#!/usr/bin/env node
/**
 * End-to-end agent verification test.
 *
 * 1. Starts the game server
 * 2. Connects a mock Godot client that responds to commands
 * 3. Creates the Mastra agent
 * 4. Asks the agent to explore the game
 * 5. Verifies the agent calls tools and receives state
 *
 * Usage:
 *   ZAI_API_KEY=<key> node src/test-agent.js
 */
import { createServer } from "node:http";
import { WebSocket, WebSocketServer } from "ws";
import { createGameAgent } from "./mastra/agent.js";
import { createMastraServer } from "./mastra/index.js";
import { ContextBuilder } from "./replay/context-builder.js";
import { initReplayDB } from "./replay/db.js";
import { initEmbedder } from "./replay/embedder.js";
import { Recorder } from "./replay/recorder.js";
import { GameStateStore } from "./state/store.js";
import { ConnectionManager } from "./ws/connection.js";

const PORT = 3099; // Use a different port to avoid conflicts

// --- Mock game state (simulates what Godot would send) ---
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
		{
			entity_id: "SonPlayer",
			components: {
				grid_position: { col: 7, row: 4, facing: "down" },
				timeline_era: { era: "SON" },
				player_controlled: { active: false },
			},
		},
		{
			entity_id: "Slime01",
			components: {
				grid_position: { col: 4, row: 4, facing: "down" },
				timeline_era: { era: "FATHER" },
				enemy: { enemy_type: "slime" },
			},
		},
	],
	map: {
		width: 10,
		height: 8,
		father_tiles: [
			[0, 0, 0, 2, 2, 0, 0, 0, 3, 3],
			[0, 0, 1, 1, 1, 1, 0, 0, 3, 3],
			[0, 1, 1, 0, 0, 1, 1, 0, 0, 3],
			[2, 1, 0, 0, 0, 0, 1, 0, 0, 0],
			[2, 1, 0, 0, 0, 0, 1, 1, 1, 0],
			[0, 1, 1, 0, 2, 0, 0, 0, 1, 0],
			[0, 0, 1, 1, 1, 1, 1, 1, 1, 0],
			[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
		],
		son_tiles: [
			[0, 0, 0, 2, 2, 0, 0, 0, 3, 3],
			[0, 0, 1, 1, 1, 1, 0, 0, 3, 3],
			[0, 1, 1, 0, 0, 1, 1, 0, 0, 3],
			[2, 1, 0, 0, 0, 0, 1, 0, 0, 0],
			[2, 1, 0, 0, 0, 0, 1, 1, 1, 0],
			[0, 1, 1, 0, 2, 0, 0, 0, 1, 0],
			[0, 0, 1, 1, 1, 1, 1, 1, 1, 0],
			[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
		],
	},
	battle: null,
};

// Track the father's position for mock updates
let fatherCol = 2;
let fatherRow = 2;
let fatherFacing = "down";

const DIRECTION_DELTAS = {
	up: { col: 0, row: -1 },
	down: { col: 0, row: 1 },
	left: { col: -1, row: 0 },
	right: { col: 1, row: 0 },
};

function isWalkable(col, row) {
	if (col < 0 || col >= 10 || row < 0 || row >= 8) return false;
	const tile = MOCK_STATE.map.father_tiles[row][col];
	return tile === 0 || tile === 1; // grass or path
}

// --- Set up server ---
const stateStore = new GameStateStore();
const connMgr = new ConnectionManager(stateStore);
const { tools } = createMastraServer(connMgr, stateStore);

const httpServer = createServer((req, res) => {
	res.writeHead(200, { "Content-Type": "text/plain" });
	res.end("test server");
});

const wss = new WebSocketServer({ server: httpServer });
wss.on("connection", (ws, req) => {
	console.log("[test] WS connection received");
	connMgr.handleConnection(ws);
});

// --- Start server ---
httpServer.listen(PORT, () => {
	console.log(`[test] server on port ${PORT}`);
	connectMockGodot();
});

// --- Mock Godot client ---
function connectMockGodot() {
	const ws = new WebSocket(`ws://localhost:${PORT}`);

	ws.on("open", () => {
		console.log("[mock-godot] connected, sending handshake");
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
			console.log("[mock-godot] handshake OK, session:", msg.session_id);
			return;
		}

		if (msg.type === "command") {
			console.log(
				`[mock-godot] received command: ${msg.action}`,
				JSON.stringify(msg.payload),
			);
			handleMockCommand(ws, msg);
			return;
		}
	});

	ws.on("error", (err) => {
		console.error("[mock-godot] error:", err.message);
	});
}

function handleMockCommand(ws, msg) {
	const { id, action, payload } = msg;

	switch (action) {
		case "get_state": {
			// Update state with current position
			MOCK_STATE.entities[0].components.grid_position = {
				col: fatherCol,
				row: fatherRow,
				facing: fatherFacing,
			};
			ws.send(
				JSON.stringify({ type: "command_ack", id, success: true, error: null }),
			);
			ws.send(JSON.stringify({ type: "state_snapshot", data: MOCK_STATE }));
			console.log(
				`[mock-godot] sent state snapshot (father at ${fatherCol},${fatherRow})`,
			);
			break;
		}
		case "move": {
			const dir = payload.direction;
			fatherFacing = dir;
			const delta = DIRECTION_DELTAS[dir];
			const newCol = fatherCol + delta.col;
			const newRow = fatherRow + delta.row;

			if (isWalkable(newCol, newRow)) {
				fatherCol = newCol;
				fatherRow = newRow;
				ws.send(
					JSON.stringify({
						type: "command_ack",
						id,
						success: true,
						error: null,
					}),
				);
				// Push state event
				ws.send(
					JSON.stringify({
						type: "state_event",
						event: "entity_updated",
						data: {
							entity_id: "FatherPlayer",
							components: {
								grid_position: {
									col: fatherCol,
									row: fatherRow,
									facing: fatherFacing,
								},
								timeline_era: { era: "FATHER" },
								player_controlled: { active: true },
							},
						},
					}),
				);
				console.log(`[mock-godot] moved ${dir} to ${fatherCol},${fatherRow}`);
			} else {
				ws.send(
					JSON.stringify({
						type: "command_ack",
						id,
						success: false,
						error: `tile ${newCol},${newRow} not walkable`,
					}),
				);
				console.log(
					`[mock-godot] move ${dir} blocked (${newCol},${newRow} not walkable)`,
				);
			}
			break;
		}
		case "interact": {
			ws.send(
				JSON.stringify({
					type: "command_ack",
					id,
					success: false,
					error: "no_interactable_in_front",
				}),
			);
			console.log("[mock-godot] interact — nothing in front");
			break;
		}
		case "switch_era": {
			ws.send(
				JSON.stringify({ type: "command_ack", id, success: true, error: null }),
			);
			MOCK_STATE.active_era =
				MOCK_STATE.active_era === "FATHER" ? "SON" : "FATHER";
			MOCK_STATE.active_entity_id =
				MOCK_STATE.active_era === "FATHER" ? "father" : "son";
			ws.send(
				JSON.stringify({
					type: "state_event",
					event: "era_switched",
					data: {
						active_era: MOCK_STATE.active_era,
						active_entity_id: MOCK_STATE.active_entity_id,
					},
				}),
			);
			console.log(`[mock-godot] switched to ${MOCK_STATE.active_era}`);
			break;
		}
		default:
			ws.send(
				JSON.stringify({
					type: "command_ack",
					id,
					success: false,
					error: `unknown: ${action}`,
				}),
			);
	}
}

// --- Run agent after a short delay for connections to establish ---
setTimeout(runAgent, 2000);

async function runAgent() {
	console.log("\n=== AGENT TEST START ===\n");

	// --- Replay setup ---
	let recorder = null;
	let contextBuilder = null;
	let replayDb = null;
	try {
		replayDb = await initReplayDB();
		await initEmbedder();
		recorder = new Recorder(replayDb);
		recorder.setStateStore(stateStore);
		contextBuilder = new ContextBuilder(replayDb);

		// Hook recorder into connection manager
		connMgr.onEvent((direction, msg) => {
			recorder.recordEvent(direction, msg).catch(console.error);
		});

		await recorder.startSession("agent", "rotating");
		console.log("[test] replay recording enabled\n");
	} catch (err) {
		console.warn("[test] replay disabled:", err.message);
	}

	// Provider rotation — both keys from env vars
	const providers = [
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

	const agent = await createGameAgent(tools, {
		providers,
		contextBuilder,
		stateStore,
	});

	try {
		console.log("[agent] Asking agent to explore the game...\n");

		const result = await agent.generate(
			"Get the current game state, then move the player right twice and down once. After each move, report what happened.",
			{ maxSteps: 10 },
		);

		console.log("\n=== AGENT RESPONSE ===\n");
		console.log(result.text);
		console.log("\n=== TOOL CALLS ===\n");
		if (result.steps) {
			for (const step of result.steps) {
				if (step.toolCalls) {
					for (const tc of step.toolCalls) {
						console.log(
							`  ${tc.toolName}(${JSON.stringify(tc.args)}) → ${JSON.stringify(tc.result)}`,
						);
					}
				}
			}
		}
		console.log("\n=== VERIFICATION ===");
		console.log(`Father position: col=${fatherCol}, row=${fatherRow}`);
		console.log("Expected: col=4, row=3 (right, right, down from 2,2)");
		console.log(
			`Match: ${fatherCol === 4 && fatherRow === 3 ? "✅ PASS" : "❌ FAIL (agent may have adapted to blocked tiles)"}`,
		);
		// --- Replay verification ---
		if (recorder) {
			await recorder.endSession("completed");

			const [sessions] = await replayDb.query("SELECT * FROM replay_session");
			const [eventCounts] = await replayDb.query(
				"SELECT count() FROM replay_event GROUP ALL",
			);
			const [turns] = await replayDb.query(
				"SELECT text, sequence FROM replay_turn ORDER BY sequence",
			);

			console.log("\n=== REPLAY VERIFICATION ===");
			console.log(`Sessions: ${sessions?.length || 0}`);
			console.log(`Events: ${eventCounts?.[0]?.count || 0}`);
			console.log(`Turns: ${turns?.length || 0}`);
			if (turns?.length > 0) {
				console.log("Turn texts:");
				for (const t of turns) {
					console.log(`  [${t.sequence}] ${t.text}`);
				}
			}
			console.log(
				`Replay: ${(sessions?.length || 0) > 0 && (turns?.length || 0) > 0 ? "✅ PASS" : "❌ FAIL"}`,
			);

			// Test context builder
			const context = await contextBuilder.buildContext(stateStore.getState());
			console.log("\n=== CONTEXT BUILDER OUTPUT ===");
			console.log(
				context || "(empty — first run, no prior sessions to reference)",
			);

			await replayDb.close();
		}

		console.log("\n=== AGENT TEST COMPLETE ===\n");
	} catch (err) {
		console.error("[agent] Error:", err.message);
		if (err.cause) console.error("[agent] Cause:", err.cause);
		if (replayDb) {
			try {
				await replayDb.close();
			} catch (_) {
				// ignore
			}
		}
	}

	// Cleanup
	httpServer.close();
	wss.close();
	process.exit(0);
}
