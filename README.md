# MCP Server 自作ハンズオン — 利用ガイド

Slack / Notion / GitHub を Claude に自動連携させる MCP サーバを 0 から作る実践教材です。

## クイックスタート

```bash
# リポジトリをクローンしてこのディレクトリに移動
cd mcp-handson

# Pythonバージョン確認（3.11以上が必要）
python --version

# スターターコードで始める
cd boilerplate/mcp-starter
pip install -r requirements.txt
python server.py
```

## ディレクトリ構成

```
mcp-handson/
├── tutorial.md                    # メイン教材（全5章 + ベストプラクティス）
├── README.md                      # このファイル
├── testing-guide.md               # テスト・検証の詳細ガイド
│
├── exercises/                     # 演習課題
│   ├── exercise-01-basics.md      # 課題1：基本MCP実装（初級）
│   ├── exercise-02-slackbot.md    # 課題2：Slack連携（中級）
│   ├── exercise-03-multiservice.md # 課題3：複数サービス統合（上級）
│   └── solutions/                 # 解答コード
│       ├── solution-01/           # 課題1解答（計算ツール）
│       ├── solution-02/           # 課題2解答（Slack統合）
│       └── solution-03/           # 課題3解答（マルチサービス）
│
├── boilerplate/                   # テンプレートコード
│   ├── mcp-starter/               # Pythonスターター
│   └── client-example/            # TypeScriptクライアント例
│
├── reference/                     # リファレンス資料
│   ├── mcp-spec-summary.md        # MCPプロトコル仕様要約
│   ├── api-reference.md           # Slack/Notion/GitHub API早見表
│   ├── debugging-tips.md          # トラブルシューティング
│   └── deployment-checklist.md   # デプロイチェックリスト
│
└── integration-examples/          # 実装例（すぐ動くコード）
    ├── slack-mcp/                 # Slack連携の完全実装
    ├── notion-mcp/                # Notion連携の完全実装
    └── github-mcp/                # GitHub連携の完全実装
```

## 学習パス

### 初級（Python入門者）
1. `tutorial.md` の第0〜2章を読む
2. `boilerplate/mcp-starter/` のコードを動かす
3. `exercises/exercise-01-basics.md` に取り組む
4. `exercises/solutions/solution-01/` で答え合わせ

### 中級（API連携経験あり）
1. `tutorial.md` を通読（全章）
2. `exercises/exercise-02-slackbot.md` から始める
3. `integration-examples/slack-mcp/` を参考にする
4. 課題3まで全て完走する

### 上級（本番運用を目指す）
1. `exercises/exercise-03-multiservice.md` に直接取り組む
2. `reference/deployment-checklist.md` でデプロイを完成させる
3. TypeScript クライアントも実装する（`boilerplate/client-example/`）

## 環境変数の準備

`.env` ファイルをプロジェクトルートに作成：

```bash
# Slack（課題2・3で使用）
SLACK_BOT_TOKEN=xoxb-your-token-here

# Notion（課題3で使用）
NOTION_TOKEN=secret_your-token-here

# GitHub（課題3で使用）
GITHUB_TOKEN=ghp_your-token-here

# Anthropic（TypeScriptクライアントで使用）
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## トラブルシューティング

詳細は `reference/debugging-tips.md` を参照してください。

よくある問題：
- **ImportError: mcp not found** → `pip install mcp` を実行
- **Slack API error: not_authed** → `SLACK_BOT_TOKEN` が正しく設定されているか確認
- **Permission denied** → ボットをSlackチャンネルに招待（`/invite @botname`）
- **Claude Desktopに接続できない** → `claude_desktop_config.json` の絶対パスを確認

## 前提知識

| 知識 | 必要度 |
|------|--------|
| Python基礎（関数・クラス）| 必須 |
| 非同期処理（async/await）| あると良い |
| REST API の基礎 | 課題2から必須 |
| TypeScript | 第4章のみ |
| Docker | 第5章のみ |
