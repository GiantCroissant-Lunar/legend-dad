import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { connectMockGodot } from "./helpers/mock-godot.js";
import { startTestServer } from "./helpers/test-server.js";

const HEADERS = {
	"Content-Type": "application/json",
	Accept: "application/json, text/event-stream",
};

let server;
let mockGodot;
let sessionId = null;

/** Parse SSE response body into JSON-RPC result */
function parseSSE(body) {
	for (const line of body.split("\n")) {
		if (line.startsWith("data: ")) {
			return JSON.parse(line.slice(6));
		}
	}
	return JSON.parse(body);
}

async function mcpRequest(method, params = {}, id = 1) {
	const headers = { ...HEADERS };
	if (sessionId) headers["mcp-session-id"] = sessionId;

	const res = await fetch(server.mcpUrl, {
		method: "POST",
		headers,
		body: JSON.stringify({ jsonrpc: "2.0", id, method, params }),
	});

	const sid = res.headers.get("mcp-session-id");
	if (sid) sessionId = sid;

	const text = await res.text();
	return { status: res.status, body: parseSSE(text), raw: text };
}

function sleep(ms) {
	return new Promise((r) => setTimeout(r, ms));
}

beforeAll(async () => {
	server = await startTestServer();
	mockGodot = await connectMockGodot(server.port);
	await sleep(500); // Wait for handshake
});

afterAll(async () => {
	mockGodot?.close();
	await server?.cleanup();
});

describe("MCP Initialize", () => {
	it("returns server info and tools capability", async () => {
		const init = await mcpRequest("initialize", {
			protocolVersion: "2025-03-26",
			capabilities: {},
			clientInfo: { name: "test-mcp", version: "0.1.0" },
		});

		expect(init.status).toBe(200);
		expect(init.body.result.serverInfo.name).toBe("Legend Dad Game Server");
		expect(init.body.result.capabilities.tools).toBeDefined();

		// Send initialized notification
		await fetch(server.mcpUrl, {
			method: "POST",
			headers: { ...HEADERS, "mcp-session-id": sessionId },
			body: JSON.stringify({
				jsonrpc: "2.0",
				method: "notifications/initialized",
			}),
		});
		await sleep(200);
	});
});

describe("MCP tools/list", () => {
	it("returns all 5 tools", async () => {
		const tools = await mcpRequest("tools/list", {}, 2);

		expect(tools.status).toBe(200);
		const toolNames = tools.body.result.tools.map((t) => t.name).sort();
		expect(toolNames).toEqual([
			"get_state",
			"interact",
			"move",
			"poll_events",
			"switch_era",
		]);
	});
});

describe("MCP tool calls", () => {
	it("get_state returns game state with FATHER era", async () => {
		const state = await mcpRequest(
			"tools/call",
			{ name: "get_state", arguments: {} },
			3,
		);

		expect(state.status).toBe(200);
		const data = JSON.parse(state.body.result.content[0].text);
		expect(data.state).toBeDefined();
		expect(data.state.active_era).toBe("FATHER");
	});

	it("move returns success", async () => {
		const move = await mcpRequest(
			"tools/call",
			{ name: "move", arguments: { direction: "right" } },
			4,
		);

		expect(move.status).toBe(200);
		const data = JSON.parse(move.body.result.content[0].text);
		expect(data.success).toBe(true);
	});

	it("poll_events returns events after move", async () => {
		await sleep(300); // Wait for event propagation

		const poll = await mcpRequest(
			"tools/call",
			{ name: "poll_events", arguments: {} },
			5,
		);

		expect(poll.status).toBe(200);
		const data = JSON.parse(poll.body.result.content[0].text);
		expect(data.count).toBeGreaterThan(0);
		expect(data.events.some((e) => e.event === "entity_updated")).toBe(true);
	});

	it("poll_events drains queue (second call empty)", async () => {
		const poll = await mcpRequest(
			"tools/call",
			{ name: "poll_events", arguments: {} },
			6,
		);

		const data = JSON.parse(poll.body.result.content[0].text);
		expect(data.count).toBe(0);
	});
});
