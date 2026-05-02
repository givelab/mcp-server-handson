# 課題3：複数サービス対応MCPサーバ

**難度**：上級 | **実装時間**：2〜2.5時間 | **ファイル数**：15〜20

---

## 目標

Slack + Notion + GitHub を単一のMCPサーバに統合し、サービス障害に強いアーキテクチャを実装する。

---

## 課題背景

本番環境では1つのMCPサーバが複数のサービスを管理します。この課題では：

- **モジュール分割**：各サービスを独立したクラスとして実装
- **共通エラーハンドリング**：サービス横断の一貫したエラー処理
- **フォールバック設計**：1サービスが落ちても全体は動き続ける
- **構造化ログ**：本番運用に耐える監視可能な実装

---

## 作成するファイル

```
solution-03/
├── multi_service_server.py        # MCPサーバエントリポイント
├── services/
│   ├── __init__.py
│   ├── base_service.py            # 基底クラス・共通エラー
│   ├── slack_service.py           # Slackサービス
│   ├── notion_service.py          # Notionサービス
│   └── github_service.py          # GitHubサービス
├── utils/
│   ├── __init__.py
│   ├── logger.py                  # 構造化ログ
│   └── retry.py                   # リトライデコレータ
├── requirements.txt
├── .env.example
└── tests/
    ├── conftest.py
    ├── test_slack_service.py
    ├── test_notion_service.py
    ├── test_github_service.py
    └── test_multi_service.py       # 統合テスト
```

---

## 各サービスの実装要件

### Slack（課題2の拡張）

ツール一覧：
- `slack_send_message(channel, message)` — メッセージ送信
- `slack_get_messages(channel, limit)` — メッセージ取得
- `slack_list_channels()` — チャンネル一覧

### Notion

ツール一覧：
- `notion_create_page(title, content, parent_id)` — ページ作成
- `notion_get_page(page_id)` — ページ取得
- `notion_search(query)` — ページ検索

**Notion Token の取得方法**：
1. https://www.notion.so/my-integrations → "New integration"
2. "Read content" + "Insert content" + "Update content" を有効化
3. 対象データベースのページを開き "..." → "Add connections" でインテグレーションを追加
4. トークンをコピー（`secret_...` で始まる）

### GitHub

ツール一覧：
- `github_list_issues(owner, repo, state)` — Issue一覧
- `github_create_issue(owner, repo, title, body)` — Issue作成
- `github_get_pr(owner, repo, pr_number)` — PR取得

**GitHub Token の取得方法**：
1. GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Repository permissions: Issues (Read/Write), Pull requests (Read)
3. トークンをコピー（`github_pat_...` で始まる）

---

## アーキテクチャ設計

### 基底クラスの設計

```python
# services/base_service.py
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class ServiceError(Exception):
    """すべてのサービスエラーの基底クラス"""
    def __init__(self, service: str, message: str, code: str | None = None):
        self.service = service
        self.code = code
        super().__init__(f"[{service}] {message}")

class BaseService(ABC):
    """すべてのサービスの基底クラス"""
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        """サービス名（ログ・エラーメッセージで使用）"""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """サービスが利用可能か確認する"""
        ...

    def _raise(self, message: str, code: str | None = None) -> None:
        raise ServiceError(self.service_name, message, code)

    async def safe_execute(self, coro, fallback_message: str):
        """例外をキャッチしてフォールバックメッセージを返す"""
        try:
            return await coro
        except ServiceError:
            raise
        except Exception as e:
            logger.exception(f"{self.service_name} で予期しないエラー")
            self._raise(fallback_message)
```

### サービスレジストリ

```python
# multi_service_server.py 内

class ServiceRegistry:
    def __init__(self):
        self._services: dict[str, BaseService] = {}
    
    def register(self, service: BaseService):
        self._services[service.service_name] = service
    
    async def get_available_tools(self) -> list[types.Tool]:
        """利用可能なサービスのツールだけを返す"""
        tools = []
        for service in self._services.values():
            try:
                if await service.health_check():
                    tools.extend(service.get_tools())
                else:
                    logger.warning(f"{service.service_name} は利用不可 - ツールをスキップ")
            except Exception:
                logger.exception(f"{service.service_name} のヘルスチェック失敗")
        return tools
```

---

## フォールバック設計

各サービスの `health_check()` が失敗した場合、そのサービスのツールはリストから除外されます。

```python
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return await registry.get_available_tools()

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    service_prefix = name.split("_")[0]  # "slack_send_message" → "slack"
    service = registry.get(service_prefix)
    
    if service is None:
        raise ValueError(f"サービス '{service_prefix}' は登録されていません")
    
    try:
        return await service.dispatch(name, arguments)
    except ServiceError as e:
        # サービスエラーはisError: Trueで返す（サーバは落とさない）
        return [types.TextContent(
            type="text",
            text=f"サービスエラー ({e.service}): {e}"
        )]
```

