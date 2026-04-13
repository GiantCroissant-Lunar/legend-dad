/**
 * Generate 16x1 palette swatch PNGs from vault location frontmatter.
 *
 * Reads palette-hex arrays from location markdown files and outputs
 * small PNG images for use in ComfyUI workflows (IPAdapter, reference).
 *
 * Usage: node palette-generator.mjs [--vault=vault/world/locations]
 */

import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join, basename } from 'path';
import { globSync } from 'glob';

const VAULT_DIR = process.argv.find((a) => a.startsWith('--vault='))?.split('=')[1] || 'vault/world/locations';
const OUTPUT_DIR = 'project/comfyui/palettes';

function parseYamlFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  const yaml = match[1];
  const result = {};
  let currentKey = null;
  const lines = yaml.split('\n');

  for (const line of lines) {
    const kvMatch = line.match(/^(\S[\w-]+):\s*(.*)$/);
    if (kvMatch) {
      currentKey = kvMatch[1];
      const value = kvMatch[2].trim();
      if (value === '' || value === '""') {
        result[currentKey] = '';
      } else if (value.startsWith('"') && value.endsWith('"')) {
        result[currentKey] = value.slice(1, -1);
      } else {
        result[currentKey] = value;
      }
    } else if (currentKey && line.match(/^\s+-\s+"(#[0-9a-fA-F]{6})"/)) {
      const hexMatch = line.match(/"(#[0-9a-fA-F]{6})"/);
      if (hexMatch) {
        if (!Array.isArray(result[currentKey])) result[currentKey] = [];
        result[currentKey].push(hexMatch[1]);
      }
    }
  }

  return result;
}

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return [r, g, b];
}

/**
 * Create a minimal 16x1 PNG with the palette colors.
 * Uses raw PNG encoding (no dependencies).
 */
function createPalettePng(hexColors) {
  const width = hexColors.length;
  const height = 1;

  // Raw pixel data: filter byte + RGB per pixel
  const rawData = Buffer.alloc((1 + width * 3) * height);
  rawData[0] = 0; // filter: none

  for (let i = 0; i < hexColors.length; i++) {
    const [r, g, b] = hexToRgb(hexColors[i]);
    rawData[1 + i * 3] = r;
    rawData[2 + i * 3] = g;
    rawData[3 + i * 3] = b;
  }

  // Deflate the raw data (use zlib)
  const { deflateSync } = await import('zlib');
  const compressed = deflateSync(rawData);

  // Build PNG file
  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 2; // color type: RGB
  ihdr[10] = 0; // compression
  ihdr[11] = 0; // filter
  ihdr[12] = 0; // interlace

  const chunks = [
    createChunk('IHDR', ihdr),
    createChunk('IDAT', compressed),
    createChunk('IEND', Buffer.alloc(0)),
  ];

  return Buffer.concat([signature, ...chunks]);
}

function createChunk(type, data) {
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);

  const typeBuffer = Buffer.from(type, 'ascii');

  const { crc32 } = await import('zlib');
  // Simple CRC32
  const crcData = Buffer.concat([typeBuffer, data]);
  const crcValue = crc32Compute(crcData);
  const crcBuffer = Buffer.alloc(4);
  crcBuffer.writeUInt32BE(crcValue >>> 0);

  return Buffer.concat([length, typeBuffer, data, crcBuffer]);
}

function crc32Compute(buf) {
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i++) {
    crc ^= buf[i];
    for (let j = 0; j < 8; j++) {
      crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

// Main
mkdirSync(OUTPUT_DIR, { recursive: true });

const locationFiles = globSync(join(VAULT_DIR, '*.md'));
const generated = [];

for (const file of locationFiles) {
  const content = readFileSync(file, 'utf-8');
  const fm = parseYamlFrontmatter(content);

  if (!fm.palette || !fm['palette-hex'] || !Array.isArray(fm['palette-hex'])) {
    console.log(`Skipping ${basename(file)}: no palette-hex`);
    continue;
  }

  const outName = `${fm.palette}.png`;
  const outPath = join(OUTPUT_DIR, outName);

  // Skip if already generated (same palette used by multiple locations)
  if (generated.includes(fm.palette)) {
    console.log(`Skipping ${basename(file)}: palette ${fm.palette} already generated`);
    continue;
  }

  console.log(`${basename(file)} → ${outName} (${fm['palette-hex'].length} colors)`);
  generated.push(fm.palette);

  // For now, output a hex list file (PNG generation needs sharp or manual encoding)
  const hexList = fm['palette-hex'].join('\n');
  writeFileSync(join(OUTPUT_DIR, `${fm.palette}.hex`), hexList + '\n');
}

console.log(`Generated ${generated.length} palette files in ${OUTPUT_DIR}`);
