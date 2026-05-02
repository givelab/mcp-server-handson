# 課題1：基本的なMCP Serverを実装

**難度**：初級 | **実装時間**：30〜40分 | **ファイル数**：5

---

## 目標

MCPプロトコルの基本的なライフサイクルを理解し、2数の加算を行うシンプルなツールを持つMCPサーバを実装する。

---

## 課題背景

MCPサーバを初めて作る際、プロトコルの「お作法」を理解することが最重要です。`initialize → tools/list → tools/call` の3ステップを実際に実装することで、MCP通信の仕組みを体で覚えましょう。

---

## 作成するファイル

```
solution-01/
├── mcp_server.py        # MCPサーバ本体
├── handler.py           # ツールのロジック
├── requirements.txt     # 依存パッケージ
├── test_mcp.py          # pytestによるテスト
└── .env.example         # 環境変数サンプル
```

---

## 要件

### 機能要件

1. **MCPサーバとして起動できること**
   - `python mcp_server.py` で起動する
   - 標準入出力（stdio）で通信する

2. **`initialize` メソッドに応答すること**
   - `protocolVersion: "2024-11-05"` を返す
   - `serverInfo.name: "calculator-mcp"` を返す

3. **`tools/list` で `add` ツールを返すこと**
   - ツール名: `add`
   - 説明: 2つの数値を加算して返す
   - パラメータ: `a`（number, 必須）、`b`（number, 必須）

4. **`tools/call` で `add` を実行できること**
   - `a + b` の結果をテキストで返す
   - 結果は `isError: false` で返す

5. **存在しないツールを呼んだ場合はエラーを返すこと**
   - `code: -32601`、`message: "Tool not found"` を返す

### テスト要件

- `test_add_positive()` — 正の数の加算
- `test_add_negative()` — 負の数を含む加算
- `test_add_float()` — 小数の加算
- `test_unknown_tool()` — 存在しないツールの呼び出し

---

## ステップバイステップガイド

### Step 1：プロジェクトをセットアップする

```bash
mkdir solution-01 && cd solution-01
python -m venv .venv
source .venv/bin/activate
pip install mcp pytest pytest-asyncio
pip freeze > requirements.txt
```

### Step 2：handler.py を作る

ツールのビジネスロジックをサーバコードから分離します。

```python
# handler.py の骨格
from mcp import types

async def handle_add(a: float, b: float) -> list[types.TextContent]:
    # ここを実装してください
    pass

async def dispatch_tool(name: str, arguments: dict) -> list[types.TextContent]:
    # ツール名に応じてハンドラを呼び出す
    # 存在しないツールの場合は ValueError を raise する
    pass
```

### Step 3：mcp_server.py を作る

```python
# mcp_server.py の骨格
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import asyncio
from handler import dispatch_tool

app = Server("calculator-mcp")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    # ツール一覧を返す
    pass

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    # dispatch_tool を呼び出す
    pass

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4：test_mcp.py を作る

```python
# test_mcp.py の骨格
import pytest
from handler import dispatch_tool, handle_add

@pytest.mark.asyncio
async def test_add_positive():
    result = await handle_add(3, 4)
    # result[0].text が "7" であることをアサート

@pytest.mark.asyncio
async def test_add_negative():
    # -5 + 3 = -2 をテスト
    pass

@pytest.mark.asyncio
async def test_add_float():
    # 1.5 + 2.5 = 4.0 をテスト
    pass

@pytest.mark.asyncio
async def test_unknown_tool():
    # "nonexistent" ツールで ValueError が発生することをテスト
    pass
```

### Step 5：動作確認

```bash
# テストを実行
pytest test_mcp.py -v

# MCPサーバを手動テスト（別ターミナル）
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' | python mcp_server.py
```

---

## チェックポイント

- [ ] `pip install mcp` が成功している
- [ ] `python mcp_server.py` を起動して `initialize` リクエストに応答できる
- [ ] `tools/list` で `add` ツールが返ってくる
- [ ] `tools/call` で `add(3, 4)` → `"7"` が返ってくる
- [ ] `pytest` が全テストパスする

---

## 解答例

詰まったら `exercises/solutions/solution-01/` を参照してください。  
まず自分で実装してから確認することを強くお勧めします。

---

## 発展課題（時間が余った場合）

- `multiply(a, b)` — 掛け算ツールを追加する
- `divide(a, b)` — 割り算ツールを追加する（ゼロ除算エラーのハンドリングも）
- Claude Desktop に接続して動作確認する
