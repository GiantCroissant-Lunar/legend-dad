// project/server/packages/game-server/src/replay/embedder.js
import { EmbeddingModel, FlagEmbedding } from "fastembed";

let _model = null;

/**
 * Initialize the fastembed model. Call once at startup.
 * @returns {Promise<void>}
 */
export async function initEmbedder() {
	if (_model) return;
	_model = await FlagEmbedding.init({
		model: EmbeddingModel.BGESmallENV15,
	});
	console.log("[embedder] BGE-small-en-v1.5 model loaded (384 dims)");
}

/**
 * Compute embedding for a single text string.
 * @param {string} text
 * @returns {Promise<number[]>} 384-dimensional float array
 */
export async function embed(text) {
	if (!_model) {
		throw new Error("embedder not initialized — call initEmbedder() first");
	}
	const batches = _model.embed([text], 1);
	for await (const batch of batches) {
		// batch is Float32Array[], we want the first (and only) item as a plain number[]
		return Array.from(batch[0]);
	}
	throw new Error("embed returned no results");
}

/**
 * Compute embeddings for multiple texts.
 * @param {string[]} texts
 * @returns {Promise<number[][]>}
 */
export async function embedBatch(texts) {
	if (!_model) {
		throw new Error("embedder not initialized — call initEmbedder() first");
	}
	const results = [];
	const batches = _model.embed(texts, 32);
	for await (const batch of batches) {
		for (const vec of batch) {
			results.push(Array.from(vec));
		}
	}
	return results;
}
