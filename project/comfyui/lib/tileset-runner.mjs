/**
 * tileset-runner.mjs — Read vault biome defs, build prompts, queue ComfyUI tileset jobs.
 *
 * Usage:
 *   node project/comfyui/lib/tileset-runner.mjs --biome=field
 *   node project/comfyui/lib/tileset-runner.mjs --biome=field --seed=42
 *   node project/comfyui/lib/tileset-runner.mjs --biome=all
 *   node project/comfyui/lib/tileset-runner.mjs --biome=field --dry-run
 *
 * Env vars:
 *   COMFYUI_BASE_URL     (default: http://127.0.0.1:8188)
 *   COMFYUI_CHECKPOINT   (default: sd_xl_base_1.0.safetensors)
 *   COMFYUI_LORA         (default: pixel-art-xl.safetensors)
 *   COMFYUI_LORA_STRENGTH (default: 0.85)
 *   COMFYUI_STEPS        (default: 25)
 *   COMFYUI_CFG          (default: 7)
 */

import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { loadWorkflowAsPrompt, applyOverrides } from './workflow-loader.mjs';
import { queuePrompt, waitForPromptCompletion, downloadOutputImages, pingComfyUi } from './comfyui-client.mjs';

const PROJECT_ROOT = join(import.meta.dirname, '..', '..', '..');
const WORKFLOW_PATH = join(PROJECT_ROOT, 'project/comfyui/workflows/tileset-grayscale.json');
const OUTPUT_DIR = join(PROJECT_ROOT, 'build/tilesets');

// Biome prompt definitions — matching vault/world/biomes/_comfyui-workflows.md
const BIOME_PROMPTS = {
  field: {
    positive: [
      '16-bit pixel art tileset sheet, top-down 3/4 perspective, 16x16 tile grid layout,',
      'JRPG style, grayscale, monochrome, black and white tonal values only,',
      'old-growth forest biome, grass tiles, dirt path tiles, tree trunk tiles,',
      'bush tiles, water stream tiles, stone path tiles, fallen log, wildflowers,',
      'seamless tile edges, clean pixel edges, no anti-aliasing, flat background',
    ].join(' '),
    negative: [
      'blurry, smooth, anti-aliased, 3D render, photograph, realistic, photorealistic,',
      'gradient, color, colored, chromatic, RGB, hue, saturation,',
      'watermark, text, UI elements, modern, high resolution details',
    ].join(' '),
  },
  dungeon: {
    positive: [
      '16-bit pixel art tileset sheet, top-down 3/4 perspective, 16x16 tile grid layout,',
      'JRPG style, grayscale, monochrome, black and white tonal values only,',
      'underground cave mine biome, cave floor tiles, cave wall tiles, mine track tiles,',
      'ore vein tiles, crystal tiles, lava pool tiles, rubble tiles, torch bracket,',
      'seamless tile edges, clean pixel edges, no anti-aliasing, flat background,',
      'dark ambient lighting with localized light sources',
    ].join(' '),
    negative: [
      'blurry, smooth, anti-aliased, 3D render, photograph, realistic, photorealistic,',
      'gradient, color, colored, chromatic, RGB, hue, saturation,',
      'watermark, text, UI elements, modern, high resolution details',
    ].join(' '),
  },
  town: {
    positive: [
      '16-bit pixel art tileset sheet, top-down 3/4 perspective, 16x16 tile grid layout,',
      'JRPG style, grayscale, monochrome, black and white tonal values only,',
      'medieval village biome with open-top buildings interiors visible,',
      'cobblestone tiles, building wall tiles, wood floor tiles, furniture tiles,',
      'fence tiles, market stall, well, door frame, window, roof edge,',
      'seamless tile edges, clean pixel edges, no anti-aliasing, flat background,',
      'warm ambient lighting',
    ].join(' '),
    negative: [
      'blurry, smooth, anti-aliased, 3D render, photograph, realistic, photorealistic,',
      'gradient, color, colored, chromatic, RGB, hue, saturation,',
      'watermark, text, UI elements, modern, high resolution details',
    ].join(' '),
  },
};

