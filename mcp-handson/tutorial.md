# MCP Server 自作ハンズオン

> Slack / Notion / GitHub を Claude に自動連携させる MCP サーバを 0 から作る実践ガイド

---

## 第0章：はじめに

### MCPプロトコルとは何か

MCP（Model Context Protocol）は Anthropic が策定したオープン標準プロトコルです。Claude などの大規模言語モデル（LLM）が、外部ツールやデータソースと標準化された方法で通信できるようにします。

従来のアプローチでは、各サービス連携ごとにカスタムの統合コードを書く必要がありました。MCPはこの課題を解決します：

```
【従来】
Claude ←→ カスタムコード(Slack) 
Claude ←→ カスタムコード(Notion)
Claude ←→ カスタムコード(GitHub)
   ↑ それぞれ別々の実装が必要

【MCPあり】
Claude ←→ MCP Protocol ←→ MCP Server ←→ Slack/Notion/GitHub
              ↑ 統一インターフェース
```

### MCPの基本アーキテクチャ

```
┌─────────────┐    JSON-RPC 2.0    ┌─────────────┐
│  MCP Client │ ←────────────────→ │  MCP Server │
│  (Claude)   │   stdio / HTTP/SSE │  (あなたが  │
└─────────────┘                    │   作るもの) │
                                   └──────┬──────┘
                                          │
                              ┌───────────┼───────────┐
                              ↓           ↓           ↓
                           Slack API  Notion API  GitHub API
```

### Claudeとの連携の可能性

MCPを使うことで Claude は以下が可能になります：

- **情報収集**：GitHubのIssueやPRを取得、Notionのドキュメントを読む
- **操作実行**：Slackにメッセージを送る、GitHubにコミットする
- **ワークフロー自動化**：「このバグレポートをNotionに記録してSlackに通知して」

### このハンズオンで学べること

1. MCPプロトコルのリクエスト/レスポンス構造
2. Python での MCP サーバ実装
3. TypeScript での MCP クライアント実装
4. Slack / Notion / GitHub との実践的な連携
5. テスト・Docker化・本番デプロイ

---

## 第1章：MCPプロトコルの理解

### 1.1 JSON-RPC 2.0 ベースの通信

MCP は JSON-RPC 2.0 をトランスポート層として使います。

**リクエスト構造**：
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "send_slack_message",
    "arguments": {
      "channel": "#general",
      "message": "Hello from Claude!"
    }
  }
}
```

**レスポンス構造（成功時）**：
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "メッセージを送信しました。timestamp: 1234567890.123456"
      }
    ],
    "isError": false
  }
}
```

**レスポンス構造（エラー時）**：
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "channel が指定されていません"
  }
}
```

### 1.2 MCP のライフサイクル

```
1. initialize       → サーバの能力を確認
2. tools/list       → 利用可能なツール一覧を取得
3. tools/call       → ツールを実行
4. (resources/list) → リソース一覧（オプション）
5. shutdown         → 接続を終了
```

**initialize リクエスト**：
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "clientInfo": {
      "name": "claude-desktop",
      "version": "0.6.0"
    }
  }
}
```

**initialize レスポンス**：
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": { "listChanged": false }
    },
    "serverInfo": {
      "name": "my-mcp-server",
      "version": "1.0.0"
    }
  }
}
```

### 1.3 ツール定義とパラメータ

ツールは JSON Schema で定義します：

```json
{
  "name": "add_numbers",
  "description": "2つの数値を加算して結果を返す",
  "inputSchema": {
    "type": "object",
    "properties": {
      "a": {
        "type": "number",
        "description": "1つ目の数値"
      },
      "b": {
        "type": "number",
        "description": "2つ目の数値"
      }
    },
    "required": ["a", "b"]
  }
}
```

### 1.4 エラーコード体系

| コード | 意味 | 使用場面 |
|--------|------|---------|
| -32700 | Parse error | JSONパースに失敗 |
| -32600 | Invalid Request | リクエスト形式が不正 |
| -32601 | Method not found | 存在しないメソッド |
| -32602 | Invalid params | パラメータ不正 |
| -32603 | Internal error | サーバ内部エラー |
| -32000〜-32099 | Server error | カスタムエラー |

---

## 第2章：Python での MCP Server 実装基本

### 2.1 環境セットアップ

**必要なもの**：
- Python 3.11+
- pip / uv（パッケージ管理）

```bash
# プロジェクト作成
mkdir my-mcp-server && cd my-mcp-server

