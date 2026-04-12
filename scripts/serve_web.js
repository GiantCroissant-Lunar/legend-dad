#!/usr/bin/env node
/**
 * Static file server for Godot web exports.
 * Sets Cross-Origin-Opener-Policy and Cross-Origin-Embedder-Policy headers
 * required for SharedArrayBuffer support (needed by Godot WASM).
 */

import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, resolve } from "node:path";

const PORT = Number.parseInt(process.env.SERVE_PORT || "8080", 10);
const ROOT = resolve(process.argv[2] || "build/_artifacts/latest/web");

const MIME_TYPES = {
  ".html": "text/html",
  ".js": "application/javascript",
  ".wasm": "application/wasm",
  ".pck": "application/octet-stream",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".json": "application/json",
  ".css": "text/css",
};

const server = createServer(async (req, res) => {
  // COOP/COEP headers for SharedArrayBuffer
  res.setHeader("Cross-Origin-Opener-Policy", "same-origin");
  res.setHeader("Cross-Origin-Embedder-Policy", "require-corp");
  res.setHeader("Access-Control-Allow-Origin", "*");

  let filePath = join(ROOT, req.url === "/" ? "complete-app.html" : req.url);

  try {
    const fileStat = await stat(filePath);
    if (fileStat.isDirectory()) {
      filePath = join(filePath, "complete-app.html");
    }

    const data = await readFile(filePath);
    const ext = extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || "application/octet-stream";

    res.writeHead(200, { "Content-Type": contentType });
    res.end(data);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not found\n");
  }
});

server.listen(PORT, () => {
  console.log(`[serve] Godot web build at http://localhost:${PORT}`);
  console.log(`[serve] Root: ${ROOT}`);
  console.log("[serve] COOP/COEP headers enabled (SharedArrayBuffer support)");
});