function parseArgs() {
  const args = {};
  for (const arg of process.argv.slice(2)) {
    if (arg.startsWith('--')) {
      const [key, ...rest] = arg.slice(2).split('=');
      args[key] = rest.join('=') || 'true';
    }
  }
  return args;
}

function buildOverrides(biome, seed) {
  const prompts = BIOME_PROMPTS[biome];
  if (!prompts) {
    throw new Error(`Unknown biome: ${biome}. Available: ${Object.keys(BIOME_PROMPTS).join(', ')}`);
  }

  const checkpoint = process.env.COMFYUI_CHECKPOINT || 'sd_xl_base_1.0.safetensors';
  const lora = process.env.COMFYUI_LORA || 'pixel-art-xl.safetensors';
  const loraStrength = Number(process.env.COMFYUI_LORA_STRENGTH) || 0.85;
  const steps = Number(process.env.COMFYUI_STEPS) || 25;
  const cfg = Number(process.env.COMFYUI_CFG) || 7;

  // Node IDs match tileset-grayscale.json
  return {
    '1.ckpt_name': checkpoint,
    '2.lora_name': lora,
    '2.strength_model': loraStrength,
    '2.strength_clip': loraStrength,
    '5.text': prompts.positive,        // Positive CLIPTextEncode
    '6.text': prompts.negative,        // Negative CLIPTextEncode
    '8.seed': seed ?? Math.floor(Math.random() * 2 ** 32),
    '8.steps': steps,
    '8.cfg': cfg,
  };
}

async function runBiome(biome, args) {
  const dryRun = args['dry-run'] === 'true';
  const seed = args.seed ? Number(args.seed) : undefined;

  console.log(`\n=== Biome: ${biome} ===`);

  // Load workflow and apply overrides
  const basePrompt = loadWorkflowAsPrompt(WORKFLOW_PATH);
  const overrides = buildOverrides(biome, seed);
  const prompt = applyOverrides(basePrompt, overrides);

  const biomeOutputDir = join(OUTPUT_DIR, biome);
  mkdirSync(biomeOutputDir, { recursive: true });

  if (dryRun) {
    const jobPath = join(biomeOutputDir, 'dry-run-job.json');
    writeFileSync(jobPath, JSON.stringify(prompt, null, 2));
    console.log(`[dry-run] Workflow written to ${jobPath}`);
    console.log(`[dry-run] Positive prompt: ${overrides['5.text'].slice(0, 80)}...`);
    console.log(`[dry-run] Seed: ${overrides['8.seed']}`);
    return;
  }

  // Ping ComfyUI
  console.log('Connecting to ComfyUI...');
  const stats = await pingComfyUi();
  console.log(`ComfyUI online — ${stats.system?.devices?.[0]?.name || 'unknown device'}`);

  // Queue prompt
  console.log('Queuing tileset generation...');
  const promptId = await queuePrompt({ workflow: prompt });
  console.log(`Queued: ${promptId}`);

  // Wait for completion
  console.log('Waiting for generation...');
  const history = await waitForPromptCompletion({ promptId });
  console.log('Generation complete.');

  // Download outputs
  const files = await downloadOutputImages({
    promptHistory: history,
    targetDir: biomeOutputDir,
  });

  console.log(`Downloaded ${files.length} images to ${biomeOutputDir}/`);
  for (const f of files) {
    console.log(`  ${f}`);
  }
}

async function main() {
  const args = parseArgs();
  const biomeArg = args.biome;

  if (!biomeArg) {
    console.error('Usage: node tileset-runner.mjs --biome=<field|dungeon|town|all> [--seed=N] [--dry-run]');
    process.exit(1);
  }

  const biomes = biomeArg === 'all' ? Object.keys(BIOME_PROMPTS) : [biomeArg];

  for (const biome of biomes) {
    await runBiome(biome, args);
  }

  console.log('\nDone.');
}

main().catch((err) => {
  console.error('Error:', err.message);
  process.exit(1);
});
