// project/server/packages/game-server/src/replay/recorder.js
import { embed } from "./embedder.js";

/**
 * Records WS events and per-turn decision points to SurrealDB.
 * Passive observer — does not modify or delay message flow.
 */
export class Recorder {
	/**
	 * @param {import('surrealdb').Surreal} db
	 */
	constructor(db) {
		this._db = db;
		this._sessionId = null;
		this._sequence = 0;
		this._turnSequence = 0;
		this._pendingTurn = null; // { cmdId, action, payload, stateBefore, sentAt }
		this._stateStore = null;
	}

	/**
	 * Bind the state store so recorder can capture state_before/state_after.
	 * @param {import('../state/store.js').GameStateStore} stateStore
	 */
	setStateStore(stateStore) {
		this._stateStore = stateStore;
	}

	/**
	 * Start a new recording session.
	 * @param {string} playerType — "agent" or "human"
	 * @param {string|null} agentModel — e.g. "glm-5.1"
	 * @returns {Promise<string>} session record ID
	 */
	async startSession(playerType, agentModel = null) {
		const initialState = this._stateStore?.getState() ?? null;
		const [[session]] = await this._db.query(
			`CREATE replay_session SET
         started_at = time::now(),
         player_type = $player_type,
         agent_model = $agent_model,
         initial_state = $initial_state,
         total_actions = 0`,
			{
				player_type: playerType,
				agent_model: agentModel ?? "",
				initial_state: initialState ?? {},
			},
		);
		this._sessionId = session.id;
		this._sequence = 0;
		this._turnSequence = 0;
		this._pendingTurn = null;
		console.log(`[recorder] session started: ${this._sessionId}`);
		return this._sessionId;
	}

	/**
	 * End the current session.
	 * @param {string} outcome — "completed", "abandoned", "stuck"
	 */
	async endSession(outcome = "completed") {
		if (!this._sessionId) return;

		// Flush any pending turn
		if (this._pendingTurn) {
			await this._flushPendingTurn({ success: false, error: "session_ended" });
		}

		const summary = this._buildSessionSummary(outcome);

		await this._db.query(
			"UPDATE $session_id SET ended_at = time::now(), total_actions = $total_actions, outcome = $outcome, summary = $summary",
			{
				session_id: this._sessionId,
				total_actions: this._turnSequence,
				outcome,
				summary,
			},
		);

		console.log(
			`[recorder] session ended: ${this._sessionId} (${outcome}, ${this._turnSequence} actions)`,
		);
		this._sessionId = null;
	}

	/**
	 * Record a WS event. Called by ConnectionManager.onEvent.
	 * @param {string} direction — "to_godot" or "from_godot"
	 * @param {object} msg — raw WS message
	 */
	async recordEvent(direction, msg) {
		if (!this._sessionId) return;

		// Write raw event
		this._sequence++;
		await this._db.query(
			"CREATE replay_event SET session = $sid, timestamp = time::now(), direction = $direction, message = $message, sequence = $seq",
			{
				sid: this._sessionId,
				direction,
				message: msg,
				seq: this._sequence,
			},
		);

		// Turn detection
		if (
			direction === "to_godot" &&
			msg.type === "command" &&
			msg.action !== "get_state"
		) {
			// New turn starts — capture state before
			this._pendingTurn = {
				cmdId: msg.id,
				action: msg.action,
				payload: msg.payload || {},
				stateBefore: structuredClone(this._stateStore?.getState()),
				sentAt: Date.now(),
			};
		}

		if (
			direction === "from_godot" &&
			msg.type === "command_ack" &&
			this._pendingTurn
		) {
			if (msg.id === this._pendingTurn.cmdId) {
				// Turn ends — capture result and state after
				// Small delay to let state_events propagate
				await new Promise((r) => setTimeout(r, 50));
				await this._flushPendingTurn({
					success: msg.success,
					error: msg.error ?? null,
				});
			}
		}
	}

	/** @private */
	async _flushPendingTurn(result) {
		if (!this._pendingTurn || !this._sessionId) return;

		const turn = this._pendingTurn;
		this._pendingTurn = null;
		this._turnSequence++;

		const stateAfter = structuredClone(this._stateStore?.getState());
		const text = this._buildTurnText(turn, result, stateAfter);

		let embedding = null;
		try {
			embedding = await embed(text);
		} catch (err) {
			console.error("[recorder] embedding failed:", err.message);
		}

		const turnParams = {
			sid: this._sessionId,
			seq: this._turnSequence,
			state_before: turn.stateBefore ?? {},
			action: turn.action,
			payload: turn.payload,
			result,
			state_after: stateAfter ?? {},
			text,
		};

		if (embedding !== null) {
			await this._db.query(
				`CREATE replay_turn SET
           session = $sid,
           sequence = $seq,
           state_before = $state_before,
           action = $action,
           payload = $payload,
           result = $result,
           state_after = $state_after,
           text = $text,
           embedding = $embedding`,
				{ ...turnParams, embedding },
			);
		} else {
			await this._db.query(
				`CREATE replay_turn SET
           session = $sid,
           sequence = $seq,
           state_before = $state_before,
           action = $action,
           payload = $payload,
           result = $result,
           state_after = $state_after,
           text = $text`,
				turnParams,
			);
		}
	}

	/** @private */
	_buildTurnText(turn, result, stateAfter) {
		const parts = [];

		// Context from state_before
		if (turn.stateBefore) {
			const activeId = turn.stateBefore.active_entity_id || "?";
			const entity = turn.stateBefore.entities?.find(
				(e) =>
					e.entity_id === activeId || e.components?.player_controlled?.active,
			);
			if (entity?.components?.grid_position) {
				const gp = entity.components.grid_position;
				parts.push(
					`era:${turn.stateBefore.active_era || "?"} pos:(${gp.col},${gp.row}) facing:${gp.facing}`,
				);

				// Nearby entities
				const nearby = (turn.stateBefore.entities || [])
					.filter((e) => {
						if (e.entity_id === entity.entity_id) return false;
						const egp = e.components?.grid_position;
						if (!egp) return false;
						return (
							Math.abs(egp.col - gp.col) <= 2 && Math.abs(egp.row - gp.row) <= 2
						);
					})
					.map((e) => {
						const egp = e.components.grid_position;
						const type =
							e.components?.enemy?.enemy_type ||
							e.components?.interactable?.type ||
							"entity";
						return `${type}@(${egp.col},${egp.row})`;
					});

				if (nearby.length > 0) {
					parts.push(`nearby:[${nearby.join(",")}]`);
				}
			}
		}

		// Action
		const payloadStr =
			Object.keys(turn.payload).length > 0
				? ` ${Object.entries(turn.payload)
						.map(([k, v]) => v)
						.join(" ")}`
				: "";
		parts.push(`| ${turn.action}${payloadStr}`);

		// Result
		if (result.success) {
			const afterEntity = stateAfter?.entities?.find(
				(e) => e.entity_id === (turn.stateBefore?.active_entity_id || ""),
			);
			if (afterEntity?.components?.grid_position) {
				const agp = afterEntity.components.grid_position;
				parts.push(`| success -> pos:(${agp.col},${agp.row})`);
			} else {
				parts.push("| success");
			}
		} else {
			parts.push(`| failed: ${result.error || "unknown"}`);
		}

		return parts.join(" ");
	}

	/** @private */
	_buildSessionSummary(outcome) {
		return `Session (${this._turnSequence} actions). Outcome: ${outcome}.`;
	}
}
