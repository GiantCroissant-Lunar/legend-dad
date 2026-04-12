// project/server/packages/game-server/src/replay/db.js
import { Surreal } from "surrealdb";

const SURREAL_URL = process.env.SURREAL_URL || "ws://localhost:6480";
const SURREAL_NS = process.env.SURREAL_NS || "legend_dad";
const SURREAL_DB = process.env.SURREAL_DB || "replay";
const SURREAL_USER = process.env.SURREAL_USER || "root";
const SURREAL_PASS = process.env.SURREAL_PASS || "root";

const SCHEMA = `
DEFINE TABLE IF NOT EXISTS replay_session SCHEMALESS;
DEFINE FIELD IF NOT EXISTS started_at ON replay_session TYPE datetime;
DEFINE FIELD IF NOT EXISTS ended_at ON replay_session TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS player_type ON replay_session TYPE string;
DEFINE FIELD IF NOT EXISTS agent_model ON replay_session TYPE option<string>;
DEFINE FIELD IF NOT EXISTS initial_state ON replay_session TYPE option<object>;
DEFINE FIELD IF NOT EXISTS summary ON replay_session TYPE option<string>;
DEFINE FIELD IF NOT EXISTS total_actions ON replay_session TYPE int DEFAULT 0;
DEFINE FIELD IF NOT EXISTS outcome ON replay_session TYPE option<string>;

DEFINE TABLE IF NOT EXISTS replay_event SCHEMALESS;
DEFINE FIELD IF NOT EXISTS session ON replay_event TYPE record<replay_session>;
DEFINE FIELD IF NOT EXISTS timestamp ON replay_event TYPE datetime;
DEFINE FIELD IF NOT EXISTS direction ON replay_event TYPE string;
DEFINE FIELD IF NOT EXISTS message ON replay_event TYPE object;
DEFINE FIELD IF NOT EXISTS sequence ON replay_event TYPE int;
DEFINE INDEX IF NOT EXISTS replay_event_session ON replay_event FIELDS session;

DEFINE TABLE IF NOT EXISTS replay_turn SCHEMALESS;
DEFINE FIELD IF NOT EXISTS session ON replay_turn TYPE record<replay_session>;
DEFINE FIELD IF NOT EXISTS sequence ON replay_turn TYPE int;
DEFINE FIELD IF NOT EXISTS state_before ON replay_turn TYPE option<object>;
DEFINE FIELD IF NOT EXISTS action ON replay_turn TYPE string;
DEFINE FIELD IF NOT EXISTS payload ON replay_turn TYPE object;
DEFINE FIELD IF NOT EXISTS result ON replay_turn TYPE object;
DEFINE FIELD IF NOT EXISTS state_after ON replay_turn TYPE option<object>;
DEFINE FIELD IF NOT EXISTS text ON replay_turn TYPE string;
DEFINE FIELD IF NOT EXISTS embedding ON replay_turn TYPE option<array>;
DEFINE INDEX IF NOT EXISTS replay_turn_session ON replay_turn FIELDS session;
DEFINE INDEX IF NOT EXISTS replay_turn_vec ON replay_turn FIELDS embedding HNSW DIMENSION 384 DIST COSINE;
`;

/**
 * Connect to SurrealDB and ensure replay schema exists.
 * @returns {Promise<Surreal>}
 */
export async function initReplayDB() {
	const db = new Surreal();

	await db.connect(SURREAL_URL);
	await db.signin({ username: SURREAL_USER, password: SURREAL_PASS });
	await db.use({ namespace: SURREAL_NS, database: SURREAL_DB });

	// Apply schema (idempotent — IF NOT EXISTS)
	await db.query(SCHEMA);
	console.log(
		`[replay-db] connected to ${SURREAL_URL} ns=${SURREAL_NS} db=${SURREAL_DB}`,
	);

	return db;
}
