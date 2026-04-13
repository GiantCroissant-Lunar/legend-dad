/**
 * ComfyUI HTTP client — queue workflows, poll for completion, download results.
 * Adapted from ultima-magic/tools/world-sync/lib/comfyui-client.mjs
 */

import { mkdirSync, writeFileSync } from 'fs';
import { join } from 'path';

const DEFAULT_BASE_URL = process.env.COMFYUI_BASE_URL || 'http://127.0.0.1:8188';
const DEFAULT_TIMEOUT = Number(process.env.COMFYUI_TIMEOUT_SECONDS) || 600;
const DEFAULT_POLL_MS = 1500;

export async function queuePrompt({ baseUrl = DEFAULT_BASE_URL, workflow, clientId = 'legend-dad' }) {
  const response = await fetchJson(`${baseUrl}/prompt`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      prompt: workflow,
      client_id: clientId,
    }),
  });

  if (!response.prompt_id) {
    throw new Error('ComfyUI did not return a prompt_id');
  }

  return response.prompt_id;
}

export async function waitForPromptCompletion({
  baseUrl = DEFAULT_BASE_URL,
  promptId,
  timeoutSeconds = DEFAULT_TIMEOUT,
  pollIntervalMs = DEFAULT_POLL_MS,
}) {
  const startedAt = Date.now();

  while ((Date.now() - startedAt) / 1000 < timeoutSeconds) {
    const history = await fetchJson(`${baseUrl}/history/${promptId}`);
    const promptHistory = history?.[promptId];
    if (promptHistory?.outputs) {
      return promptHistory;
    }

    await sleep(pollIntervalMs);
  }

  throw new Error(`Timed out waiting for ComfyUI prompt ${promptId}`);
}

export async function downloadOutputImages({ baseUrl = DEFAULT_BASE_URL, promptHistory, targetDir }) {
  mkdirSync(targetDir, { recursive: true });
  const savedPaths = [];

  for (const output of Object.values(promptHistory.outputs || {})) {
    for (const image of output.images || []) {
      const url = new URL(`${baseUrl}/view`);
      url.searchParams.set('filename', image.filename);
      url.searchParams.set('subfolder', image.subfolder || '');
      url.searchParams.set('type', image.type || 'output');

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to download ComfyUI image ${image.filename}: ${response.status}`);
      }

      const arrayBuffer = await response.arrayBuffer();
      // Prefix filename with subfolder's last segment to avoid collisions
      // e.g. "legend-dad/raw/tileset_00001_.png" → "raw_tileset_00001_.png"
      const subParts = (image.subfolder || '').split('/').filter(Boolean);
      const prefix = subParts.length > 0 ? `${subParts[subParts.length - 1]}_` : '';
      const outputPath = join(targetDir, `${prefix}${image.filename}`);
      writeFileSync(outputPath, Buffer.from(arrayBuffer));
      savedPaths.push(outputPath);
    }
  }

  return savedPaths;
}

export async function pingComfyUi(baseUrl = DEFAULT_BASE_URL) {
  const response = await fetch(`${baseUrl}/system_stats`);
  if (!response.ok) {
    throw new Error(`ComfyUI ping failed: ${response.status}`);
  }
  return response.json();
}

async function fetchJson(url, init) {
  const response = await fetch(url, init);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`ComfyUI request failed (${response.status}): ${body}`);
  }
  return response.json();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
