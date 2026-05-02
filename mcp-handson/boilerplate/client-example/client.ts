import Anthropic from "@anthropic-ai/sdk";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY! });

async function createMcpClient(): Promise<Client> {
  const transport = new StdioClientTransport({
    command: "python",
    args: ["server.py"],
    env: {
      ...process.env,
      SLACK_BOT_TOKEN: process.env.SLACK_BOT_TOKEN ?? "",
    } as Record<string, string>,
  });

  const client = new Client(
    { name: "mcp-client-example", version: "1.0.0" },
    { capabilities: { tools: {} } }
  );

  await client.connect(transport);
  return client;
}

async function agentLoop(mcpClient: Client, userMessage: string): Promise<string> {
  const { tools } = await mcpClient.listTools();

  const anthropicTools: Anthropic.Tool[] = tools.map((tool) => ({
    name: tool.name,
    description: tool.description ?? "",
    input_schema: tool.inputSchema as Anthropic.Tool["input_schema"],
  }));

  const messages: Anthropic.MessageParam[] = [
    { role: "user", content: userMessage },
  ];

  while (true) {
    const response = await anthropic.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 4096,
      tools: anthropicTools,
      messages,
    });

    if (response.stop_reason === "end_turn") {
      const textBlock = response.content.find((b) => b.type === "text");
      return textBlock?.type === "text" ? textBlock.text : "";
    }

    if (response.stop_reason === "tool_use") {
      const toolResults: Anthropic.ToolResultBlockParam[] = [];

      for (const block of response.content) {
        if (block.type === "tool_use") {
          console.log(`[TOOL] ${block.name}`, JSON.stringify(block.input, null, 2));

          const result = await mcpClient.callTool({
            name: block.name,
            arguments: block.input as Record<string, unknown>,
          });

          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: Array.isArray(result.content)
              ? result.content.map((c: { text?: string }) => c.text ?? "").join("\n")
              : String(result.content),
          });
        }
      }

      messages.push({ role: "assistant", content: response.content });
      messages.push({ role: "user", content: toolResults });
    }
  }
}

async function main() {
  const mcpClient = await createMcpClient();
  const { tools } = await mcpClient.listTools();
  console.log("利用可能なツール:", tools.map((t) => t.name).join(", "));

  const answer = await agentLoop(mcpClient, "GitHubのantropic/claude-codeリポジトリの最新Issue3件を取得して");
  console.log("\n=== Claudeの回答 ===");
  console.log(answer);

  process.exit(0);
}

main().catch(console.error);
