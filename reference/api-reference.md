# 外部サービス API リファレンス

---

## Slack API

**ベースURL**: `https://slack.com/api`  
**認証**: `Authorization: Bearer xoxb-...`

### 主要エンドポイント

| メソッド | エンドポイント | 説明 |
|----------|---------------|------|
| POST | `/chat.postMessage` | メッセージ送信 |
| GET | `/conversations.history` | チャンネル履歴取得 |
| GET | `/conversations.list` | チャンネル一覧 |
| GET | `/auth.test` | トークン検証 |

### chat.postMessage
```
POST https://slack.com/api/chat.postMessage
Content-Type: application/json; charset=utf-8
Authorization: Bearer xoxb-...

{
  "channel": "#general",
  "text": "メッセージ本文",
  "thread_ts": "1234567890.000001"  // スレッド返信時のみ
}
```

**レスポンス（成功）**:
```json
{"ok": true, "ts": "1234567890.000002", "channel": "C01234567"}
```

### 必要なスコープ

| スコープ | 用途 |
|----------|------|
| `chat:write` | メッセージ送信 |
| `channels:history` | パブリックチャンネル履歴 |
| `channels:read` | パブリックチャンネル一覧 |
| `groups:history` | プライベートチャンネル履歴 |

### よくあるエラーコード

| エラー | 原因 | 対処 |
|--------|------|------|
| `not_authed` | トークン未設定 | SLACK_BOT_TOKEN を確認 |
| `channel_not_found` | チャンネルが存在しない | チャンネル名を確認 |
| `not_in_channel` | ボット未参加 | `/invite @bot-name` |
| `ratelimited` | レート制限 | Retry-After ヘッダの秒数待つ |

---

## Notion API

**ベースURL**: `https://api.notion.com/v1`  
**認証**: `Authorization: Bearer secret_...`  
**必須ヘッダ**: `Notion-Version: 2022-06-28`

### 主要エンドポイント

| メソッド | エンドポイント | 説明 |
|----------|---------------|------|
| POST | `/pages` | ページ作成 |
| GET | `/pages/{page_id}` | ページ取得 |
| PATCH | `/pages/{page_id}` | ページ更新 |
| POST | `/search` | 全文検索 |
| GET | `/databases/{database_id}/query` | データベースクエリ |

### pages（ページ作成）
```
POST https://api.notion.com/v1/pages
Authorization: Bearer secret_...
Notion-Version: 2022-06-28
Content-Type: application/json

{
  "parent": {"database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"},
  "properties": {
    "title": {
      "title": [{"type": "text", "text": {"content": "ページタイトル"}}]
    }
  },
  "children": [
    {
      "object": "block",
      "type": "paragraph",
      "paragraph": {
        "rich_text": [{"type": "text", "text": {"content": "本文"}}]
      }
    }
  ]
}
```

### Integration の作成手順

1. https://www.notion.so/my-integrations → "New integration"
2. 権限: "Read content", "Insert content", "Update content" を有効化
3. 対象データベースページの "..." → "Add connections" でインテグレーションを追加
4. トークンをコピー（`secret_` で始まる）

---

## GitHub API

**ベースURL**: `https://api.github.com`  
**認証**: `Authorization: Bearer github_pat_...`  
**必須ヘッダ**: `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`

### 主要エンドポイント

| メソッド | エンドポイント | 説明 |
|----------|---------------|------|
| GET | `/repos/{owner}/{repo}/issues` | Issue一覧 |
| POST | `/repos/{owner}/{repo}/issues` | Issue作成 |
| GET | `/repos/{owner}/{repo}/pulls/{pull_number}` | PR取得 |
| GET | `/user` | 認証ユーザー情報 |
| GET | `/repos/{owner}/{repo}` | リポジトリ情報 |

### Issue一覧取得
```
GET https://api.github.com/repos/{owner}/{repo}/issues?state=open&per_page=20
Authorization: Bearer github_pat_...
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

### Fine-grained Token の作成手順

1. GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. "Generate new token" → リポジトリを選択
3. Permissions:
   - Issues: Read and write
   - Pull requests: Read-only
   - Contents: Read-only（必要な場合）
4. トークンをコピー（`github_pat_` で始まる）

### HTTPステータスコード

| コード | 意味 |
|--------|------|
| 200 | 成功 |
| 201 | 作成成功 |
| 404 | リソースが見つからない |
| 422 | バリデーションエラー |
| 403 | 権限不足 |
| 429 | レート制限 |

---

## レート制限まとめ

| サービス | 制限 | リセット |
|----------|------|---------|
| Slack | 1メッセージ/秒/チャンネル | Retry-After ヘッダ |
| Notion | 3リクエスト/秒 | Retry-After ヘッダ |
| GitHub | 5,000リクエスト/時（認証済み） | X-RateLimit-Reset ヘッダ |