# 仮想環境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存パッケージ
pip install mcp anthropic python-dotenv
pip install pytest pytest-asyncio  # テスト用
```

**pyproject.toml**：
```toml
[project]
name = "my-mcp-server"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
    "anthropic>=0.40.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
mcp-server = "server:main"
```

### 2.2 最小限のMCPサーバ実装

`server.py`:
```python
import asyncio
import json
import sys
from typing import Any

# MCPの通信はstdioベース（標準入出力）
async def handle_request(request: dict) -> dict:
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "minimal-mcp", "version": "0.1.0"}
            }
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "add",
                        "description": "2数の加算",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "a": {"type": "number"},
                                "b": {"type": "number"}
                            },
                            "required": ["a", "b"]
                        }
                    }
                ]
            }
        }

    if method == "tools/call":
        tool_name = request["params"]["name"]
        args = request["params"]["arguments"]

        if tool_name == "add":
            result = args["a"] + args["b"]
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": str(result)}],
                    "isError": False
                }
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": "Method not found"}
    }

async def main():
    while True:
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        request = json.loads(line.strip())
        response = await handle_request(request)
        print(json.dumps(response), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.3 mcp ライブラリを使った実装（推奨）

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import asyncio

app = Server("my-server")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="add",
            description="2数の加算",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "1つ目"},
                    "b": {"type": "number", "description": "2つ目"}
                },
                "required": ["a", "b"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "add":
        result = arguments["a"] + arguments["b"]
        return [types.TextContent(type="text", text=str(result))]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.4 ローカルテスト方法

**方法1：直接実行してテスト**
```bash
# サーバを起動してリクエストを手動送信
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' | python server.py
```

**方法2：Claude Desktop で接続**

`~/.claude/claude_desktop_config.json`（macOS）または
`%APPDATA%\Claude\claude_desktop_config.json`（Windows）に追加：

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "SLACK_TOKEN": "xoxb-..."
      }
    }
  }
}
```

**方法3：MCP Inspector（GUI）**
```bash
npx @modelcontextprotocol/inspector python server.py
# ブラウザで http://localhost:5173 を開く
```

---

## 第3章：演習課題（全3課題）

### 課題1：基本的なMCP Serverを実装

**目標**：プラス計算の単純なツールを持つMCPサーバ  
**難度**：初級 | **実装時間**：30〜40分 | **ファイル数**：5

#### 課題背景

MCPプロトコルの基本的な流れを理解するため、最シンプルな計算ツールを実装します。`initialize → tools/list → tools/call` のライフサイクルを手を動かして体験してください。

#### 要件

- Python で MCP サーバを実装する
- 引数 `a`, `b` を受け取り合計を返す `add` ツールを定義する
- pytest でユニットテストを実装する
- MCP Inspector か Claude Desktop で動作確認する

#### ヒント（3段階）

- **Level 1**：`tools/list` レスポンスの `inputSchema` フィールドを JSON Schema 形式で書いてみてください
- **Level 2**：`call_tool` デコレータの戻り値の型は `list[types.TextContent]` です。`TextContent` の `text` フィールドに結果を入れてください
- **Level 3**：`types.TextContent(type="text", text=str(result))` を返せば完成です

#### 解答例

`exercises/solutions/solution-01/` に完全なコードがあります。

---

### 課題2：Slack統合MCPサーバ

**目標**：Slackのメッセージ送信・取得ツール  
**難度**：中級 | **実装時間**：1〜1.5時間 | **ファイル数**：10〜12

#### 課題背景

MCPサーバが実際の外部サービス（Slack）と連携するパターンを学びます。認証・APIコール・エラーハンドリングの実践的な実装を体験します。

#### 要件

- Slack Bot Token を環境変数で管理する
- `send_message(channel, message)` ツールを実装する
- `get_messages(channel, limit)` ツールを実装する
- API エラー（レート制限・認証失敗）を適切にハンドリングする

#### Slack Bot Token の取得方法

1. https://api.slack.com/apps → "Create New App"
2. "Bot Token Scopes" に `chat:write`, `channels:history` を追加
3. "Install App" → `xoxb-...` トークンをコピー
4. `.env` ファイルに `SLACK_BOT_TOKEN=xoxb-...` を記述

#### ヒント（3段階）

- **Level 1**：`python-dotenv` の `load_dotenv()` で `.env` を読み込み、`os.environ["SLACK_BOT_TOKEN"]` で取得できます
- **Level 2**：`slack_sdk` の `WebClient(token=...)` を使い、`client.chat_postMessage(channel=channel, text=message)` で送信できます
- **Level 3**：`slack_sdk.errors.SlackApiError` をキャッチし、`e.response["error"]` で Slack のエラーコードを取得してユーザーに返しましょう

#### 解答例

`exercises/solutions/solution-02/` に完全なコードがあります。

---

### 課題3：複数サービス対応MCPサーバ

**目標**：Slack + Notion + GitHub を単一 MCP サーバに統合  
**難度**：上級 | **実装時間**：2〜2.5時間 | **ファイル数**：15〜20

#### 課題背景

本番環境では複数サービスを1つのMCPサーバで管理することが多いです。モジュール設計・共通エラーハンドリング・フォールバック処理を実践します。

#### 要件

- `services/slack_service.py`、`services/notion_service.py`、`services/github_service.py` でサービスを分割
- 共通の `ServiceError` 例外クラスを作る
- 構造化ログ（JSON ログ）を実装する
- 1サービスが落ちても他のサービスは動き続ける設計にする

#### ヒント（3段階）

- **Level 1**：各 API のトークン取得方法を確認してください（Slack: `SLACK_BOT_TOKEN`, Notion: `NOTION_TOKEN`, GitHub: `GITHUB_TOKEN`）
- **Level 2**：各サービスクラスに `async def is_available() -> bool` メソッドを作り、ヘルスチェックを実装しましょう
- **Level 3**：`try/except ServiceError` でサービスエラーをキャッチし、`isError: True` を返すことで他サービスへの影響を防ぎます

#### 解答例

`exercises/solutions/solution-03/` に完全なコードがあります。

---

## 第4章：TypeScript での クライアント実装

### 4.1 MCPクライアントの基本構造

```typescript
import Anthropic from "@anthropic-ai/sdk";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