---

## 構造化ログの実装

```python
# utils/logger.py
import logging
import json
import sys
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", "mcp-server"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logger(name: str = "mcp") -> logging.Logger:
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stderr)  # stdoutはMCP通信で使うのでstderrに
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
```

---

## Notion サービスの実装ガイド

```python
# services/notion_service.py
import os
import httpx
from .base_service import BaseService, ServiceError
from mcp import types

NOTION_API_BASE = "https://api.notion.com/v1"

class NotionService(BaseService):
    service_name = "notion"
    
    def __init__(self):
        token = os.environ.get("NOTION_TOKEN")
        if not token:
            raise RuntimeError("NOTION_TOKEN が設定されていません")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    async def health_check(self) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{NOTION_API_BASE}/users/me", headers=self._headers)
            return resp.status_code == 200
    
    async def create_page(self, title: str, content: str, parent_id: str) -> str:
        payload = {
            "parent": {"database_id": parent_id},
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": title}}]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    }
                }
            ]
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{NOTION_API_BASE}/pages",
                headers=self._headers,
                json=payload
            )
            if resp.status_code != 200:
                self._raise(f"ページ作成失敗: {resp.json().get('message')}")
            return resp.json()["id"]
    
    def get_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="notion_create_page",
                description="Notionデータベースに新しいページを作成する",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "ページタイトル"},
                        "content": {"type": "string", "description": "本文"},
                        "parent_id": {"type": "string", "description": "データベースID"}
                    },
                    "required": ["title", "content", "parent_id"]
                }
            )
            # 他のツールも追加してください
        ]
```

---

## GitHub サービスの実装ガイド

```python
# services/github_service.py
import os
import httpx
from .base_service import BaseService, ServiceError
from mcp import types

GITHUB_API_BASE = "https://api.github.com"

class GitHubService(BaseService):
    service_name = "github"
    
    def __init__(self):
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN が設定されていません")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    async def health_check(self) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{GITHUB_API_BASE}/user", headers=self._headers)
            return resp.status_code == 200
    
    async def list_issues(self, owner: str, repo: str, state: str = "open") -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                headers=self._headers,
                params={"state": state, "per_page": 20}
            )
            if resp.status_code == 404:
                self._raise(f"リポジトリ {owner}/{repo} が見つかりません", "repo_not_found")
            if resp.status_code != 200:
                self._raise(f"Issue取得失敗: {resp.status_code}")
            return resp.json()
    
    def get_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="github_list_issues",
                description="GitHubリポジトリのIssue一覧を取得する",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "リポジトリオーナー"},
                        "repo": {"type": "string", "description": "リポジトリ名"},
                        "state": {
                            "type": "string",
                            "enum": ["open", "closed", "all"],
                            "description": "Issueの状態",
                            "default": "open"
                        }
                    },
                    "required": ["owner", "repo"]
                }
            )
            # github_create_issue と github_get_pr も実装してください
        ]
```

---

## テスト戦略

### ユニットテスト（各サービス）

```python
# tests/test_github_service.py
import pytest
import respx
import httpx
from services.github_service import GitHubService

@pytest.fixture
def github_service(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake_token")
    return GitHubService()

@pytest.mark.asyncio
@respx.mock
async def test_list_issues_success(github_service):
    respx.get("https://api.github.com/repos/test/repo/issues").mock(
        return_value=httpx.Response(200, json=[
            {"number": 1, "title": "テストIssue", "state": "open"}
        ])
    )
    issues = await github_service.list_issues("test", "repo")
    assert len(issues) == 1
    assert issues[0]["title"] == "テストIssue"
```

### 統合テスト（サービス間の連携）

```python
# tests/test_multi_service.py
@pytest.mark.asyncio
async def test_github_to_notion_workflow():
    """GitHubのIssueをNotionに記録するワークフローのテスト"""
    # 1. GitHub から Issue を取得
    # 2. Notion にページを作成
    # 3. Slack に通知
    pass
```

---

## 動作確認シナリオ

Claudeに以下を依頼して動作確認してください：

1. **情報収集**：「claude-code リポジトリの open な Issue を5件教えて」
2. **クロスサービス連携**：「さっきのIssueをNotionに記録して、#devに要約を送って」
3. **エラー回復**：環境変数を一時削除してサーバを再起動し、そのサービスのツールがリストから消えることを確認

---

## チェックポイント

- [ ] 3サービスすべてのトークンを `.env` に設定した
- [ ] `health_check()` が各サービスで正しく動作する
- [ ] 1つのサービスが利用不可でも他のサービスは動く
- [ ] 構造化ログが stderr に出力される
- [ ] モックテストが全パスする
- [ ] Claudeを使ったクロスサービスワークフローが動作する

---

## 解答例

`exercises/solutions/solution-03/` を参照してください。
