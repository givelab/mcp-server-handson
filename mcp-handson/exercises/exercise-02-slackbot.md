# 課題2：Slack統合MCPサーバ

**難度**：中級 | **実装時間**：1〜1.5時間 | **ファイル数**：10〜12

---

## 目標

Slackとリアルタイム連携できるMCPサーバを実装する。メッセージ送信・取得・チャンネル一覧取得の3つのツールを持つ。

---

## 課題背景

課題1ではプロトコルの基礎を学びました。本課題では外部APIとの認証・通信・エラーハンドリングを実践します。Slackという実際のサービスに接続することで「本物のMCPサーバ」を体験します。

---

## 作成するファイル

```
solution-02/
├── slack_integration.py      # Slackクライアントのラッパー
├── handler.py                # MCPツールハンドラ
├── server.py                 # MCPサーバエントリポイント
├── requirements.txt
├── .env.example
└── tests/
    ├── test_handler.py       # ハンドラのユニットテスト（モック使用）
    ├── test_integration.py   # 統合テスト（実Slack APIを使用）
    └── conftest.py           # pytest設定・フィクスチャ
```

---

## Slack Bot の準備

### 1. Slack App の作成

1. https://api.slack.com/apps にアクセス
2. "Create New App" → "From scratch"
3. App名を入力（例：`claude-mcp-bot`）、ワークスペースを選択

### 2. Bot Token Scopes の設定

"OAuth & Permissions" → "Bot Token Scopes" に以下を追加：

| スコープ | 用途 |
|----------|------|
| `chat:write` | メッセージ送信 |
| `channels:history` | チャンネルのメッセージ取得 |
| `channels:read` | チャンネル一覧取得 |
| `groups:history` | プライベートチャンネルのメッセージ取得 |

### 3. アプリをインストール

"Install App" → "Install to Workspace" → トークンをコピー

### 4. ボットをチャンネルに招待

Slackで `/invite @claude-mcp-bot` を実行

---

## 実装する3つのツール

### ツール1：`send_message`

```
説明：Slackチャンネルにメッセージを送信する
パラメータ：
  - channel (string, 必須): "#general" 形式のチャンネル名
  - message (string, 必須): 送信するテキスト
  - thread_ts (string, 任意): スレッドに返信する場合のタイムスタンプ
戻り値：送信成功時のタイムスタンプ
```

### ツール2：`get_messages`

```
説明：チャンネルの最新メッセージを取得する
パラメータ：
  - channel (string, 必須): "#general" 形式のチャンネル名
  - limit (integer, 任意, デフォルト10): 取得件数（1〜100）
戻り値：メッセージのリスト（投稿者・本文・タイムスタンプ）
```

### ツール3：`list_channels`

```
説明：参加しているパブリックチャンネルの一覧を取得する
パラメータ：なし
戻り値：チャンネル名とIDのリスト
```

---

## 実装ガイド

### slack_integration.py の骨格

```python
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dataclasses import dataclass

@dataclass
class SlackMessage:
    user: str
    text: str
    timestamp: str

class SlackClient:
    def __init__(self):
        token = os.environ.get("SLACK_BOT_TOKEN")
        if not token:
            raise RuntimeError("SLACK_BOT_TOKEN が設定されていません")
        self._client = WebClient(token=token)

    def send_message(self, channel: str, message: str, thread_ts: str | None = None) -> str:
        """メッセージを送信してタイムスタンプを返す"""
        try:
            kwargs = {"channel": channel, "text": message}
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            response = self._client.chat_postMessage(**kwargs)
            return response["ts"]
        except SlackApiError as e:
            raise SlackError(f"送信失敗: {e.response['error']}") from e

    def get_messages(self, channel: str, limit: int = 10) -> list[SlackMessage]:
        """チャンネルのメッセージ一覧を取得する"""
        # ここを実装してください
        pass

    def list_channels(self) -> list[dict]:
        """チャンネル一覧を取得する"""
        # ここを実装してください
        pass

class SlackError(Exception):
    pass
```