// MCPサーバに接続
const transport = new StdioClientTransport({
  command: "python",
  args: ["server.py"],
  env: { SLACK_BOT_TOKEN: process.env.SLACK_BOT_TOKEN! }
});

const mcpClient = new Client(
  { name: "my-client", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

await mcpClient.connect(transport);

// 利用可能なツールを取得
const { tools } = await mcpClient.listTools();
console.log("Available tools:", tools.map(t => t.name));
```

### 4.2 Anthropic API との統合

```typescript
const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// MCPのツール定義をAnthropic形式に変換
const anthropicTools = tools.map(tool => ({
  name: tool.name,
  description: tool.description,
  input_schema: tool.inputSchema as Anthropic.Tool["input_schema"]
}));

// Claudeにメッセージを送る
const response = await anthropic.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 1024,
  tools: anthropicTools,
  messages: [{ role: "user", content: "Slackの#generalに『ハンズオン完了！』と送って" }]
});

// ツール使用のハンドリング
for (const block of response.content) {
  if (block.type === "tool_use") {
    const result = await mcpClient.callTool({
      name: block.name,
      arguments: block.input as Record<string, unknown>
    });
    console.log("Tool result:", result.content);
  }
}
```

### 4.3 完全なエージェントループ

```typescript
async function agentLoop(userMessage: string) {
  const messages: Anthropic.MessageParam[] = [
    { role: "user", content: userMessage }
  ];

  while (true) {
    const response = await anthropic.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 4096,
      tools: anthropicTools,
      messages
    });

    if (response.stop_reason === "end_turn") {
      const textBlock = response.content.find(b => b.type === "text");
      return textBlock?.text ?? "";
    }

    if (response.stop_reason === "tool_use") {
      const toolResults: Anthropic.ToolResultBlockParam[] = [];

      for (const block of response.content) {
        if (block.type === "tool_use") {
          const result = await mcpClient.callTool({
            name: block.name,
            arguments: block.input as Record<string, unknown>
          });
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: result.content as string
          });
        }
      }

      messages.push({ role: "assistant", content: response.content });
      messages.push({ role: "user", content: toolResults });
    }
  }
}

// 使用例
const answer = await agentLoop("GitHubの最新Issueを3件取得してNotionに記録して");
console.log(answer);
```

### 4.4 デバッグ方法

```typescript
// 詳細ログを有効化
process.env.MCP_LOG_LEVEL = "debug";

