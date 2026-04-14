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
import { extname, join, resolve } from "node:path";
import { networkInterfaces } from "node:os";

const USE_HTTPS = process.env.SERVE_HTTPS === "1";
const PORT = Number.parseInt(process.env.SERVE_PORT || (USE_HTTPS ? "8443" : "7601"), 10);
const ROOT = resolve(process.argv[2] || "build/_artifacts/latest/web");
const CERT_DIR = resolve("build/_certs");

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
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not found\n");
  }
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
  console.log("[serve] COOP/COEP headers enabled (SharedArrayBuffer support)");
  if (USE_HTTPS) {
    console.log("[serve] HTTPS mode — accept the self-signed cert in your browser");
  }
});