### handler.py の骨格

```python
from mcp import types
from slack_integration import SlackClient, SlackError

_slack: SlackClient | None = None

def get_slack() -> SlackClient:
    global _slack
    if _slack is None:
        _slack = SlackClient()
    return _slack

async def handle_send_message(channel: str, message: str, thread_ts: str | None = None):
    try:
        ts = get_slack().send_message(channel, message, thread_ts)
        return [types.TextContent(type="text", text=f"送信完了 (ts: {ts})")]
    except SlackError as e:
        return [types.TextContent(type="text", text=f"エラー: {e}")]

# get_messages と list_channels も実装してください
```

---

## エラーハンドリングの要件

以下のSlackエラーに対応してください：

| Slackエラーコード | 意味 | 対応 |
|-------------------|------|------|
| `not_authed` | トークン未設定 | 分かりやすいメッセージを返す |
| `channel_not_found` | チャンネルが存在しない | チャンネル名を確認するよう促す |
| `not_in_channel` | ボットがチャンネルに未参加 | `/invite` を促すメッセージを返す |
| `ratelimited` | レート制限 | `Retry-After` ヘッダの秒数待ってリトライ |

---

## テストの書き方

### モックを使ったユニットテスト（tests/test_handler.py）

```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_slack(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("handler._slack", mock)
    return mock

@pytest.mark.asyncio
async def test_send_message_success(mock_slack):
    mock_slack.send_message.return_value = "1234567890.123456"
    
    from handler import handle_send_message
    result = await handle_send_message("#general", "テストメッセージ")
    
    assert "1234567890.123456" in result[0].text
    mock_slack.send_message.assert_called_once_with("#general", "テストメッセージ", None)

@pytest.mark.asyncio
async def test_send_message_channel_not_found(mock_slack):
    from slack_integration import SlackError
    mock_slack.send_message.side_effect = SlackError("channel_not_found")
    
    from handler import handle_send_message
    result = await handle_send_message("#nonexistent", "test")
    
    assert "エラー" in result[0].text
```

### 統合テスト（tests/test_integration.py）

```python
# 実際のSlack APIを呼び出すテスト（CI環境では SKIP）
import pytest
import os

pytestmark = pytest.mark.skipif(
    not os.environ.get("SLACK_BOT_TOKEN"),
    reason="SLACK_BOT_TOKEN が未設定"
)

@pytest.mark.asyncio
async def test_real_send_message():
    from handler import handle_send_message
    result = await handle_send_message("#test-channel", "MCPハンズオンテスト")
    assert "送信完了" in result[0].text
```

---

## 動作確認手順

```bash
# 1. 依存パッケージをインストール
pip install -r requirements.txt

# 2. 環境変数を設定
cp .env.example .env
# .env を編集して SLACK_BOT_TOKEN を設定

# 3. テストを実行（モックのみ）
pytest tests/test_handler.py -v

# 4. サーバを起動してMCP Inspectorで確認
npx @modelcontextprotocol/inspector python server.py

# 5. Claudeに話しかけてテスト
# 「#generalに『ハンズオン課題2が完了しました！』と送って」
```

---

## チェックポイント

- [ ] `.env` に `SLACK_BOT_TOKEN` を設定した
- [ ] ボットを対象チャンネルに招待した
- [ ] `send_message` でメッセージが送れる
- [ ] `get_messages` でメッセージ一覧が取れる
- [ ] `list_channels` でチャンネル一覧が取れる
- [ ] モックテストが全パスする
- [ ] `channel_not_found` エラーを適切にハンドリングできる

---

## 解答例

`exercises/solutions/solution-02/` を参照してください。

---

## 発展課題

- メッセージにリアクション（絵文字）を付ける `add_reaction` ツールを追加する
- ファイルをアップロードする `upload_file` ツールを追加する
- スレッドの返信を取得する機能を追加する
