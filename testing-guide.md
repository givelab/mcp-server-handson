# テスト・検証ガイド

---

## テスト戦略の全体像

```
┌─────────────────────────────────────────┐
│              テストピラミッド              │
│                                         │
│          ┌─────────────┐               │
│          │  E2E テスト  │  少数・低速     │
│          │  (Claude連携) │               │
│        ┌─┴─────────────┴─┐             │
│        │  統合テスト       │  中数・中速   │
│        │  (実API / モック) │             │
│      ┌─┴─────────────────┴─┐           │
│      │    ユニットテスト      │  多数・高速 │
│      │   (ハンドラロジック)   │           │
│      └─────────────────────┘           │
└─────────────────────────────────────────┘
```

---

## ユニットテスト（pytest）

### セットアップ

```bash
pip install pytest pytest-asyncio
```

`pytest.ini` または `pyproject.toml` に追加：
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### 基本的なハンドラテスト

```python
# test_handler.py
import pytest
from handler import dispatch_tool

@pytest.mark.asyncio
async def test_add():
    result = await dispatch_tool("add", {"a": 3, "b": 4})
    assert result[0].text == "7"

@pytest.mark.asyncio
async def test_unknown_tool():
    with pytest.raises(ValueError, match="Unknown tool"):
        await dispatch_tool("nonexistent", {})
```

### モックを使ったテスト

```python
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_slack(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("handler._slack", mock)
    return mock

@pytest.mark.asyncio
async def test_send_message(mock_slack):
    mock_slack.send_message.return_value = "1234567890.000001"
    from handler import handle_send_message
    result = await handle_send_message("#general", "hello")
    assert "1234567890.000001" in result[0].text
```

### HTTP APIのモック（respx）

```bash
pip install respx
```

```python
import respx
import httpx

@pytest.mark.asyncio
@respx.mock
async def test_github_api():
    respx.get("https://api.github.com/repos/test/repo/issues").mock(
        return_value=httpx.Response(200, json=[
            {"number": 1, "title": "Test Issue", "state": "open"}
        ])
    )
    from services.github_service import GitHubService
    service = GitHubService()
    result = await service.dispatch("github_list_issues", {"owner": "test", "repo": "repo"})
    assert "#1" in result[0].text
```

---

## テスト実行コマンド

```bash
# すべてのテストを実行
pytest

# 詳細表示
pytest -v

# 特定ファイルのみ
pytest tests/test_handler.py

# 特定のテストのみ
pytest tests/test_handler.py::test_send_message -v

# 失敗時に即終了
pytest -x

# カバレッジ付きで実行
pip install pytest-cov
pytest --cov=. --cov-report=term-missing
```

---

## MCP Inspector を使った手動テスト

```bash
npx @modelcontextprotocol/inspector python server.py
```

1. ブラウザで `http://localhost:5173` を開く
2. 左サイドバーの "Tools" タブで利用可能なツールを確認
3. 各ツールをクリックして引数を入力し "Call Tool" を押す
4. レスポンスのJSONを確認

---

## stdio 直接テスト

```bash
# initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' | python server.py

# tools/list（複数行を送る）
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n' | python server.py

# tools/call (add)
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"add","arguments":{"a":3,"b":4}}}\n' | python server.py
```

---

## 統合テスト（実サービス接続）

実際のトークンが必要なテストは `skipif` で条件付きスキップ：

```python
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("SLACK_BOT_TOKEN"),
    reason="SLACK_BOT_TOKEN が未設定"
)

@pytest.mark.asyncio
async def test_real_slack():
    from handler import handle_send_message
    result = await handle_send_message("#test-channel", "統合テスト")
    assert "送信完了" in result[0].text
```

実行方法：
```bash
# .env を読み込んで実行
source .env && pytest tests/test_integration.py -v
```

---

## E2Eテスト（Claude連携）

Claude Desktop またはスクリプトで動作確認します。

### テストシナリオ例

**課題1（基本計算）**:
```
Claude: 「3と7を足して」
期待: 10 が返ってくる
```

**課題2（Slack）**:
```
Claude: 「#generalに『テスト完了』と送って」
期待: Slackにメッセージが届く
```

**課題3（マルチサービス）**:
```
Claude: 「GitHubのfacebook/reactリポジトリの最新Issueを3件取得して、Notionにまとめて記録して」
期待: GitHub → Notion の連携が動作する
```

---

## CI/CD への組み込み（GitHub Actions）

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --ignore=tests/test_integration.py
        # 統合テストはシークレットがないためスキップ
```
