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

import { readFileSync } from 'fs';

/**
 * Load a workflow JSON and return the API-ready prompt object.
 * @param {string} filePath - Path to the .json workflow file
 * @returns {object} The prompt object ready for ComfyUI /prompt API
 */
export function loadWorkflowAsPrompt(filePath) {
  const raw = JSON.parse(readFileSync(filePath, 'utf-8'));

  // Shape 2: has embedded prompt
  if (raw.prompt && typeof raw.prompt === 'object') {
    return raw.prompt;
  }

  // Shape 1: editor-format with "nodes" array — convert to API format
  if (Array.isArray(raw.nodes)) {
    return editorNodesToApiPrompt(raw.nodes);
  }

  // Already API format (keys are numeric IDs with class_type)
  const firstKey = Object.keys(raw)[0];
  if (raw[firstKey]?.class_type) {
    return raw;
  }

  throw new Error(`Unrecognized workflow format in ${filePath}`);
}

/**
 * Convert editor-format nodes array to API prompt object.
 */
function editorNodesToApiPrompt(nodes) {
  const prompt = {};

  for (const node of nodes) {
    if (node.type === 'Reroute' || node.mode === 4) continue; // skip bypassed nodes

    const entry = {
      class_type: node.type,
      inputs: {},
    };

    // Collect widget values
    if (node.widgets_values && node.inputs) {
      let widgetIdx = 0;
      // Widget values are positional; we map them based on input order
      // This is a simplified version — full conversion needs node definitions
      for (const input of node.inputs || []) {
        if (input.link == null && input.widget) {
          entry.inputs[input.name] = node.widgets_values[widgetIdx++];
        }
      }
    }

    prompt[String(node.id)] = entry;
  }

  return prompt;
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
    const [nodeId, ...keyParts] = path.split('.');
    const key = keyParts.join('.');

    if (!result[nodeId]) {
      throw new Error(`Override target node "${nodeId}" not found in workflow`);
    }

    result[nodeId].inputs[key] = value;
  }

  return result;
}
