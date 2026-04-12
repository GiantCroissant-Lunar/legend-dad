// project/server/packages/game-server/src/mcp/event-queue.js

/**
 * Per-session ring buffer for game events.
 * MCP clients drain this via the poll_events tool.
 */
export class EventQueue {
	constructor(maxSize = 200) {
		this._maxSize = maxSize;
		/** @type {Array<{type: string, event?: string, data: object, timestamp: string}>} */
		this._buffer = [];
	}

	/**
	 * Push a game event into the buffer. Drops oldest if full.
	 * @param {object} msg — raw state_event or state_snapshot from Godot
	 */
	push(msg) {
		this._buffer.push({
			type: msg.type,
			event: msg.event ?? null,
			data: msg.data ?? {},
			timestamp: new Date().toISOString(),
		});
		if (this._buffer.length > this._maxSize) {
			this._buffer.shift();
		}
	}

	/**
	 * Return all buffered events and clear the buffer.
	 * @returns {Array<object>}
	 */
	drain() {
		const events = this._buffer;
		this._buffer = [];
		return events;
	}

	get size() {
		return this._buffer.length;
	}
}

/**
 * Registry of MCP session → EventQueue.
 * Handles creation, lookup, cleanup, and inactivity garbage collection.
 */
export class EventQueueRegistry {
	constructor({ inactivityMs = 5 * 60 * 1000 } = {}) {
		/** @type {Map<string, { queue: EventQueue, lastAccess: number }>} */
		this._sessions = new Map();
		this._inactivityMs = inactivityMs;

		// GC sweep every 60s
		this._gcInterval = setInterval(() => this._sweep(), 60_000);
		this._gcInterval.unref(); // don't keep process alive
	}

	/**
	 * Create a queue for a new MCP session.
	 * @param {string} sessionId
	 * @returns {EventQueue}
	 */
	create(sessionId) {
		const queue = new EventQueue();
		this._sessions.set(sessionId, { queue, lastAccess: Date.now() });
		console.log(`[mcp] event queue created for session ${sessionId}`);
		return queue;
	}

	/**
	 * Get the queue for a session, or null if not found.
	 * Updates last-access timestamp.
	 * @param {string} sessionId
	 * @returns {EventQueue|null}
	 */
	get(sessionId) {
		const entry = this._sessions.get(sessionId);
		if (!entry) return null;
		entry.lastAccess = Date.now();
		return entry.queue;
	}

	/**
	 * Remove a session's queue.
	 * @param {string} sessionId
	 */
	remove(sessionId) {
		if (this._sessions.delete(sessionId)) {
			console.log(`[mcp] event queue removed for session ${sessionId}`);
		}
	}

	/**
	 * Broadcast a game event to all active session queues.
	 * @param {object} msg
	 */
	broadcast(msg) {
		for (const { queue } of this._sessions.values()) {
			queue.push(msg);
		}
	}

	/** @private Sweep stale sessions */
	_sweep() {
		const now = Date.now();
		for (const [sessionId, entry] of this._sessions) {
			if (now - entry.lastAccess > this._inactivityMs) {
				this.remove(sessionId);
			}
		}
	}

	/**
	 * Get the first available queue (for single-client fallback).
	 * Updates last-access timestamp.
	 * @returns {EventQueue|null}
	 */
	getFirstQueue() {
		for (const [, entry] of this._sessions) {
			entry.lastAccess = Date.now();
			return entry.queue;
		}
		return null;
	}

	/** Stop the GC interval (for clean shutdown / tests). */
	dispose() {
		clearInterval(this._gcInterval);
	}
}
