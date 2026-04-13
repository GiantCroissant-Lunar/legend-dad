import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { createGameAgent } from "../mastra/agent.js";
import { createMastraServer } from "../mastra/index.js";
import { connectMockGodot } from "./helpers/mock-godot.js";
import { startTestServer } from "./helpers/test-server.js";

const HAS_API_KEY = !!(process.env.ZAI_API_KEY || process.env.ALIBABA_API_KEY);

let server;
let mockGodot;

beforeAll(async () => {
	if (!HAS_API_KEY) return;
	server = await startTestServer();
	mockGodot = await connectMockGodot(server.port);
	// Wait for handshake + initial state
	await new Promise((r) => setTimeout(r, 1000));
});

afterAll(async () => {
	mockGodot?.close();
	await server?.cleanup();
});

describe.skipIf(!HAS_API_KEY)("Agent integration", () => {
	it("calls tools and receives game state", async () => {
		const providers = [
			{
				name: "zai",
				url: "https://api.z.ai/api/coding/paas/v4",
				apiKey: process.env.ZAI_API_KEY || "",
				model: process.env.ZAI_MODEL || "glm-5.1",
			},
			{
				name: "alibaba",
				url: "https://coding-intl.dashscope.aliyuncs.com/v1",
				apiKey: process.env.ALIBABA_API_KEY || "",
				model: process.env.ALIBABA_MODEL || "qwen3.5-plus",
			},
		];

		const { tools } = createMastraServer(server.connMgr, server.stateStore);

		const agent = await createGameAgent(tools, {
			providers,
			stateStore: server.stateStore,
		});

		const result = await agent.generate(
			"Get the current game state and tell me where the player is.",
			{ maxSteps: 5 },
		);

		expect(result.text).toBeTruthy();
		// Agent should have called at least one tool (LLM behavior is non-deterministic)
		const toolCalls = result.steps?.flatMap((s) => s.toolCalls || []) || [];
		expect(toolCalls.length).toBeGreaterThan(0);
	}, 30_000); // 30s timeout for LLM round-trip
});
