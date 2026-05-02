import os
from dataclasses import dataclass
from mcp import types
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from .base_service import BaseService, ServiceError


@dataclass
class SlackMessage:
    user: str
    text: str
    timestamp: str


class SlackService(BaseService):
    service_name = "slack"

    def __init__(self):
        token = os.environ.get("SLACK_BOT_TOKEN")
        if not token:
            raise RuntimeError("SLACK_BOT_TOKEN が設定されていません")
        self._client = WebClient(token=token)

    async def health_check(self) -> bool:
        try:
            response = self._client.auth_test()
            return response["ok"]
        except Exception:
            return False

    def send_message(self, channel: str, message: str, thread_ts: str | None = None) -> str:
        try:
            kwargs: dict = {"channel": channel, "text": message}
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            response = self._client.chat_postMessage(**kwargs)
            return response["ts"]
        except SlackApiError as e:
            self._raise(f"送信失敗: {e.response['error']}", e.response["error"])

    def get_messages(self, channel: str, limit: int = 10) -> list[SlackMessage]:
        try:
            response = self._client.conversations_history(channel=channel, limit=limit)
            return [
                SlackMessage(
                    user=m.get("user", "unknown"),
                    text=m.get("text", ""),
                    timestamp=m.get("ts", "")
                )
                for m in response["messages"]
            ]
        except SlackApiError as e:
            self._raise(f"メッセージ取得失敗: {e.response['error']}", e.response["error"])

    def list_channels(self) -> list[dict]:
        try:
            response = self._client.conversations_list(types="public_channel", limit=200)
            return [{"id": ch["id"], "name": ch["name"]} for ch in response["channels"]]
        except SlackApiError as e:
            self._raise(f"チャンネル一覧取得失敗: {e.response['error']}", e.response["error"])

    def get_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="slack_send_message",
                description="Slackチャンネルにメッセージを送信する",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string", "description": "#general 形式のチャンネル名"},
                        "message": {"type": "string", "description": "送信するテキスト"},
                        "thread_ts": {"type": "string", "description": "スレッドへの返信用タイムスタンプ（任意）"}
                    },
                    "required": ["channel", "message"]
                }
            ),
            types.Tool(
                name="slack_get_messages",
                description="チャンネルの最新メッセージを取得する",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string", "description": "#general 形式のチャンネル名"},
                        "limit": {"type": "integer", "description": "取得件数（デフォルト10）", "default": 10}
                    },
                    "required": ["channel"]
                }
            ),
            types.Tool(
                name="slack_list_channels",
                description="参加しているパブリックチャンネルの一覧を取得する",
                inputSchema={"type": "object", "properties": {}}
            )
        ]

    async def dispatch(self, name: str, arguments: dict) -> list[types.TextContent]:
        if name == "slack_send_message":
            ts = self.send_message(
                arguments["channel"],
                arguments["message"],
                arguments.get("thread_ts")
            )
            return [types.TextContent(type="text", text=f"送信完了 (ts: {ts})")]
        if name == "slack_get_messages":
            messages = self.get_messages(arguments["channel"], arguments.get("limit", 10))
            if not messages:
                return [types.TextContent(type="text", text="メッセージがありません")]
            lines = [f"[{m.timestamp}] {m.user}: {m.text}" for m in messages]
            return [types.TextContent(type="text", text="\n".join(lines))]
        if name == "slack_list_channels":
            channels = self.list_channels()
            lines = [f"#{ch['name']} (ID: {ch['id']})" for ch in channels]
            return [types.TextContent(type="text", text="\n".join(lines))]
        raise ValueError(f"Unknown Slack tool: {name}")
