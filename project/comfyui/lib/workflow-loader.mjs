/**
 * Load ComfyUI editor-format workflows and extract the prompt object for API execution.
 *
 * Editor format: saved from ComfyUI UI, contains node positions, groups, UI metadata.
 * API format: flat node graph keyed by ID — what the /prompt endpoint accepts.
 *
 * Editor-format JSON can have two shapes:
 *   1. Top-level keys include "nodes" + "links" (legacy editor save)
 *   2. Top-level keys include "workflow" + "prompt" (export with embedded API prompt)
 *
 * If the workflow is already in API format (keys are numeric string IDs with class_type),
 * it is returned as-is.
 */

import { readFileSync } from "fs";

// Node types that exist only in the editor UI and must not appear in the API prompt.
// Their values are wired into target nodes via links.
const EDITOR_ONLY_TYPES = new Set(["PrimitiveNode", "Reroute", "Note"]);

/**
 * Load a workflow JSON and return the API-ready prompt object.
 * @param {string} filePath - Path to the .json workflow file
 * @returns {object} The prompt object ready for ComfyUI /prompt API
 */
export function loadWorkflowAsPrompt(filePath) {
	const raw = JSON.parse(readFileSync(filePath, "utf-8"));

	// Shape 2: has embedded prompt
	if (raw.prompt && typeof raw.prompt === "object") {
		return raw.prompt;
	}

	// Shape 1: editor-format with "nodes" array — convert to API format
	if (Array.isArray(raw.nodes)) {
		return editorNodesToApiPrompt(raw.nodes, raw.links || []);
	}

	// Already API format (keys are numeric IDs with class_type)
	const firstKey = Object.keys(raw)[0];
	if (raw[firstKey]?.class_type) {
		return raw;
	}

	throw new Error(`Unrecognized workflow format in ${filePath}`);
}

/**
 * Convert editor-format nodes array + links to API prompt object.
 *
 * Key behaviors:
 * - Skips editor-only nodes (PrimitiveNode, Reroute, Note) and bypassed nodes
 * - Wires node-to-node connections via link references
 * - For PrimitiveNode sources, injects their widget value directly into the target input
 * - Maps widget_values to input names using the node's inputs/outputs metadata
 */
function editorNodesToApiPrompt(nodes, links) {
	const prompt = {};
	const nodeMap = new Map();
	for (const node of nodes) {
		nodeMap.set(node.id, node);
	}

	// Build link lookup: link_id → { fromNode, fromSlot, toNode, toSlot, type }
	const linkMap = new Map();
	for (const link of links) {
		const [linkId, fromNode, fromSlot, toNode, toSlot, type] = link;
		linkMap.set(linkId, { fromNode, fromSlot, toNode, toSlot, type });
	}

	// First pass: create API entries for real (non-editor-only) nodes
	for (const node of nodes) {
		if (EDITOR_ONLY_TYPES.has(node.type)) continue;
		if (node.mode === 4) continue; // bypassed

		const entry = {
			class_type: node.type,
			inputs: {},
		};

		// Map widget values to input names.
		// In ComfyUI editor format, widgets_values is a flat array of all widget values.
		// Node inputs that are connected via links are NOT widgets — they're link inputs.
		// The widget_values array only contains values for unconnected (widget) inputs.
		//
		// Strategy: walk the node's "inputs" array (link-type inputs) to know which names
		// are link inputs vs widgets. Then assign widgets_values positionally to the
		// remaining input names from the node definition.
		//
		// Since we don't have the full node definition here, we use a simpler approach:
		// assign widget_values to known input names by node type.
		assignWidgetValues(entry, node);

		prompt[String(node.id)] = entry;
	}

	// Second pass: wire links
	for (const node of nodes) {
		if (EDITOR_ONLY_TYPES.has(node.type)) continue;
		if (node.mode === 4) continue;

		const entry = prompt[String(node.id)];
		if (!entry || !node.inputs) continue;

		for (const input of node.inputs) {
			if (input.link == null) continue;
			const link = linkMap.get(input.link);
			if (!link) continue;

			const sourceNode = nodeMap.get(link.fromNode);
			if (!sourceNode) continue;

			if (EDITOR_ONLY_TYPES.has(sourceNode.type)) {
				// PrimitiveNode/Reroute: inject widget value directly
				const value = sourceNode.widgets_values?.[0];
				if (value !== undefined) {
					entry.inputs[input.name] = value;
				}
			} else {
				// Normal node: reference as [nodeId, outputSlot]
				entry.inputs[input.name] = [String(link.fromNode), link.fromSlot];
			}
		}
	}

	return prompt;
}