// ツール呼び出しをインターセプトしてログ
const originalCallTool = mcpClient.callTool.bind(mcpClient);
mcpClient.callTool = async (params) => {
  console.log(`[TOOL CALL] ${params.name}`, JSON.stringify(params.arguments, null, 2));
  const result = await originalCallTool(params);
  console.log(`[TOOL RESULT] ${params.name}`, JSON.stringify(result.content, null, 2));
  return result;
};
```

---

## 第5章：テスト・デプロイメント

### 5.1 ユニットテスト（pytest）

```python
# test_tools.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from server import call_tool

@pytest.mark.asyncio
async def test_add_tool():
    result = await call_tool("add", {"a": 3, "b": 4})
    assert result[0].text == "7"

@pytest.mark.asyncio
async def test_add_tool_negative():
    result = await call_tool("add", {"a": -5, "b": 3})
    assert result[0].text == "-2"

@pytest.mark.asyncio
async def test_unknown_tool():
    with pytest.raises(ValueError, match="Unknown tool"):
        await call_tool("nonexistent", {})
```

### 5.2 Slack API のモックテスト

```python
@pytest.mark.asyncio
async def test_send_slack_message():
    with patch("slack_sdk.WebClient.chat_postMessage") as mock_post:
        mock_post.return_value = {
            "ok": True,
            "ts": "1234567890.123456"
        }
        result = await call_tool("send_message", {
            "channel": "#test",
            "message": "Hello"
        })
    assert "1234567890.123456" in result[0].text
    mock_post.assert_called_once_with(channel="#test", text="Hello")
```

### 5.3 Docker化

`Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 環境変数は実行時に渡す（ビルド時に埋め込まない）
ENV PYTHONUNBUFFERED=1

CMD ["python", "server.py"]
```

`docker-compose.yml`:
```yaml
version: "3.9"
services:
  mcp-server:
    build: .
    stdin_open: true
    tty: true
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

### 5.4 本番環境への展開

**Claude Desktop + ローカルサーバ（最もシンプル）**：
```json
{
  "mcpServers": {
    "production-server": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--env-file", "/path/to/.env", "my-mcp-server:latest"]
    }
  }
}
```

**systemd サービスとして常駐（Linux）**：
```ini
[Unit]
Description=MCP Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/mcp-server
EnvironmentFile=/opt/mcp-server/.env
ExecStart=/opt/mcp-server/.venv/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## ベストプラクティス

### 認証情報の管理

```python
# ❌ NG：コードに直接書く
SLACK_TOKEN = "xoxb-..."

# ✅ OK：環境変数から取得
import os
from dotenv import load_dotenv

load_dotenv()  # .envファイルを読み込む
SLACK_TOKEN = os.environ["SLACK_BOT_TOKEN"]  # 未設定なら起動時にエラー
```

`.gitignore` に必ず追加：
```
.env
*.env.local
__pycache__/
.venv/
```

### パフォーマンス最適化

```python
# ❌ NG：毎回クライアントを生成
async def call_tool(name, args):
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    return client.chat_postMessage(...)

# ✅ OK：クライアントをシングルトンで持つ
_slack_client: WebClient | None = None

def get_slack_client() -> WebClient:
    global _slack_client
    if _slack_client is None:
        _slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    return _slack_client
```

### セキュリティ考慮事項

1. **入力バリデーション**：Claude から渡された引数を信頼しない
   ```python
   def validate_channel(channel: str) -> str:
       if not channel.startswith("#"):
           raise ValueError("channel は # で始まる必要があります")
       if len(channel) > 80:
           raise ValueError("channel 名が長すぎます")
       return channel
   ```

2. **レート制限への対応**：
   ```python
   import time

   async def send_with_retry(client, channel, message, max_retries=3):
       for attempt in range(max_retries):
           try:
               return client.chat_postMessage(channel=channel, text=message)
           except SlackApiError as e:
               if e.response["error"] == "ratelimited":
                   retry_after = int(e.response.headers.get("Retry-After", 60))
                   await asyncio.sleep(retry_after)
               else:
                   raise
       raise RuntimeError("最大リトライ回数を超えました")
   ```

3. **ログに機密情報を出力しない**：
   ```python
   # ❌ NG
   logger.info(f"Slack token: {token}")

   # ✅ OK
   logger.info("Slack client initialized", extra={"token_prefix": token[:10] + "..."})
   ```
