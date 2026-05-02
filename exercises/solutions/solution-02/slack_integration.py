import os
import time
from dataclasses import dataclass
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


@dataclass
class SlackMessage:
    user: str
    text: str
    timestamp: str


class SlackError(Exception):
    pass


class SlackClient:
    def __init__(self):
        token = os.environ.get("SLACK_BOT_TOKEN")
        if not token:
            raise RuntimeError("SLACK_BOT_TOKEN が設定されていません")
        self._client = WebClient(token=token)

    def send_message(self, channel: str, message: str, thread_ts: str | None = None) -> str:
        try:
            kwargs: dict = {"channel": channel, "text": message}
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            response = self._client.chat_postMessage(**kwargs)
            return response["ts"]
        except SlackApiError as e:
            error_code = e.response["error"]
            if error_code == "not_authed":
                raise SlackError("認証失敗: SLACK_BOT_TOKEN を確認してください") from e
            if error_code == "channel_not_found":
                raise SlackError(f"チャンネルが見つかりません: {channel}") from e
            if error_code == "not_in_channel":
                raise SlackError(f"ボットが {channel} に未参加です。/invite @ボット名 を実行してください") from e
            if error_code == "ratelimited":
                retry_after = int(e.response.headers.get("Retry-After", 60))
                time.sleep(retry_after)
                return self.send_message(channel, message, thread_ts)
            raise SlackError(f"送信失敗: {error_code}") from e

    def get_messages(self, channel: str, limit: int = 10) -> list[SlackMessage]:
        try:
            response = self._client.conversations_history(channel=channel, limit=limit)
            messages = []
            for msg in response["messages"]:
                messages.append(SlackMessage(
                    user=msg.get("user", "unknown"),
                    text=msg.get("text", ""),
                    timestamp=msg.get("ts", "")
                ))
            return messages
        except SlackApiError as e:
            error_code = e.response["error"]
            if error_code == "channel_not_found":
                raise SlackError(f"チャンネルが見つかりません: {channel}") from e
            if error_code == "not_in_channel":
                raise SlackError(f"ボットが {channel} に未参加です") from e
            raise SlackError(f"メッセージ取得失敗: {error_code}") from e

    def list_channels(self) -> list[dict]:
        try:
            response = self._client.conversations_list(types="public_channel", limit=200)
            return [
                {"id": ch["id"], "name": ch["name"]}
                for ch in response["channels"]
            ]
        except SlackApiError as e:
            raise SlackError(f"チャンネル一覧取得失敗: {e.response['error']}") from e
