#!/usr/bin/env node
/**
 * Static file server for Godot web exports.
 * Sets Cross-Origin-Opener-Policy and Cross-Origin-Embedder-Policy headers
 * required for SharedArrayBuffer support (needed by Godot WASM).
 *
 * Supports HTTPS mode for cross-machine testing (Godot requires secure context).
 * Usage:
 *   node serve_web.js [root_dir]           # HTTP on :7601
 *   SERVE_HTTPS=1 node serve_web.js        # HTTPS on :8443 with self-signed cert
 */

import { createServer as createHttpServer } from "node:http";
import { createServer as createHttpsServer } from "node:https";
import { readFile, stat } from "node:fs/promises";
import { execSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { networkInterfaces } from "node:os";

// Repo root = parent of scripts/ — so paths inside the repo resolve the same
// no matter which cwd this script is invoked from (e.g. Playwright's
// webServer config runs it from project/server/packages/e2e).
const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const USE_HTTPS = process.env.SERVE_HTTPS === "1";
const PORT = Number.parseInt(process.env.SERVE_PORT || (USE_HTTPS ? "8443" : "7601"), 10);
const ROOT = resolve(process.argv[2] || join(REPO_ROOT, "build/_artifacts/latest/web"));
const CERT_DIR = join(REPO_ROOT, "build/_certs");
// Where `task content:build -- {id}` writes freshly-packed PCKs. We probe this
// as a fallback for `/pck/*.pck` misses so F9 hot-reload sees the rebuild
// output without having to pollute the engine-export snapshot under ROOT.
// Anchored to REPO_ROOT so it works regardless of invocation cwd (Playwright's
// webServer runs this from project/server/packages/e2e).
// See vault/dev-log/2026-04-15-f9-pck-404-root-cause.md.
const CONTENT_BUILD_PCK_DIR = join(REPO_ROOT, "build/_artifacts/pck");

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

function getLanIp() {
  const nets = networkInterfaces();
  for (const iface of Object.values(nets)) {
    for (const addr of iface) {
      if (addr.family === "IPv4" && !addr.internal) {
        return addr.address;
      }
    }
  }
  return "127.0.0.1";
}

function ensureCerts() {
  const keyPath = join(CERT_DIR, "key.pem");
  const certPath = join(CERT_DIR, "cert.pem");

  if (existsSync(keyPath) && existsSync(certPath)) {
    return { key: readFileSync(keyPath), cert: readFileSync(certPath) };
  }

  mkdirSync(CERT_DIR, { recursive: true });
  const lanIp = getLanIp();

  console.log(`[serve] Generating self-signed cert for localhost + ${lanIp}...`);
  execSync(
    `openssl req -x509 -newkey rsa:2048 -keyout "${keyPath}" -out "${certPath}" ` +
      `-days 365 -nodes -subj "/CN=localhost" ` +
      `-addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:${lanIp}"`,
    { stdio: "pipe" },
  );

  return { key: readFileSync(keyPath), cert: readFileSync(certPath) };
}

async function handler(req, res) {
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
    return;
  } catch {
    // Fall through — maybe the file lives in the content-build output dir.
  }

  // Fallback: `/pck/{name}.pck` requests that miss ROOT (engine-export
  // snapshot) are retried against build/_artifacts/pck/, where
  // `task content:build` writes freshly-packed bundles. This keeps the
  // versioned snapshot immutable while letting F9 hot-reload see rebuild
  // output without re-running the full web export.
  if (req.url.startsWith("/pck/") && req.url.endsWith(".pck")) {
    const pckName = req.url.slice("/pck/".length);
    const altPath = join(CONTENT_BUILD_PCK_DIR, pckName);
    try {
      const data = await readFile(altPath);
      res.writeHead(200, { "Content-Type": "application/octet-stream" });
      res.end(data);
      return;
    } catch {
      // Fall through to 404.
    }
  }

  res.writeHead(404, { "Content-Type": "text/plain" });
  res.end("Not found\n");
}

const lanIp = getLanIp();
const protocol = USE_HTTPS ? "https" : "http";

let server;
if (USE_HTTPS) {
  const certs = ensureCerts();
  server = createHttpsServer(certs, handler);
} else {
  server = createHttpServer(handler);
}

server.listen(PORT, "0.0.0.0", () => {
  console.log(`[serve] Godot web build at ${protocol}://localhost:${PORT}`);
  console.log(`[serve] LAN access: ${protocol}://${lanIp}:${PORT}`);
  console.log(`[serve] Root: ${ROOT}`);
  console.log(`[serve] /pck/ fallback: ${CONTENT_BUILD_PCK_DIR}`);
  console.log("[serve] COOP/COEP headers enabled (SharedArrayBuffer support)");
  if (USE_HTTPS) {
    console.log("[serve] HTTPS mode — accept the self-signed cert in your browser");
  }
});