/**
 * Assign widget_values to named inputs based on node type.
 * This maps known ComfyUI node types to their widget input names.
 */
function assignWidgetValues(entry, node) {
	const wv = node.widgets_values;
	if (!wv || wv.length === 0) return;

	const type = node.type;

	// Known node type → widget name mappings (positional)
	const WIDGET_MAPS = {
		CheckpointLoaderSimple: ["ckpt_name"],
		LoraLoader: ["lora_name", "strength_model", "strength_clip"],
		CLIPTextEncode: ["text"],
		EmptyLatentImage: ["width", "height", "batch_size"],
		KSampler: [
			"seed",
			"control_after_generate",
			"steps",
			"cfg",
			"sampler_name",
			"scheduler",
			"denoise",
		],
		SaveImage: ["filename_prefix"],
		ImageScale: ["upscale_method", "width", "height", "crop"],
		PixelArtDetectorToImage: ["reduce_palette", "reduce_palette_max_colors"],
		PixelArtLoadPalettes: [
			"image",
			"render_all_palettes_in_grid",
			"grid_settings",
			"paletteList_grid_font_size",
			"paletteList_grid_font_color",
			"paletteList_grid_background",
			"paletteList_grid_cols",
			"paletteList_grid_add_border",
			"paletteList_grid_border_width",
		],
		PixelArtDetectorConverter: [
			"palette",
			"resize_w",
			"resize_h",
			"resize_type",
			"pixelize",
			"grid_pixelate_grid_scan_size",
			"reduce_colors_before_palette_swap",
			"reduce_colors_method",
			"reduce_colors_max_colors",
			"apply_pixeldetector_max_colors",
			"image_quantize_reduce_method",
			"opencv_settings",
			"opencv_kmeans_centers",
			"opencv_kmeans_attempts",
			"opencv_criteria_max_iterations",
			"pycluster_kmeans_metrics",
			"cleanup",
			"cleanup_colors",
			"cleanup_pixels_threshold",
			"dither",
		],
	};

	const widgetNames = WIDGET_MAPS[type];
	if (widgetNames) {
		for (let i = 0; i < widgetNames.length && i < wv.length; i++) {
			entry.inputs[widgetNames[i]] = wv[i];
		}
	}

	// For unknown types, store all widget values as _raw_widgets for debugging
	// (the override system can still target these nodes by ID)
	if (!widgetNames && wv.length > 0) {
		entry._raw_widgets = wv;
	}

	// Post-process: fix enum values that don't match the current node version.
	// PixelArtDetectorConverter's "palette" field only accepts known palettes
	// (e.g. NES, GAMEBOY). When a paletteList link overrides it, set a valid
	// placeholder so validation passes.
	if (type === "PixelArtDetectorConverter") {
		const validPalettes = ["NES", "GAMEBOY"];
		if (entry.inputs.palette && !validPalettes.includes(entry.inputs.palette)) {
			entry.inputs.palette = "NES"; // placeholder — overridden by paletteList link
		}
	}
}

/**
 * Apply parameter overrides to an API prompt object.
 * @param {object} prompt - API prompt object
 * @param {object} overrides - Map of nodeId.inputKey → value
 * @returns {object} Modified prompt
 */
export function applyOverrides(prompt, overrides) {
	const result = JSON.parse(JSON.stringify(prompt)); // deep clone

	for (const [path, value] of Object.entries(overrides)) {
		const [nodeId, ...keyParts] = path.split(".");
		const key = keyParts.join(".");

		if (!result[nodeId]) {
			throw new Error(
				`Override target node "${nodeId}" not found in workflow`,
			);
		}

		result[nodeId].inputs[key] = value;
	}

	return result;
}
