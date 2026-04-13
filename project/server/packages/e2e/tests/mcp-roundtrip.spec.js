import { expect, test } from "@playwright/test";

const MCP_URL = "http://localhost:3000/mcp";
const MCP_HEADERS = {
	"Content-Type": "application/json",
	Accept: "application/json, text/event-stream",
};

/** Parse SSE response body into JSON-RPC result */
function parseSSE(body) {
	for (const line of body.split("\n")) {
		if (line.startsWith("data: ")) {
			return JSON.parse(line.slice(6));
		}
	}
	return JSON.parse(body);
}

test.describe("MCP round-trip with live Godot", () => {
	let sessionId = null;

	test.beforeAll(async ({ request }) => {
		// Initialize MCP session
		const res = await request.post(MCP_URL, {
			headers: MCP_HEADERS,
			data: {
				jsonrpc: "2.0",
				id: 1,
				method: "initialize",
				params: {
					protocolVersion: "2025-03-26",
					capabilities: {},
					clientInfo: { name: "e2e-test", version: "0.1.0" },
				},
			},
		});

		expect(res.status()).toBe(200);
		sessionId = res.headers()["mcp-session-id"];

		// Send initialized notification
		await request.post(MCP_URL, {
			headers: { ...MCP_HEADERS, "mcp-session-id": sessionId },
			data: {
				jsonrpc: "2.0",
				method: "notifications/initialized",
			},
		});
	});

	test("Godot is connected and MCP lists tools", async ({ page, request }) => {
		// First verify Godot is loaded in browser
		await page.goto("/");
		const canvas = page.locator("canvas");
		await expect(canvas).toBeVisible({ timeout: 30_000 });

		// List MCP tools
		const res = await request.post(MCP_URL, {
			headers: { ...MCP_HEADERS, "mcp-session-id": sessionId },
			data: { jsonrpc: "2.0", id: 2, method: "tools/list", params: {} },
		});

		expect(res.status()).toBe(200);
		const body = parseSSE(await res.text());
		const toolNames = body.result.tools.map((t) => t.name).sort();
		expect(toolNames).toContain("move");
		expect(toolNames).toContain("get_state");
	});

	test("MCP get_state reflects live game", async ({ page, request }) => {
		await page.goto("/");
		const canvas = page.locator("canvas");
		await expect(canvas).toBeVisible({ timeout: 30_000 });

		// Wait for WS connection + state sync
		await page.waitForTimeout(2000);

		const res = await request.post(MCP_URL, {
			headers: { ...MCP_HEADERS, "mcp-session-id": sessionId },
			data: {
				jsonrpc: "2.0",
				id: 3,
				method: "tools/call",
				params: { name: "get_state", arguments: {} },
			},
		});

		expect(res.status()).toBe(200);
		const body = parseSSE(await res.text());
		const data = JSON.parse(body.result.content[0].text);
		expect(data.state).toBeDefined();
		expect(data.state.active_era).toBeDefined();
	});
});
