# デプロイメントチェックリスト

---

## ローカル開発（Claude Desktop）

- [ ] `python server.py` を直接実行して `initialize` に応答するか確認
- [ ] MCP Inspector で全ツールの動作確認
- [ ] `.env` ファイルに全トークンを設定
- [ ] `.gitignore` に `.env` を追加
- [ ] `claude_desktop_config.json` に絶対パスで登録
- [ ] Claude Desktop を再起動してサーバが認識されるか確認

```json
// ~/.claude/claude_desktop_config.json (macOS)
{
  "mcpServers": {
    "my-server": {
      "command": "/usr/bin/python3",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-..."
      }
    }
  }
}
```

---

## Docker 化

- [ ] `Dockerfile` を作成
- [ ] `.dockerignore` に `.env`, `__pycache__`, `.venv` を追加
- [ ] `docker build -t my-mcp-server .` でビルド成功を確認
- [ ] `docker run -i --env-file .env my-mcp-server` で起動確認
- [ ] 環境変数をビルド時に埋め込んでいないことを確認（`docker history` で確認）

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "server.py"]
```

---

## 本番環境（Linux サーバ）

### systemd サービス登録

- [ ] `/opt/mcp-server/` にファイルを配置
- [ ] 専用ユーザーを作成（`sudo useradd -r mcp`）
- [ ] `/opt/mcp-server/.env` のパーミッションを `600` に設定
- [ ] `/etc/systemd/system/mcp-server.service` を作成
- [ ] `systemctl enable mcp-server` で自動起動を有効化
- [ ] `systemctl start mcp-server` で起動
- [ ] `journalctl -u mcp-server -f` でログを確認

```ini
[Unit]
Description=MCP Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/mcp-server
EnvironmentFile=/opt/mcp-server/.env
ExecStart=/opt/mcp-server/.venv/bin/python server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## セキュリティチェック

- [ ] `.env` を Git にコミットしていない
- [ ] トークンのスコープを最小限に絞っている
- [ ] 入力バリデーションを実装している
- [ ] ログに機密情報（トークン全体）を出力していない
- [ ] 依存パッケージに既知の脆弱性がないか確認（`pip audit`）

---

## 動作確認チェック

- [ ] 全ツールが `tools/list` で返ってくる
- [ ] 各ツールが期待通りの結果を返す
- [ ] エラー時に `isError: true` を返し、サーバがクラッシュしない
- [ ] Claudeとの実際の会話で意図通りに動作する
- [ ] 長時間稼働しても安定している（メモリリークなし）
