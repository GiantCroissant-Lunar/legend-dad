import { embed } from "./embedder.js";

/**
 * Queries SurrealDB to build replay context for the agent.
 * Returns a string to inject into the agent's instructions.
 */
export class ContextBuilder {
	/**
	 * @param {import('surrealdb').Surreal} db
	 */
	constructor(db) {
		this._db = db;
	}

	/**
	 * Build context string from past replay data.
	 * @param {object|null} currentState — current game state snapshot
	 * @param {object} opts
	 * @param {number} opts.maxSessions — max past session summaries (default 5)
	 * @param {number} opts.maxSimilarTurns — max similar turns from vector search (default 10)
	 * @param {number} opts.sessionRecencyHours — only sessions from last N hours (default 24)
	 * @returns {Promise<string>} context string for agent instructions
	 */
	async buildContext(currentState, opts = {}) {
		const maxSessions = opts.maxSessions ?? 5;
		const maxSimilarTurns = opts.maxSimilarTurns ?? 10;
		const recencyHours = opts.sessionRecencyHours ?? 24;

		const sections = [];

		// 1. Past session summaries
		const summaries = await this._getSessionSummaries(
			maxSessions,
			recencyHours,
		);
		if (summaries.length > 0) {
			sections.push("### Session History");
			for (const s of summaries) {
				const ago = this._timeAgo(s.ended_at || s.started_at);
				const model = s.agent_model
					? `${s.player_type}/${s.agent_model}`
					: s.player_type;
				sections.push(`- ${ago}: ${s.summary || "No summary"} (${model})`);
			}
		}

		// 2. Similar past turns (vector search)
		if (currentState) {
			const similarTurns = await this._findSimilarTurns(
				currentState,
				maxSimilarTurns,
			);
			if (similarTurns.length > 0) {
				sections.push("");
				sections.push("### Similar Past Situations");
				for (const t of similarTurns) {
					sections.push(`- [turn ${t.sequence}]: ${t.text}`);
				}
			}
		}

		if (sections.length === 0) {
			return ""; // No replay history yet
		}

		return [
			"",
			"## Past Experience",
			"",
			...sections,
			"",
			"Use this experience to make better decisions. Avoid repeating past failures.",
		].join("\n");
	}

	/** @private */
	async _getSessionSummaries(maxSessions, recencyHours) {
		const cutoff = new Date(
			Date.now() - recencyHours * 60 * 60 * 1000,
		).toISOString();
		const [results] = await this._db.query(
			`SELECT started_at, ended_at, player_type, agent_model, summary, total_actions, outcome
       FROM replay_session
       WHERE started_at > $cutoff
       ORDER BY started_at DESC
       LIMIT $limit`,
			{ cutoff, limit: maxSessions },
		);
		return results || [];
	}

	/** @private */
	async _findSimilarTurns(currentState, maxTurns) {
		// Build a query text from current state
		const activeId = currentState.active_entity_id || "";
		const entity = (currentState.entities || []).find(
			(e) =>
				e.entity_id === activeId || e.components?.player_controlled?.active,
		);

		if (!entity?.components?.grid_position) {
			return [];
		}

		const gp = entity.components.grid_position;
		const queryText = `era:${currentState.active_era || "?"} pos:(${gp.col},${gp.row}) facing:${gp.facing}`;

		let queryEmbedding;
		try {
			queryEmbedding = await embed(queryText);
		} catch {
			return [];
		}

		const [results] = await this._db.query(
			`SELECT text, sequence, action, payload, result,
              vector::similarity::cosine(embedding, $vec) AS similarity
       FROM replay_turn
       WHERE embedding <~$limit:COSINE:> $vec
       ORDER BY similarity DESC`,
			{ vec: queryEmbedding, limit: maxTurns },
		);

		return results || [];
	}

	/** @private */
	_timeAgo(isoString) {
		if (!isoString) return "unknown time";
		const diffMs = Date.now() - new Date(isoString).getTime();
		const mins = Math.floor(diffMs / 60000);
		if (mins < 60) return `${mins}m ago`;
		const hours = Math.floor(mins / 60);
		if (hours < 24) return `${hours}h ago`;
		return `${Math.floor(hours / 24)}d ago`;
	}
}
