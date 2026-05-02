# MCPプロトコル仕様要約

> Model Context Protocol (MCP) — 2024-11-05 版

---

## 通信レイヤー

| 項目 | 仕様 |
|------|------|
| ベースプロトコル | JSON-RPC 2.0 |
| トランスポート | stdio（ローカル）/ HTTP+SSE（リモート） |
| エンコーディング | UTF-8 |
| メッセージ区切り | 改行（`\n`） |

---

## メッセージタイプ

### リクエスト（`id` あり）
```json
{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {...}}
```

### レスポンス（成功）
```json
{"jsonrpc": "2.0", "id": 1, "result": {...}}
```

### レスポンス（エラー）
```json
{"jsonrpc": "2.0", "id": 1, "error": {"code": -32600, "message": "..."}}
```

### 通知（`id` なし、レスポンス不要）
```json
{"jsonrpc": "2.0", "method": "notifications/tools/list_changed"}
```

---

## ライフサイクルメソッド

| メソッド | 方向 | 必須 | 説明 |
|----------|------|------|------|
| `initialize` | Client→Server | ✅ | プロトコルバージョン交換 |
| `initialized` | Client→Server | ✅ | 初期化完了通知 |
| `shutdown` | Client→Server | — | 接続終了要求 |
| `ping` | 双方向 | — | 生存確認 |

---

## ツール関連メソッド

| メソッド | 説明 |
|----------|------|
| `tools/list` | 利用可能なツール一覧を返す |
| `tools/call` | ツールを実行して結果を返す |
| `notifications/tools/list_changed` | ツールリスト変更を通知（Server→Client） |

### tools/list レスポンス
```json
{
  "tools": [
    {
      "name": "tool_name",
      "description": "ツールの説明",
      "inputSchema": {
        "type": "object",
        "properties": {
          "param1": {"type": "string", "description": "説明"}
        },
        "required": ["param1"]
      }
    }
  ]
}
```

### tools/call レスポンス（成功）
```json
{
  "content": [
    {"type": "text", "text": "結果テキスト"}
  ],
  "isError": false
}
```

### tools/call レスポンス（エラー）
```json
{
  "content": [
    {"type": "text", "text": "エラーの詳細"}
  ],
  "isError": true
}
```

---

## リソース関連メソッド（オプション）

| メソッド | 説明 |
|----------|------|
| `resources/list` | リソース一覧を返す |
| `resources/read` | リソースを読み取る |
| `resources/subscribe` | リソース変更を購読 |

---

## コンテンツタイプ

| タイプ | 説明 | フィールド |
|--------|------|-----------|
| `text` | テキストコンテンツ | `text: string` |
| `image` | 画像（Base64） | `data: string`, `mimeType: string` |
| `resource` | 埋め込みリソース | `uri: string` |

---

## エラーコード

| コード | 定数名 | 意味 |
|--------|--------|------|
| -32700 | ParseError | JSONパース失敗 |
| -32600 | InvalidRequest | リクエスト形式不正 |
| -32601 | MethodNotFound | 存在しないメソッド |
| -32602 | InvalidParams | パラメータ不正 |
| -32603 | InternalError | サーバ内部エラー |
| -32000〜-32099 | ServerError | カスタムサーバエラー |

---

## Capability ネゴシエーション

`initialize` で双方のCapabilityを交換します。

**クライアントのCapability例**：
```json
{
  "capabilities": {
    "roots": {"listChanged": true},
    "sampling": {}
  }
}
```

**サーバのCapability例**：
```json
{
  "capabilities": {
    "tools": {"listChanged": false},
    "resources": {"subscribe": false, "listChanged": false},
    "prompts": {"listChanged": false},
    "logging": {}
  }
}
```

---

## 参考リンク

- 公式仕様: https://spec.modelcontextprotocol.io/
- Python SDK: https://github.com/modelcontextprotocol/python-sdk
- TypeScript SDK: https://github.com/modelcontextprotocol/typescript-sdk
- MCP Inspector: `npx @modelcontextprotocol/inspector`
