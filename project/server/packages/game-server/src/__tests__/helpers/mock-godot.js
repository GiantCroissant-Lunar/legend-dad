import { WebSocket } from "ws";

/**
 * Default game state returned by mock Godot for get_state commands.
 */
export const MOCK_STATE = {
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

/**
 * Connect a mock Godot client to a WS server.
 * Responds to commands: get_state, move, interact, switch_era.
 *
 * @param {number} port - WS server port
 * @param {object} [opts]
 * @param {object} [opts.state] - Custom state to return (defaults to MOCK_STATE)
 * @returns {Promise<{ ws: WebSocket, close: () => void }>}
 */
export function connectMockGodot(port, opts = {}) {
	const state = structuredClone(opts.state ?? MOCK_STATE);

	return new Promise((resolve, reject) => {
		const ws = new WebSocket(`ws://localhost:${port}`);

		ws.on("error", reject);

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
				resolve({ ws, close: () => ws.close() });
				return;
			}

			if (msg.type === "command") {
				handleCommand(ws, msg, state);
			}
		});
	});
}

function handleCommand(ws, msg, state) {
	const { id, action, payload } = msg;

	// Always ack first
	ws.send(
		JSON.stringify({ type: "command_ack", id, success: true, error: null }),
	);

	switch (action) {
		case "get_state":
			ws.send(JSON.stringify({ type: "state_snapshot", data: state }));
			break;

		case "move":
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
								facing: payload?.direction || "right",
							},
						},
					},
				}),
			);
			break;

		case "interact":
			// Ack already sent above -- nothing more for interact
			break;

		case "switch_era": {
			state.active_era = state.active_era === "FATHER" ? "SON" : "FATHER";
			state.active_entity_id = state.active_era === "FATHER" ? "father" : "son";
			ws.send(
				JSON.stringify({
					type: "state_event",
					event: "era_switched",
					data: {
						active_era: state.active_era,
						active_entity_id: state.active_entity_id,
					},
				}),
			);
			break;
		}
	}
}
