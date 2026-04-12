// project/server/packages/game-server/src/state/store.js

/**
 * In-memory game state store.
 * Updated by state_event and state_snapshot messages from Godot.
 */
export class GameStateStore {
	constructor() {
		/** @type {object|null} Full game state snapshot */
		this.snapshot = null;
		/** @type {Array<object>} Recent state events (ring buffer, max 100) */
		this.recentEvents = [];
		this._maxEvents = 100;
	}

	/**
	 * Replace entire state with a snapshot from Godot.
	 */
	setSnapshot(data) {
		this.snapshot = data;
	}

	/**
	 * Apply a state_event from Godot.
	 * Updates snapshot if possible, stores in recent events.
	 */
	pushEvent(event) {
		this.recentEvents.push(event);
		if (this.recentEvents.length > this._maxEvents) {
			this.recentEvents.shift();
		}

		// Apply entity updates to snapshot if we have one
		if (
			this.snapshot &&
			event.event === "entity_updated" &&
			event.data?.entity_id
		) {
			const entity = this.snapshot.entities?.find(
				(e) => e.entity_id === event.data.entity_id,
			);
			if (entity) {
				Object.assign(entity.components, event.data.components);
			}
		}

		if (this.snapshot && event.event === "era_switched" && event.data) {
			this.snapshot.active_era = event.data.active_era;
			this.snapshot.active_entity_id = event.data.active_entity_id;
		}
	}

	/**
	 * Get current state. Returns snapshot or null if not yet received.
	 */
	getState() {
		return this.snapshot;
	}

	/**
	 * Clear all state (on Godot disconnect).
	 */
	clear() {
		this.snapshot = null;
		this.recentEvents = [];
	}
}
