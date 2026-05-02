# デバッグ Tips

---

## 1. MCP Inspector で視覚的にデバッグ

```bash
npx @modelcontextprotocol/inspector python server.py
```

ブラウザで `http://localhost:5173` を開き、以下が確認できます：
- 利用可能なツール一覧
- ツール呼び出しのリクエスト/レスポンス
- エラーの詳細

---

## 2. stdio メッセージをファイルに記録する

```bash
python server.py 2>debug.log
```

または Python 側でログを stderr に出す：
```python
import sys
import json

def debug(msg):
    print(json.dumps({"debug": msg}), file=sys.stderr, flush=True)
```

> **注意**: stdout は MCP 通信に使うので、デバッグ出力は必ず stderr へ。

---

## 3. よくあるエラーと対処

### `ModuleNotFoundError: No module named 'mcp'`
```bash
pip install mcp
# または
uv add mcp
```

### `SLACK_BOT_TOKEN が設定されていません`
```bash
cp .env.example .env
# .env を編集してトークンを設定
source .env  # または load_dotenv() をコード先頭に追加
```

### `channel_not_found`
- `#channel-name` の先頭 `#` を忘れていないか確認
- ボットをチャンネルに招待しているか確認（`/invite @bot-name`）

### `initialize` に応答しない
- サーバが起動しているか確認（`python server.py` を直接実行）
- JSON の改行区切りが正しいか確認（各メッセージは1行）

### `tools/call` が `{"error": {"code": -32601}}` を返す
- `method` が `tools/call` になっているか（`tool/call` ではない）
- `params.name` にツール名が入っているか確認

---

## 4. Claude Desktop の接続確認

ログファイルの場所：
- macOS: `~/Library/Logs/Claude/mcp*.log`
- Windows: `%APPDATA%\Claude\logs\mcp*.log`

よくあるエラー：
```
Error: spawn python ENOENT
```
→ `python` が PATH に入っていない。絶対パスを使う：
```json
{"command": "/usr/bin/python3", "args": ["server.py"]}
```

---

## 5. Python デバッガで止める

```python
import asyncio

async def call_tool(name: str, arguments: dict):
    import pdb; pdb.set_trace()  # ← ここで止まる
    ...
```

ただし stdio サーバでは pdb が stdin を奪うため、
代わりにファイルにダンプする方が安全：

```python
import json, pathlib

def dump_debug(data: dict, filename: str = "/tmp/mcp_debug.json"):
    pathlib.Path(filename).write_text(json.dumps(data, indent=2, ensure_ascii=False))
```

---

## 6. テスト実行時のデバッグ

```bash
# 詳細出力で実行
pytest -v -s

# 特定のテストだけ実行
pytest tests/test_handler.py::test_send_message_success -v

# 失敗時に即座に止める
pytest -x

# print の出力を表示
pytest -s
```
