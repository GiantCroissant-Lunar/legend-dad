import { randomUUID } from "node:crypto";
import {
	createCommand,
	createHandshakeAck,
	isValidHandshake,
	parseMessage,
} from "./protocol.js";

/**
 * Manages WS connections from Godot and agent clients.
 * Relays commands to Godot and state events to agents.
 */
export class ConnectionManager {
	/**
	 * @param {import('../state/store.js').GameStateStore} stateStore
	 */
	constructor(stateStore) {
		this.stateStore = stateStore;
		/** @type {{ ws: WebSocket, sessionId: string } | null} */
		this.godotClient = null;
		/** @type {Map<string, WebSocket>} sessionId → ws */
		this.agentClients = new Map();
		/** @type {Map<string, { resolve: Function, reject: Function, timer: ReturnType<typeof setTimeout> }>} */
		this._pendingAcks = new Map();
	}

	/**
	 * Handle a new WS connection. Waits for handshake message.
	 */
	handleConnection(ws) {
		let identified = false;

		ws.on("message", (raw) => {
			const { ok, msg, error } = parseMessage(raw.toString());
			if (!ok) {
				ws.send(JSON.stringify({ type: "error", error }));
				return;
			}

			if (!identified) {
				if (!isValidHandshake(msg)) {
					ws.send(
						JSON.stringify({ type: "error", error: "expected handshake" }),
					);
					return;
				}
				identified = true;
				const sessionId = randomUUID().slice(0, 12);

				if (msg.client_type === "godot") {
					this._registerGodot(ws, sessionId);
				} else {
					this._registerAgent(ws, sessionId);
				}

				ws.send(JSON.stringify(createHandshakeAck(sessionId)));
				console.log(`[conn] ${msg.client_type} registered: ${sessionId}`);
				return;
			}

			this._routeMessage(ws, msg);
		});

		ws.on("close", () => {
			this._handleDisconnect(ws);
		});
	}

	/**
	 * Send a command to Godot and wait for ack.
	 * Returns a promise that resolves with the ack or rejects on timeout.
	 */
	sendCommandToGodot(action, payload = {}, timeoutMs = 5000) {
		return new Promise((resolve, reject) => {
			if (!this.godotClient) {
				reject(new Error("no Godot client connected"));
				return;
			}

			const cmd = createCommand(action, payload);
			const timer = setTimeout(() => {
				this._pendingAcks.delete(cmd.id);
				reject(new Error(`command ${cmd.id} timed out`));
			}, timeoutMs);

			this._pendingAcks.set(cmd.id, { resolve, reject, timer });
			this.godotClient.ws.send(JSON.stringify(cmd));
		});
	}

	_registerGodot(ws, sessionId) {
		if (this.godotClient) {
			console.log("[conn] replacing existing Godot client");
			this.godotClient.ws.close(1000, "replaced by new Godot client");
		}
		this.godotClient = { ws, sessionId };

		// Request initial state snapshot
		const cmd = createCommand("get_state");
		ws.send(JSON.stringify(cmd));
	}

	_registerAgent(ws, sessionId) {
		this.agentClients.set(sessionId, ws);
		ws.on("close", () => {
			this.agentClients.delete(sessionId);
		});
	}

	_routeMessage(_ws, msg) {
		switch (msg.type) {
			case "command_ack":
				this._handleCommandAck(msg);
				break;
			case "state_snapshot":
				this.stateStore.setSnapshot(msg.data);
				this._broadcastToAgents(msg);
				break;
			case "state_event":
				this.stateStore.pushEvent(msg);
				this._broadcastToAgents(msg);
				break;
			default:
				console.log(`[conn] unknown message type: ${msg.type}`);
		}
	}

	_handleCommandAck(msg) {
		const pending = this._pendingAcks.get(msg.id);
		if (pending) {
			clearTimeout(pending.timer);
			this._pendingAcks.delete(msg.id);
			pending.resolve(msg);
		}
	}

	_broadcastToAgents(msg) {
		const raw = JSON.stringify(msg);
		for (const [sessionId, ws] of this.agentClients) {
			if (ws.readyState === ws.OPEN) {
				ws.send(raw);
			}
		}
	}

	_handleDisconnect(ws) {
		if (this.godotClient?.ws === ws) {
			console.log("[conn] Godot client disconnected");
			this.godotClient = null;
			this.stateStore.clear();
			// Notify all agents
			this._broadcastToAgents({
				type: "state_event",
				event: "game_disconnected",
				data: {},
			});
			return;
		}

		for (const [sessionId, agentWs] of this.agentClients) {
			if (agentWs === ws) {
				console.log(`[conn] agent ${sessionId} disconnected`);
				this.agentClients.delete(sessionId);
				return;
			}
		}
	}
}
