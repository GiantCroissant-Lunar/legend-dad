import { randomUUID } from "node:crypto";

/**
 * Message types flowing server → Godot.
 */
export function createCommand(action, payload = {}) {
	return {
		type: "command",
		id: `cmd_${randomUUID().slice(0, 8)}`,
		action,
		payload,
	};
}

/**
 * Parse and validate incoming JSON message from any WS client.
 * Returns { ok: true, msg } or { ok: false, error }.
 */
export function parseMessage(raw) {
	try {
		const msg = JSON.parse(raw);
		if (!msg.type || typeof msg.type !== "string") {
			return { ok: false, error: "missing or invalid 'type' field" };
		}
		return { ok: true, msg };
	} catch {
		return { ok: false, error: "invalid JSON" };
	}
}

/**
 * Validate a handshake message.
 */
export function isValidHandshake(msg) {
	return (
		msg.type === "handshake" &&
		(msg.client_type === "godot" || msg.client_type === "agent")
	);
}

/**
 * Create handshake acknowledgement.
 */
export function createHandshakeAck(sessionId) {
	return {
		type: "handshake_ack",
		session_id: sessionId,
	};
}
